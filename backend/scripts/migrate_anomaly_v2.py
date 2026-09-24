"""
异常检测阶段迁移脚本 v2
  - 新建 stage_configs 表（阶段时间配置）
  - anomaly_records 补 teacher_id / rectification_task_id 字段
  - 自动写入 9 个默认阶段配置（当前学年）
用法：  cd backend; python scripts/migrate_anomaly_v2.py
"""
import sys
from datetime import datetime, timedelta, date

# 确保能 import app
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from app.config import settings

eng = create_engine(settings.DATABASE_URL)
TODAY = date.today()

# -------- 1) stage_configs --------
CREATE_STAGE = text("""
CREATE TABLE IF NOT EXISTS stage_configs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  module_key VARCHAR(32) NOT NULL UNIQUE,
  module_name VARCHAR(50) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  student_lock_after_end INT DEFAULT 1,
  teacher_lock_after_end INT DEFAULT 0,
  description TEXT,
  create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
  update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  KEY idx_module_key (module_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='阶段时间配置';
""")

# 默认阶段：以当前日期为基准自动铺排
DEFAULTS = [
    ("topic", "选题申报", 0, 14),
    ("proposal", "开题报告", 15, 30),
    ("midterm", "中期检查", 40, 60),
    ("thesis_draft", "论文初稿", 50, 90),
    ("thesis_revision", "论文修改稿", 91, 120),
    ("thesis_final", "论文终稿", 121, 150),
    ("review", "评阅", 145, 165),
    ("defense", "答辩", 166, 180),
    ("archive", "成果归档", 175, 200),
]

INSERT_DEFAULT = text("""
INSERT IGNORE INTO stage_configs (module_key, module_name, start_time, end_time)
VALUES (:module_key, :module_name, :start_time, :end_time)
""")

# -------- 2) anomaly_records 补列 --------
ALTER_COLS = [
    ("teacher_id", "INT NULL COMMENT '指导教师ID'"),
    ("rectification_task_id", "INT NULL COMMENT '关联整改任务ID'"),
    ("algorithm_detail", "JSON NULL COMMENT '算法详细输出(JSON)'"),
]

with eng.begin() as tx:
    tx.execute(CREATE_STAGE)
    print("[OK] stage_configs 已创建/已存在")

    today = datetime.combine(TODAY, datetime.min.time())
    for key, name, start_off, end_off in DEFAULTS:
        tx.execute(INSERT_DEFAULT, {
            "module_key": key,
            "module_name": name,
            "start_time": today + timedelta(days=start_off),
            "end_time": today + timedelta(days=end_off),
        })
    print(f"[OK] 已写入/忽略 {len(DEFAULTS)} 条默认阶段配置")

    # anomaly_records 补列
    for col_name, col_def in ALTER_COLS:
        try:
            tx.execute(text(f"ALTER TABLE anomaly_records ADD COLUMN {col_name} {col_def}"))
            print(f"[OK] anomaly_records ADD {col_name}")
        except Exception as e:
            # MySQL 1060 = Duplicate column name
            if "1060" in str(e) or "Duplicate" in str(e):
                print(f"[SKIP] {col_name} 已存在")
            else:
                raise
    print("[DONE] 迁移完成")
