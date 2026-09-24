"""
过程指导记录迁移脚本
用法: cd backend; python scripts/migrate_guidance.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from app.config import settings

eng = create_engine(settings.DATABASE_URL)

CREATE = text("""
CREATE TABLE IF NOT EXISTS guidance_records (
  id INT AUTO_INCREMENT PRIMARY KEY,
  topic_id INT NOT NULL,
  student_id INT NOT NULL,
  teacher_id INT NOT NULL,
  initiator VARCHAR(20) DEFAULT 'teacher',
  guidance_type VARCHAR(20) DEFAULT 'meeting',
  guidance_time DATETIME NULL,
  title VARCHAR(200) DEFAULT '',
  content TEXT,
  student_response TEXT,
  reply_time DATETIME NULL,
  status VARCHAR(20) DEFAULT 'pending',
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_topic (topic_id),
  KEY idx_student (student_id),
  KEY idx_teacher (teacher_id),
  KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='过程指导记录';
""")

with eng.begin() as tx:
    tx.execute(CREATE)
    print("[OK] guidance_records 表已创建/已存在")
