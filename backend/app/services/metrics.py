"""BR-01 weighted progress — single server-side implementation reused by F03/F04/F05."""
from datetime import date


def plan_days(start: str, end: str) -> int:
    return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1


def weighted_progress(plans) -> int:
    """round(sum(rate*days)/sum(days)); 0 when no plans. `plans`: rows with PlanStartDt/PlanEndDt/ProgressRate."""
    total = sum(plan_days(p["PlanStartDt"], p["PlanEndDt"]) for p in plans)
    if not total:
        return 0
    s = sum(p["ProgressRate"] * plan_days(p["PlanStartDt"], p["PlanEndDt"]) for p in plans)
    return int(s / total + 0.5)  # JS Math.round semantics for non-negative values
