"""
开题报告 API 路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.response import success_response, page_response
from app.core.security import get_current_user, require_teacher, require_student, require_student_or_teacher
from app.schemas.proposal import ProposalCreate, ProposalUpdate, ProposalReview, ProposalSubmit, ProposalResponse
from app.schemas.common import PaginationParams
from app.models.user import User
from app.services import proposal_service

router = APIRouter(prefix="/api/proposals", tags=["开题报告"])


@router.get("", summary="开题报告列表")
def list_proposals(
    params: PaginationParams = Depends(),
    status: str = Query(None, description="状态过滤"),
    student_id: int = Query(None, description="学生ID过滤"),
    teacher_id: int = Query(None, description="教师ID过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取开题报告列表，支持关键词搜索和分页"""
    # 数据隔离：学生只能看到自己的开题报告
    if current_user.role == "student":
        student_id = current_user.id
    elif current_user.role == "teacher":
        teacher_id = current_user.id

    items, total = proposal_service.get_proposal_list(db, params, status, student_id, teacher_id)
    return page_response(items=items, total=total, page=params.page, page_size=params.page_size)


@router.post("", summary="创建/更新开题报告")
def create_or_update_proposal(
    data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生创建或更新开题报告（草稿）"""
    result = proposal_service.create_or_update_proposal(db, data, current_user.id)
    return success_response(data=result, message="开题报告保存成功")


@router.get("/{proposal_id}", summary="开题报告详情")
def get_proposal(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """获取开题报告详情"""
    result = proposal_service.get_proposal_detail(db, proposal_id)
    return success_response(data=result)


@router.put("/{proposal_id}", summary="更新开题报告")
def update_proposal(
    proposal_id: int,
    data: ProposalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student_or_teacher),
):
    """更新开题报告信息"""
    result = proposal_service.update_proposal(db, proposal_id, data, current_user)
    return success_response(data=result, message="开题报告更新成功")


@router.post("/{proposal_id}/submit", summary="提交开题报告")
def submit_proposal(
    proposal_id: int,
    data: ProposalSubmit = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_student),
):
    """学生提交开题报告待审核"""
    result = proposal_service.submit_proposal(db, proposal_id, current_user.id)
    return success_response(data=result, message="开题报告提交成功")


@router.post("/{proposal_id}/review", summary="审核开题报告")
def review_proposal(
    proposal_id: int,
    data: ProposalReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_teacher),
):
    """教师/管理员审核开题报告"""
    result = proposal_service.review_proposal(db, proposal_id, data, current_user.id)
    return success_response(data=result, message="审核完成")
