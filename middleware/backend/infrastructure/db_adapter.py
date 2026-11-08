import httpx
import logging
from typing import Dict, Any, Optional
from backend.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    def __init__(self):
        self.base_url = settings.DATABASE_SERVICE_URL.rstrip("/")
        self.api_key = settings.DATABASE_API_KEY
        self.timeout = 10.0

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
        }

        async with httpx.AsyncClient(follow_redirects=True) as client:
            try:
                response = await client.request(
                    method,
                    url,
                    json=data,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )

                if response.status_code >= 400:
                    logger.error(
                        f"DB Service Error ({response.status_code}): {response.text}"
                    )
                    if response.status_code in [401, 403]:
                        raise Exception(
                            "Database Authorization Failed: Invalid X-API-Key"
                        )
                    raise Exception(f"Database Service Error: {response.text}")

                return response.json()
            except Exception as e:
                logger.error(f"Request to DB failed: {url} | Error: {str(e)}")
                raise

    # --- fsp Operations ---
    async def get_fsp(self, coop_id: str) -> Dict[str, Any]:
        """
        Fetches a single fsp by its internal database ID.
        Endpoint: GET /v1/internal/fsp/{id}
        """
        return await self._request("GET", f"internal/fsp/{coop_id}")

    async def create_fsp(self, data: Dict) -> Dict[str, Any]:
        return await self._request("POST", "internal/fsp/", data)

    async def update_rafiki_info(
        self, coop_id: str, rafiki_data: Dict
    ) -> Dict[str, Any]:
        return await self._request(
            "PATCH", f"internal/fsp/{coop_id}", rafiki_data
        )

    async def get_fsp_by_details(
        self, name: str, account_number: str
    ) -> Dict[str, Any]:
        query_params = {
            "fsp_name": name,
            "account_number": account_number,
        }
        return await self._request(
            "GET", "internal/fsp/lookup/", params=query_params
        )

    async def get_all_fsps(self) -> Any:
        """
        Fetches the complete list of fsps from Team C's database.
        """
        # Endpoint: GET /v1/internal/fsp/
        return await self._request("GET", "internal/fsp/")

    async def get_fsp_by_email(self, email: str) -> Dict[str, Any]:
        """
        Fetches a fsp record from the database using a path parameter.
        Endpoint: GET internal/fsp/email/{email}
        """

        endpoint = f"internal/fsp/email/{email}"

        return await self._request("GET", endpoint)

    async def get_fsp_transactions(self, coop_id: str) -> Any:
        """
        Fetches all transactions involving this fsp from the DB.
        """
        return await self._request(
            "GET", f"internal/transactions/fsp/{coop_id}"
        )

    async def get_fsp_by_tenant_id(
        self, tenant_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup: Finds the fsp that owns a specific Rafiki Tenant ID.
        """
        try:
            return await self._request(
                "GET", f"internal/fsp/tenant/{tenant_id}"
            )
        except Exception:
            return None

    # --- Balance & Ledger Operations ---
    async def get_balance(self, coop_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"internal/balances/{coop_id}/balance")

    async def update_balance(
        self, coop_id: str, amount: int, entry_type: str
    ) -> Dict[str, Any]:
        payload = {"amount": amount, "type": entry_type}
        return await self._request(
            "PATCH", f"/internal/balances/{coop_id}/credit", payload
        )

    # --- Transaction Operations ---
    async def create_transaction(self, data: Dict) -> Dict[str, Any]:

        return await self._request("POST", "/internal/transactions", data)

    async def update_transaction_status(
        self, tx_id: str, status: str, rafiki_payment_id: str
    ) -> Dict:
        payload = {"status": status, "rafiki_payment_id": rafiki_payment_id}
        return await self._request("PATCH", f"internal/transactions/{tx_id}/", payload)

    async def validate_fsp_uniqueness(
        self, name: str, account_number: str, email: str
    ) -> Optional[str]:
        try:
            all_coops = await self.get_all_fsps()

            logger.info(
                f"Checking uniqueness for Name: {name}, Account: {account_number}"
            )
            logger.info(f"Database returned {len(all_coops)} fsps.")

            for coop in all_coops:

                db_name = coop.get("fsp_name")
                db_account = coop.get("account_number")
                db_email = coop.get("fsp_email")

                logger.info(f"Comparing against: {db_name} | {db_account}")

                if db_name and db_name.lower() == name.lower():
                    return f"The co-operative name '{name}' is already registered."

                if db_account and db_account == account_number:
                    return (
                        f"The account number '{account_number}' is already registered."
                    )

                if db_email and db_email.lower() == email.lower():
                    return f"The email '{email}' is already exists."

            return None
        except Exception as e:
            logger.error(f"Failed to validate uniqueness: {e}")
            raise Exception("Could not validate fsp uniqueness.")

    async def get_transaction(self, tx_id: str) -> Dict[str, Any]:
        """
        Fetches a single transaction by its internal database ID.
        Endpoint: GET /v1/internal/transactions/{id}/
        """
        # Ensure trailing slash to match Team C's pattern
        return await self._request("GET", f"internal/transactions/{tx_id}/")

    async def get_transaction_by_payment_id(
        self, payment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a transaction from the database by its linked Rafiki payment ID.
        Used by the Webhook EventHandler to finalize records.
        """
        try:
            return await self._request(
                "GET", f"internal/transactions/payment/{payment_id}"
            )
        except Exception:
            return None

    # --- Member Operations ---
    async def create_member(self, data: Dict) -> Dict[str, Any]:
        """
        Creates a new member record.
        Team C now expects 'fsp_name' in the JSON body.
        """
        # Endpoint: POST /v1/internal/member/
        return await self._request("POST", "internal/member/", data)

    async def get_member(self, member_id: str) -> Dict[str, Any]:
        return await self._request("GET", f"internal/member/{member_id}")

    async def update_member_wallet(
        self, member_id: str, wallet_data: Dict
    ) -> Dict[str, Any]:
        return await self._request("PATCH", f"internal/member/{member_id}", wallet_data)

    # --- Member Transaction Operations ---

    async def create_member_transaction(self, data: Dict) -> Dict[str, Any]:
        """
        Creates a new member-level transaction log.
        Endpoint: POST /v1/internal/member-transaction/
        """
        # Ensure trailing slash to match Team C pattern
        return await self._request("POST", "internal/member-transaction/", data)

    async def update_member_transaction_status(
        self, tx_id: str, status: str, payment_id: str
    ) -> Dict:
        """
        Updates the status and links the Rafiki Payment ID.
        Endpoint: PATCH /v1/internal/member-transaction/{transaction_id}/
        """
        payload = {"status": status, "payment_id": payment_id}  # Matches Team C schema
        return await self._request(
            "PATCH", f"internal/member-transaction/{tx_id}/", payload
        )

    async def get_member_transaction_by_payment_id(
        self, payment_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup: Finds the internal transaction record using the Rafiki Payment ID.
        """
        try:
            return await self._request(
                "GET", f"internal/member-transaction/payment/{payment_id}/"
            )
        except Exception:
            return None

    async def get_member_by_rafiki_id(
        self, wallet_address_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup a member using their Rafiki Wallet UUID.
        """
        try:
            return await self._request(
                "GET", f"internal/member/wallet/{wallet_address_id}"
            )
        except Exception:
            return None

    async def get_all_members(self) -> Any:
        """
        Fetches the complete list of members from Team C's database.
        Endpoint: GET /v1/internal/member/
        """
        return await self._request("GET", "internal/member/")
    
    async def get_member(self, member_id: str) -> Dict[str, Any]:
        """
        Fetches a specific member's details.
        Endpoint: GET /v1/internal/member/{member_id}
        """
        return await self._request("GET", f"internal/member/{member_id}")

db_adapter = DatabaseAdapter()
