"""
数据库模型包
"""
from app.models.user import User
from app.models.topic import Topic
from app.models.proposal import Proposal
from app.models.midterm import MidtermCheck, Rectification
from app.models.thesis import ThesisVersion, FormatCheck
from app.models.review import Review, Defense
from app.models.archive import Archive
from app.models.anomaly import AnomalyRecord, AnomalyReview
from app.models.log import OperationLog
from app.models.token_blacklist import RevokedToken
from app.models.file import UploadedFile

__all__ = [
    "User",
    "Topic",
    "Proposal",
    "MidtermCheck",
    "Rectification",
    "ThesisVersion",
    "FormatCheck",
    "Review",
    "Defense",
    "Archive",
    "AnomalyRecord",
    "AnomalyReview",
    "OperationLog",
    "RevokedToken",
    "UploadedFile",
]
