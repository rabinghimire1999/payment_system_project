import httpx
import logging
import json
import hmac
import hashlib
import time
import urllib3
from typing import Any, Dict, Optional
from backend.core.config import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)


def _canonicalize(obj) -> str:
    """
    RFC 8785 / json-canonicalize: recursively sort dict keys,
    no extra whitespace. This is mandatory for Rafiki signature matching.
    """
    if isinstance(obj, dict):
        return (
            "{"
            + ",".join(
                f"{json.dumps(k)}:{_canonicalize(obj[k])}" for k in sorted(obj.keys())
            )
            + "}"
        )
    elif isinstance(obj, list):
        return "[" + ",".join(_canonicalize(i) for i in obj) + "]"
    else:
        return json.dumps(obj, separators=(",", ":"))


class RafikiClient:
    def __init__(self):
        self.url = settings.RAFIKI_ADMIN_URL
        self.admin_api_key = settings.ADMIN_API_SECRET

    async def execute(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a GraphQL mutation or query.
        :param query: The GraphQL string.
        :param variables: Dictionary of variables.
        :param tenant_id: The target tenant ID header. Defaults to Operator.
        :param secret: The secret to use for HMAC signing. Defaults to Admin API Secret.
        """

        request_body = {
            "query": query.strip(),
            "variables": variables or {},
            "operationName": None,
        }

        canonical_body = _canonicalize(request_body)

        timestamp = int(time.time() * 1000)
        payload_to_sign = f"{timestamp}.{canonical_body}"

        # 3. Determine the signing secret
        signing_secret = secret if secret else self.admin_api_key

        # 4. Generate HMAC SHA256 digest
        digest = hmac.new(
            signing_secret.encode("utf-8"),
            payload_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # 5. Construct headers
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.admin_api_key,
            "signature": f"t={timestamp}, v1={digest}",
            "tenant-id": tenant_id if tenant_id else settings.OPERATOR_TENANT_ID,
        }

        async with httpx.AsyncClient(verify=False) as client:
            try:
                response = await client.post(
                    self.url, content=canonical_body, headers=headers, timeout=15.0
                )

                # Handle 401 explicitly (often returns plain text "Unauthorized")
                if response.status_code == 401:
                    logger.error(f"❌ 401 Unauthorized. Check your secrets.")
                    raise Exception("Rafiki Auth Failed: 401 Unauthorized")

                if response.status_code != 200:
                    logger.error(f"❌ HTTP {response.status_code}: {response.text}")
                    raise Exception(f"Rafiki HTTP Error: {response.status_code}")

                res_json = response.json()

                # Check for GraphQL-level errors
                if "errors" in res_json:
                    msg = res_json["errors"][0].get("message", "Unknown GraphQL Error")
                    logger.error(f"❌ Rafiki GraphQL Error: {msg}")
                    raise Exception(f"Rafiki GraphQL Error: {msg}")

                return res_json.get("data", {})

            except json.JSONDecodeError:
                logger.error(f"Failed to decode Rafiki response: {response.text}")
                raise Exception(f"Invalid JSON from Rafiki: {response.text}")
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise


rafiki_client = RafikiClient()
