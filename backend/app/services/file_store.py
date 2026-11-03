"""D12: drawing PDFs on the server filesystem. FileId is a server-generated opaque id (no client paths).
Consistency (BR-08): new files are written before the DB commit and removed if it fails; replaced/deleted files are
removed only after the DB commit (best effort — a failed unlink leaves an unreferenced file, never a dangling row)."""
import logging
import os
import re
import uuid
from pathlib import Path

from ..config import settings
from ..errors import ApiError

log = logging.getLogger(__name__)
_ID = re.compile(r"^[0-9a-f]{32}$")


def _dir() -> Path:
    d = Path(settings.file_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def path_of(file_id: str) -> Path:
    if not file_id or not _ID.match(file_id):
        raise ApiError(404, "FILE_NOT_FOUND", "파일을 찾을 수 없습니다.")
    return _dir() / f"{file_id}.pdf"


def validate(filename: str | None, content_type: str | None, data: bytes) -> str:
    name = os.path.basename((filename or "").replace("\\", "/")).strip()[:200]
    if not name:
        raise ApiError(400, "VALIDATION_ERROR", "파일명을 확인하세요.", {"field": "pdf"})
    if not (name.lower().endswith(".pdf") or (content_type or "").split(";")[0].strip() == "application/pdf"):
        raise ApiError(400, "INVALID_FILE_TYPE", "PDF 파일만 업로드할 수 있습니다.", {"field": "pdf"})
    if len(data) > settings.max_pdf_bytes:
        raise ApiError(413, "FILE_TOO_LARGE", "파일 크기는 30MB 이하여야 합니다.", {"field": "pdf"})
    if not data.startswith(b"%PDF-"):  # DESIGN: magic header in addition to the mockup's ext/MIME check
        raise ApiError(400, "INVALID_FILE_TYPE", "PDF 파일만 업로드할 수 있습니다.", {"field": "pdf"})
    return name


def write(data: bytes) -> str:
    file_id = uuid.uuid4().hex
    dest = path_of(file_id)
    tmp = dest.with_suffix(".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, dest)
    return file_id


def remove(file_ids) -> None:
    for fid in file_ids:
        if not fid:
            continue
        try:
            path_of(fid).unlink(missing_ok=True)
        except (OSError, ApiError):
            log.warning("orphan drawing file left on disk: %s", fid)
