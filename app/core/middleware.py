import time
import uuid
from loguru import logger
from fastapi import Request

async def log_requests_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    with logger.contextualize(request_id=request_id):
        logger.info(f"Request started: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            logger.info(f"Request completed: {response.status_code} | Time: {process_time:.2f}ms")
            return response
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise e
