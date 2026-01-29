from src.utils.project_manager import ProjectManager
from src.utils.logger import logger

def migrate():
    print("🚀 Starting legacy migration...")
    pm = ProjectManager()
    
    # This function creates the Default project if not exists
    # and updates all sessions with NULL project_id
    default_id = pm.ensure_default_project()
    
    if default_id:
        print(f"✅ Migration successful. Default Project ID: {default_id}")
    else:
        print("❌ Migration failed.")

if __name__ == "__main__":
    migrate()
