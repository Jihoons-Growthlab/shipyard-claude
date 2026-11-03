// Client-side mirror of the server PDF check (UX only; the server re-validates ext/MIME, size and %PDF- header).
export const MAX_PDF = 30 * 1024 * 1024
export function pdfError(file) {
  if (!/\.pdf$/i.test(file.name) && file.type !== 'application/pdf') return 'PDF 파일만 업로드할 수 있습니다.'
  return file.size > MAX_PDF ? '파일 크기는 30MB 이하여야 합니다.' : ''
}
