
import os
import pymysql
from dotenv import load_dotenv
import time

load_dotenv()

host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT", 3306))

print(f"Connecting to {host}:{port} user={user} db={db_name}...")

try:
    start = time.time()
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db_name,
        connect_timeout=10
    )
    print(f"Connected in {time.time() - start:.2f}s")
    
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM research_tasks")
    result = cursor.fetchone()
    print(f"Research Tasks Count: {result}")
    
    conn.close()
    print("Connection closed.")

except Exception as e:
    print(f"Connection failed: {e}")
