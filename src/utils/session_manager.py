import pymysql
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

class SessionManager:
    """会话管理器 - 基于 MySQL 实现远程持久化"""
    
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "xsmartdeepresearch")
        
        self._init_db()
        
    def _get_connection(self, db_name: str = None):
        """获取数据库连接"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

    def _init_db(self):
        """初始化数据库表结构"""
        try:
            # 1. 连接 MySQL Server (不指定 DB) 检查数据库是否存在
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.commit()
            conn.close()
            
            # 2. 连接指定 DB 创建表
            conn = self._get_connection(self.db_name)
            cursor = conn.cursor()
            
            # 创建 Projects 表 (新)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    status ENUM('active', 'archived') DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # 创建 Sessions 表 (原有)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id VARCHAR(36) PRIMARY KEY,
                    title VARCHAR(255),
                    intent_category VARCHAR(50),
                    project_id VARCHAR(36),
                    tags JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 手动检查并添加列 (Migration for existing tables)
            try:
                cursor.execute("SELECT project_id FROM sessions LIMIT 1")
            except:
                logger.info("⚡ Migrating sessions table: Adding project_id and tags...")
                cursor.execute("ALTER TABLE sessions ADD COLUMN project_id VARCHAR(36)")
                cursor.execute("ALTER TABLE sessions ADD COLUMN tags JSON")
                cursor.execute("ALTER TABLE sessions ADD CONSTRAINT fk_project FOREIGN KEY (project_id) REFERENCES projects(id)")

            # 创建 Project Memories 表 (新)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS project_memories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    project_id VARCHAR(36),
                    key_fact TEXT,
                    source_session_id VARCHAR(36),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            # 创建 Messages 表 (原有)
            
            # 创建 Messages 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id VARCHAR(36),
                    role VARCHAR(50),
                    content LONGTEXT,
                    metadata JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
            
            conn.commit()
            conn.close()
            logger.info(f"✅ MySQL initialized: {self.db_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to init MySQL: {e}")

    def create_session(self, title: str, intent_category: str = "general", project_id: str = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        
        try:
            conn = self._get_connection(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO sessions (id, title, intent_category, project_id) VALUES (%s, %s, %s, %s)",
                (session_id, title, intent_category, project_id)
            )
            
            conn.commit()
            conn.close()
            return session_id
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    def add_message(self, session_id: str, role: str, content: str, metadata: Dict[str, Any] = None):
        """添加消息记录"""
        try:
            conn = self._get_connection(self.db_name)
            cursor = conn.cursor()
            
            meta_json = json.dumps(metadata, ensure_ascii=False) if metadata else "{}"
            
            # MySQL metadata 是 JSON 类型，直接传字符串或 json dump
            cursor.execute(
                "INSERT INTO messages (session_id, role, content, metadata) VALUES (%s, %s, %s, %s)",
                (session_id, role, content, meta_json)
            )
            
            # update_at 会通过 ON UPDATE 自动更新
             # Simple touch to ensure updated_at changes if wanted, but MySQL triggers usually handle it. 
             # For explicit update:
            cursor.execute("UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s", (session_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to add message to session {session_id}: {e}")

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出最近会话"""
        try:
            conn = self._get_connection(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT %s",
                (limit,)
            )
            
            rows = cursor.fetchall()  # DictCursor returns dicts
            conn.close()
            
            # datetime 转换 string
            for row in rows:
                if isinstance(row.get('updated_at'), datetime):
                    row['updated_at'] = row['updated_at'].isoformat()
                if isinstance(row.get('created_at'), datetime):
                    row['created_at'] = row['created_at'].isoformat()
                    
            return rows
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话完整历史"""
        try:
            conn = self._get_connection(self.db_name)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM messages WHERE session_id = %s ORDER BY id ASC",
                (session_id,)
            )
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                msg = dict(row)
                if msg.get('metadata'):
                    if isinstance(msg['metadata'], str):
                         try:
                             msg['metadata'] = json.loads(msg['metadata'])
                         except:
                             msg['metadata'] = {}
                history.append(msg)
            
            return history
        except Exception as e:
            logger.error(f"Failed to get history for session {session_id}: {e}")
            return []

    def delete_session(self, session_id: str):
        """删除会话"""
        try:
            conn = self._get_connection(self.db_name)
            cursor = conn.cursor()
            
            # Cascade delete should handle messages, but explicit is safe
            cursor.execute("DELETE FROM messages WHERE session_id = %s", (session_id,))
            cursor.execute("DELETE FROM sessions WHERE id = %s", (session_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
