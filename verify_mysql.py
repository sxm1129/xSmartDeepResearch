from src.utils.session_manager import SessionManager
from src.utils.logger import logger

try:
    print("Initializing SessionManager...")
    sm = SessionManager()
    print("✅ SessionManager Initialized.")
    
    print("Creating test session...")
    sid = sm.create_session("Test Session", "test")
    print(f"✅ Session Created: {sid}")
    
    print("Listing sessions...")
    sessions = sm.list_sessions(limit=1)
    print(f"✅ Sessions List: {sessions}")
    
    if sessions:
        print("Cleaning up...")
        sm.delete_session(sid)
        print("✅ Cleanup done.")
        
except Exception as e:
    print(f"❌ Error: {e}")
