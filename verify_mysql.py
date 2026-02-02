from src.utils.session_manager import SessionManager
from src.utils.logger import logger
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        print(f"Testing connection to {os.getenv('DB_HOST')}...")
        sm = SessionManager()
        print("✅ SessionManager Initialized (DB & Tables checked).")
        
        print("Creating test session...")
        sid = sm.create_session("Test Remote Session", "test")
        if sid:
            print(f"✅ Session Created: {sid}")
            
            print("Listing sessions...")
            sessions = sm.list_sessions(limit=5)
            print(f"✅ Recently created sessions: {[s['id'] for s in sessions]}")
            
            print("Cleaning up...")
            sm.delete_session(sid)
            print("✅ Cleanup done.")
            return True
        else:
            print("❌ Failed to create session.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
