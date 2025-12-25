#!/usr/bin/env python3
"""数据库迁移脚本 - 添加Step模型"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app, db
from app.models import Project, Step, User
def upgrade():
    """创建step表"""
    with db.engine.connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS step (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(255) NOT NULL,
                project_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (project_id) REFERENCES project (id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES user (id) ON DELETE SET NULL
            )
        """)
        conn.commit()
    print("✅ Step表创建成功")
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        upgrade()