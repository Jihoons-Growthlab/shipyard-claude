from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    emp_no: str = Field(max_length=64)
    password: str = Field(max_length=256)


class OtpIn(BaseModel):
    code: str = Field(max_length=16)


class RegisterIn(BaseModel):
    last_name: str = Field(max_length=50)
    first_name: str = Field(max_length=50)
    birth_date: str = Field(max_length=10)
    phone: str = Field(max_length=20)
    email: str = Field(max_length=254)
    emp_no: str = Field(max_length=20)
    password: str = Field(max_length=256)
    password_confirm: str = Field(max_length=256)


class ApproveIn(BaseModel):
    groups: list[str]


class UserIn(BaseModel):  # F09 USR-02; rules enforced in user_service
    emp_no: str | None = Field(default=None, max_length=20)
    last_name: str | None = Field(default=None, max_length=50)
    first_name: str | None = Field(default=None, max_length=50)
    birth_date: str | None = Field(default=None, max_length=10)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=254)
    password: str | None = Field(default=None, max_length=256)
    status: str | None = Field(default=None, max_length=10)
    group: str | None = Field(default=None, max_length=20)
    totp_enabled: bool = False


class MenuAccessIn(BaseModel):
    menu_id: str = Field(max_length=10)


class _HullBase(BaseModel):
    hull_nm: str | None = Field(default=None, max_length=100)
    ship_type: str | None = Field(default=None, max_length=10)
    hull_status: str | None = Field(default=None, max_length=10)
    owner_nm: str | None = Field(default=None, max_length=100)
    class_society: str | None = Field(default=None, max_length=50)
    length_m: float | None = None
    breadth_m: float | None = None
    depth_m: float | None = None
    dead_weight: float | None = None
    dock_no: str | None = Field(default=None, max_length=50)
    contract_dt: str | None = Field(default=None, max_length=10)
    delivery_dt: str | None = Field(default=None, max_length=10)
    remark: str | None = Field(default=None, max_length=500)
    use_yn: bool | None = None


class HullCreate(_HullBase):
    hull_no: str | None = Field(default=None, max_length=20)


class HullUpdate(_HullBase):
    hull_no: str | None = Field(default=None, max_length=20)


class MilestoneIn(BaseModel):
    milestone_cd: str = Field(max_length=10)
    plan_dt: str | None = Field(default=None, max_length=10)
    actual_dt: str | None = Field(default=None, max_length=10)


class MilestonesIn(BaseModel):
    items: list[MilestoneIn] = Field(max_length=5)


class BlockIn(BaseModel):
    block_cd: str | None = Field(default=None, max_length=20)
    block_nm: str | None = Field(default=None, max_length=100)
    block_type: str | None = Field(default=None, max_length=10)
    weight_ton: float | None = None


class PlanIn(BaseModel):
    block_id: int | None = None
    proc_cd: str | None = Field(default=None, max_length=10)
    plan_start_dt: str | None = Field(default=None, max_length=10)
    plan_end_dt: str | None = Field(default=None, max_length=10)
    manager_emp_no: str | None = Field(default=None, max_length=20)
    remark: str | None = Field(default=None, max_length=1000)
    pred_plan_ids: list[int] | None = Field(default=None, max_length=500)
    confirm_late_preds: bool = False


class PredsIn(BaseModel):
    pred_plan_ids: list[int] = Field(max_length=500)
    confirm_late_preds: bool = False


class LinkIn(BaseModel):
    drawing_id: int
    required: bool = True


class ProgressIn(BaseModel):
    progress_rate: float | None = None
    man_hour: float | None = None
    worker_cnt: int | None = None
    worker_emp_no: str | None = Field(default=None, max_length=20)
    remark: str | None = Field(default=None, max_length=1000)


class DrawingIn(BaseModel):
    drawing_no: str | None = Field(default=None, max_length=50)
    drawing_nm: str | None = Field(default=None, max_length=200)
    hull_no: str | None = Field(default=None, max_length=20)
    block_id: int | None = None
    discipline: str | None = Field(default=None, max_length=10)
    designer_emp_no: str | None = Field(default=None, max_length=20)


class RevisionIn(BaseModel):
    change_desc: str | None = Field(default=None, max_length=1000)


class ApprovalRequestIn(BaseModel):
    reviewer_emp_no: str | None = Field(default=None, max_length=20)
    approver_emp_no: str | None = Field(default=None, max_length=20)


class ApprovalDecisionIn(BaseModel):  # F08 APV-02; result/comment rules enforced in approval_service
    result: str = Field(max_length=10)
    comment: str | None = Field(default=None, max_length=1000)


class DrawingLinkIn(BaseModel):
    plan_id: int
    required: bool = True
