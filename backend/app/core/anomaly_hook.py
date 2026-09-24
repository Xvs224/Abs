"""异常检测实时触发钩子。

业务 submit 成功后调用：
    from app.core.anomaly_hook import trigger_after_submit
    trigger_after_submit(db, student_id)   # 内部会 try/except 吞掉异常，不影响主流程
"""
import logging
import threading
from datetime import datetime

logger = logging.getLogger(__name__)


def trigger_after_submit(db, student_id: int):
    """业务提交成功后异步触发异常检测（规则类 + IQR/IF）。

    设计要点：
      - 独立线程运行，不阻塞主请求
      - 内部 try/except，异常仅打日志不冒泡
    """
    def _worker():
        try:
            from app.database import SessionLocal
            from app.services.anomaly_service import AnomalyService

            local_db = SessionLocal()
            try:
                svc = AnomalyService(local_db)
                svc.trigger_for_student(student_id)
            finally:
                local_db.close()
            logger.info(f"[anomaly-hook] trigger_for_student student_id={student_id} done @ {datetime.now()}")
        except Exception as e:
            logger.warning(f"[anomaly-hook] trigger_for_student student_id={student_id} failed: {e}")

    threading.Thread(target=_worker, daemon=True).start()
