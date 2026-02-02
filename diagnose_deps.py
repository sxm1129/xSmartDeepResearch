import os
import pymysql
import redis
from dotenv import load_dotenv

load_dotenv()

def check_mysql():
    print("Checking MySQL...")
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    db_name = os.getenv("DB_NAME", "xsmartdeepresearch")
    
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=db_name,
            connect_timeout=5
        )
        print(f"✅ MySQL connected to {host}")
        conn.close()
    except Exception as e:
        print(f"❌ MySQL connection failed to {host}: {e}")

def check_redis():
    print("Checking Redis...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        r = redis.from_url(redis_url, socket_connect_timeout=5)
        r.ping()
        print(f"✅ Redis connected to {redis_url}")
    except Exception as e:
        print(f"❌ Redis connection failed to {redis_url}: {e}")

if __name__ == "__main__":
    check_mysql()
    check_redis()
