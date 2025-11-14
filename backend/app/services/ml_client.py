import asyncio
from typing import Any, cast

import httpx
from loguru import logger

from ..core.config import settings
from ..core.exceptions import MLServiceError, MLServiceTimeoutError


class MLServiceClient:
    def __init__(self) -> None:
        self.base_url: str = settings.ml_service_url
        self.timeout: int = settings.ml_service_timeout
        self.max_retries: int = settings.ml_service_max_retries
        self.retry_delay: float = settings.ml_service_retry_delay

    async def rate_script(
        self, text: str, script_id: str | None = None
    ) -> dict[str, Any]:
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/rate_script",
                        json={"text": text, "script_id": script_id},
                    )
                    response.raise_for_status()
                    return cast(dict[str, Any], response.json())

            except httpx.TimeoutException as e:
                last_error = e
                logger.warning(
                    f"ML service timeout on attempt {attempt + 1}/{self.max_retries}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    continue

            except httpx.HTTPStatusError as e:
                logger.error(f"ML service HTTP error: {e.response.status_code}")
                raise MLServiceError(f"HTTP {e.response.status_code}")

            except httpx.RequestError as e:
                last_error = e
                logger.warning(
                    f"ML service connection error on attempt {attempt + 1}/{self.max_retries}: {e}"
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2**attempt))
                    continue

        if isinstance(last_error, httpx.TimeoutException):
            raise MLServiceTimeoutError()
        elif isinstance(last_error, httpx.RequestError):
            raise MLServiceError(f"Connection failed: {str(last_error)}")
        raise MLServiceError("No attempts made")

    async def health_check(self) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return cast(dict[str, Any], response.json())
        except httpx.HTTPError as e:
            logger.error(f"ML service health check failed: {e}")
            raise MLServiceError(f"Health check failed: {str(e)}")


ml_client = MLServiceClient()
