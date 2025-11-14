import httpx
from loguru import logger
from ..core.config import settings


class MLServiceClient:
    def __init__(self):
        self.base_url = settings.ml_service_url
        self.timeout = 300.0

    async def rate_script(self, text: str, script_id: str | None = None) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rate_script",
                    json={"text": text, "script_id": script_id},
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"ML service error: {e}")
                raise

    async def health_check(self) -> dict:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"ML service health check failed: {e}")
                raise


ml_client = MLServiceClient()
