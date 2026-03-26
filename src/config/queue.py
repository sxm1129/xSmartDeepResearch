"""Redis and arq configuration for async task queue."""

import urllib.parse
from arq.connections import RedisSettings
from config.settings import Settings

settings = Settings()

# Parse redis_url from settings.redis_url (e.g., redis://localhost:6379/0)
# Default format is expected to be redis://[:password@]host[:port][/db]
try:
    url = urllib.parse.urlparse(settings.redis_url)
    redis_settings = RedisSettings(
        host=url.hostname or 'localhost',
        port=url.port or 6379,
        password=url.password,
        database=int(url.path.lstrip('/')) if url.path and url.path.lstrip('/') else 0,
    )
except Exception as e:
    # Fallback to local default if parsing fails
    redis_settings = RedisSettings(host='localhost', port=6379)


class WorkerSettings:
    """
    arq Worker Settings
    This class is configured for running the arq worker.
    Starts with: arq src.config.queue.WorkerSettings
    """
    from src.worker.tasks import run_research_task
    
    redis_settings = redis_settings
    functions = [run_research_task]
    
    @staticmethod
    async def on_startup(ctx):
        print("Worker starting up...")

    @staticmethod
    async def on_shutdown(ctx):
        print("Worker shutting down...")
