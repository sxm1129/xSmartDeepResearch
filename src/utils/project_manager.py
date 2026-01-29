from typing import List, Dict, Any, Optional
import pymysql
import uuid
import os
import json
from datetime import datetime
from src.utils.logger import logger
from src.utils.session_manager import SessionManager

class ProjectManager:
    """项目与知识库管理器"""
    
    def __init__(self):
        # 复用 SessionManager 的连接配置
        self.sm = SessionManager()
        self.host = self.sm.host
        self.port = self.sm.port
        self.user = self.sm.user
        self.password = self.sm.password
        self.db_name = self.sm.db_name
        
    def _get_connection(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.db_name,
            cursorclass=pymysql.cursors.DictCursor
        )

    def create_project(self, name: str, description: str = "") -> str:
        """创建新的研究项目"""
        project_id = str(uuid.uuid4())
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO projects (id, name, description) VALUES (%s, %s, %s)",
                (project_id, name, description)
            )
            
            conn.commit()
            conn.close()
            return project_id
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return None

    def list_projects(self, status: str = "active") -> List[Dict[str, Any]]:
        """列出所有项目"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM projects WHERE status = %s ORDER BY updated_at DESC", 
                (status,)
            )
            rows = cursor.fetchall()
            conn.close()
            
            # Format datetime
            for row in rows:
                if isinstance(row.get('updated_at'), datetime):
                    row['updated_at'] = row['updated_at'].isoformat()
                if isinstance(row.get('created_at'), datetime):
                    row['created_at'] = row['created_at'].isoformat()
                    
            return rows
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return []

    def get_project_sessions(self, project_id: str) -> List[Dict[str, Any]]:
        """获取项目下的所有会话"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM sessions WHERE project_id = %s ORDER BY updated_at DESC",
                (project_id,)
            )
            rows = cursor.fetchall()
            conn.close()
            
            # Format datetime
            for row in rows:
                if isinstance(row.get('updated_at'), datetime):
                    row['updated_at'] = row['updated_at'].isoformat()
                if isinstance(row.get('created_at'), datetime):
                    row['created_at'] = row['created_at'].isoformat()
                    
            return rows
        except Exception as e:
            logger.error(f"Failed to get project sessions: {e}")
            return []

    def add_project_memory(self, project_id: str, key_fact: str, source_session_id: str = None):
        """向项目注入新的知识上下文"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO project_memories (project_id, key_fact, source_session_id) VALUES (%s, %s, %s)",
                (project_id, key_fact, source_session_id)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")

    def get_project_context(self, project_id: str, limit: int = 5) -> str:
        """获取项目相关的上下文知识 (构建 Prompt 用)"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 获取最近的 N 条核心事实
            cursor.execute(
                "SELECT key_fact FROM project_memories WHERE project_id = %s ORDER BY created_at DESC LIMIT %s",
                (project_id, limit)
            )
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return ""
            
            context = "### Project Context (Shared Knowledge):\n"
            for row in rows:
                context += f"- {row['key_fact']}\n"
            return context
            
        except Exception as e:
            logger.error(f"Failed to get context: {e}")
            return ""

    def ensure_default_project(self) -> str:
        """确保存在默认项目，用于存放旧会话"""
        default_id = "default-0000-0000-0000-000000000000"
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT id FROM projects WHERE id = %s", (default_id,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO projects (id, name, description) VALUES (%s, %s, %s)",
                    (default_id, "Default Project", "Auto-created for legacy sessions")
                )
                conn.commit()
                # 迁移旧数据: 将所有没有 project_id 的 session 归入 default
                cursor.execute(
                    "UPDATE sessions SET project_id = %s WHERE project_id IS NULL",
                    (default_id,)
                )
                conn.commit()
                logger.info("✅ Migrated legacy sessions to Default Project")
            
            conn.close()
            return default_id
        except Exception as e:
            logger.error(f"Default project check failed: {e}")
            return None
