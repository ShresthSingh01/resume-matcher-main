import redis
import json
from loguru import logger
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.client = None
        try:
            # decode_responses=True ensures we get strings back, not bytes
            self.client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            # Test connection
            self.client.ping()
            logger.info("✅ Redis Connected")
        except Exception as e:
            logger.error(f"❌ Redis Connection Failed: {e}")
            self.client = None

    def set_session(self, sid: str, data: dict, expire: int = 3600):
        """Save session state to Redis with expiration (default 1 hour)"""
        if self.client:
            try:
                self.client.set(f"session:{sid}", json.dumps(data), ex=expire)
            except Exception as e:
                logger.error(f"Redis Set Error: {e}")

    def get_session(self, sid: str):
        """Retrieve session state from Redis"""
        if self.client:
            try:
                data = self.client.get(f"session:{sid}")
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"Redis Get Error: {e}")
                return None
        return None

    def delete_session(self, sid: str):
        """Remove session from Redis"""
        if self.client:
            try:
                self.client.delete(f"session:{sid}")
            except Exception as e:
                logger.error(f"Redis Delete Error: {e}")

# Global instance
redis_client = RedisClient()
