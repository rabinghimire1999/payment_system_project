import logging
import re
from typing import Dict, Any
from backend.services.wallet.wallet import WalletService
from backend.infrastructure.db_adapter import db_adapter

logger = logging.getLogger(__name__)


class MemberManager:
    def __init__(self):
        self.wallet_service = WalletService()

    def _generate_unique_slug(self, name: str, unique_id: str) -> str:
        """
        Creates a unique slug: 'Pankaj Kumar' + '123' -> 'pankaj-kumar-123'
        """
        name_slug = name.lower().strip().replace(" ", "-")
        name_slug = re.sub(r"[^a-z0-9-]", "", name_slug)

        suffix = str(unique_id)[-4:] if len(str(unique_id)) > 4 else str(unique_id)

        return f"{name_slug}-{suffix}"

    async def enroll_member(self, member_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        PHASE 1: Store identity in DB.
        member_payload contains 'fsp_name', 'name', 'email', 'kyc_details'.
        """
        logger.info(
            f"Registering member {member_payload.get('name')} for Coop: {member_payload.get('fsp_name')}"
        )

        # Construct the payload matching Team C's new schema
        db_payload = {
            "fsp_name": member_payload.get("fsp_name"),
            "name": member_payload.get("name"),
            "email": member_payload.get("email"),
            "account_number": member_payload.get("account_number"),  # <--- ADDED
            "kyc_details": member_payload.get("kyc_details"),
            "wallet_address": None,
        }

        return await db_adapter.create_member(db_payload)

    async def activate_member_wallet(self, member_id: str) -> Dict[str, Any]:
        """
        STEP 2: Financial Activation.
        FIXED: Correctly handles nested 'data' from Database Service.
        """
        # 1. Fetch Member from DB
        member_response = await db_adapter.get_member(member_id)

        # --- THE FIX: Extract the nested data ---
        member = member_response.get("data")
        if not member:
            raise Exception(
                f"Member details not found in database response for ID {member_id}"
            )

        # Now printing will show the actual member object
        logger.info(
            f"Fetched Member: {member['name']} (Coop ID: {member['fsp_id']})"
        )

        coop_id = member.get("fsp_id")

        # 2. Fetch Parent fsp metadata
        coop = await db_adapter.get_fsp(coop_id)
        meta = coop.get("rafiki_metadata") or {}

        t_id = meta.get("tenant_id")
        t_secret = meta.get("tenants_secret") or meta.get("tenants_secrect")
        a_id = meta.get("asset_id")
        coop_wallet_url = meta.get("wallet_address_url")

        if not t_id or not a_id:
            raise Exception("Parent fsp is not activated in Rafiki.")

        # 3. Generate unique address
        unique_slug = self._generate_unique_slug(member["name"], member_id)
        member_address = f"{coop_wallet_url}/{unique_slug}"

        try:
            logger.info(f"Creating UNIQUE member wallet: {member_address}")

            # 4. Create in Rafiki
            rafiki_wallet = await self.wallet_service.create_wallet(
                tenant_id=t_id,
                asset_id=a_id,
                public_name=member["name"],
                address=member_address,
                secret=t_secret,
            )

            # 5. Final DB Update
            update_payload = {
                "wallet_address": member_address,
                "wallet_address_id": rafiki_wallet["id"],
            }

            logger.info(f"Step 5: Updating DB with Wallet ID {rafiki_wallet['id']}")

            await db_adapter.update_member_wallet(member_id, update_payload)

            return {
                "member_id": member_id,
                "wallet_url": member_address,
                "wallet_address_id": rafiki_wallet["id"],
                "status": "ACTIVE",
            }

        except Exception as e:
            logger.error(f"❌ Member activation failed: {str(e)}")
            raise e
