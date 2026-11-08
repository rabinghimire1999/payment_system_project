import logging
from typing import Dict, Any
from backend.services.wallet.tenant import TenantService
from backend.services.wallet.asset import AssetService
from backend.services.wallet.wallet import WalletService
from backend.infrastructure.db_adapter import db_adapter
from backend.core.security import hash_password
from backend.services.wallet.liquidity import liquidity_service
from backend.core.config import settings

logger = logging.getLogger(__name__)


class EnrollmentManager:
    def __init__(self):
        self.tenant_service = TenantService()
        self.asset_service = AssetService()
        self.wallet_service = WalletService()

    # --- STEP 1: INITIAL ENROLLMENT (TENANT + KYC) ---
    # async def enroll_fsp(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Safety First:
    #     1. Store the fsp's legal identity in the DB first.
    #     2. THEN, create the Rafiki Tenant.
    #     3. If Rafiki fails, the coop is still registered (we can retry).
    #     """
    #     coop_name = kyc_data.get("fsp_name")
    #     email = kyc_data.get("email") or kyc_data.get("fsp_email")
    #     password = kyc_data.get("password")

    #     initial_db_payload = {
    #         "fsp_name": coop_name,
    #         "account_number": kyc_data.get("account_number"),
    #         "pan_number": kyc_data.get("pan_number"),
    #         "registration_authority": kyc_data.get("registration_authority"),
    #         "registration_date": str(kyc_data.get("registration_date")),
    #         "fsp_type": kyc_data.get("fsp_type", "SAVING"),
    #         "fsp_code": kyc_data.get("fsp_code"),
    #         "fsp_email": email,
    #         "password_hash": hash_password(password),
    #     }

    #     # --- STEP A: SAVE TO DB FIRST ---
    #     logger.info(f"Step 1: Storing KYC for {coop_name}...")
    #     db_coop = await db_adapter.create_fsp(initial_db_payload)
    #     internal_id = db_coop["id"]

    #     # --- STEP B: CREATE RAFIKI TENANT ---
    #     try:
    #         logger.info(f"Step 2: Creating Rafiki Tenant for DB ID {internal_id}...")
    #         tenant = await self.tenant_service.create_tenant(
    #             name=coop_name, email=email
    #         )

    #         # --- STEP C: PATCH DB WITH TENANT ---
    #         tenant_payload = {
    #             "rafiki_metadata": {
    #                 "tenant_id": tenant["tenant_id"],
    #                 "tenants_secret": tenant["api_secret"],
    #             }
    #         }

    #         await db_adapter.update_rafiki_info(internal_id, tenant_payload)
    #         logger.info(f"Enrollment Phase 1 complete for ID {internal_id}")

    #         return {"id": internal_id, **tenant_payload}

    #     except Exception as e:
    #         logger.error(
    #             f"❌ Rafiki Tenant creation failed for DB ID {internal_id}: {str(e)}"
    #         )
    #         raise e

    async def enroll_fsp(self, kyc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        1. Store the fsp's legal identity in the DB first (Safety First).
        2. Create the Rafiki Tenant.
        3. Configure the Tenant's WALLET_ADDRESS_URL (Namespace/Prefix).
        4. Store the Tenant ID/Secret in the DB.
        """
        coop_name = kyc_data.get("fsp_name")
        email = kyc_data.get("email") or kyc_data.get("fsp_email")
        password = kyc_data.get("password")
        # Get the code to create a unique prefix (e.g., NAB01)
        coop_code = kyc_data.get("fsp_code", "coop").lower().strip()

        # --- STEP A: SAVE TO DB FIRST (Identity Only) ---
        initial_db_payload = {
            "fsp_name": coop_name,  # Map to Team C's 'name'
            "account_number": kyc_data.get("account_number"),
            "pan_number": kyc_data.get("pan_number"),
            "registration_authority": kyc_data.get("registration_authority"),
            "registration_date": str(kyc_data.get("registration_date")),
            "fsp_type": kyc_data.get("fsp_type", "SAVING"),
            "fsp_code": coop_code,
            "fsp_email": email,
            "password_hash": hash_password(password),
        }

        logger.info(f"Step 1: Storing KYC for {coop_name}...")
        db_coop = await db_adapter.create_fsp(initial_db_payload)
        internal_id = db_coop["id"]

        # --- STEP B: CREATE RAFIKI TENANT ---
        try:
            logger.info(f"Step 2: Creating Rafiki Tenant for DB ID {internal_id}...")
            tenant = await self.tenant_service.create_tenant(
                name=coop_name, email=email
            )
            t_id = tenant["tenant_id"]
            t_secret = tenant["api_secret"]

            # --- STEP C: CONFIGURE TENANT PREFIX (Critical for Members) ---
            # Result: https://rafiki-backend.testnet.test/nab01/
            tenant_prefix = (
                f"{settings.RAFIKI_WALLET_BASE_URL.rstrip('/')}/{coop_code}/"
            )

            logger.info(
                f"Step 3: Configuring Wallet Prefix for Tenant: {tenant_prefix}"
            )
            await self.tenant_service.set_wallet_address_url(
                tenant_id=t_id, tenant_secret=t_secret, base_url=tenant_prefix
            )

            # --- STEP D: PATCH DB WITH TENANT DATA ---
            # We store the prefix here so we can find it when adding members later
            tenant_payload = {
                "rafiki_metadata": {
                    "tenant_id": t_id,
                    "tenants_secret": t_secret,
                    "wallet_address_prefix": tenant_prefix,
                }
            }

            await db_adapter.update_rafiki_info(internal_id, tenant_payload)
            logger.info(f"✅ Enrollment Phase 1 complete for ID {internal_id}")

            return {"id": internal_id, **tenant_payload}

        except Exception as e:
            logger.error(f"❌ Rafiki setup failed for DB ID {internal_id}: {str(e)}")
            # Note: The DB record exists but has null metadata, allowing for a retry.
            raise e

    # --- STEP 2: WALLET ACTIVATION (ASSET + WALLET) ---
    async def activate_fsp_wallet(self, fsp_id: str) -> Dict[str, Any]:
        """
        Uses existing Tenant ID and Prefix to create Asset and Wallet.
        """
        logger.info(f"🚀 Step 2: Activating Wallet for Coop ID: {fsp_id}")

        coop = await db_adapter.get_fsp(fsp_id)
        meta = coop.get("rafiki_metadata") or {}

        t_id = meta.get("tenant_id")
        t_secret = meta.get("tenants_secret")
        # --- NEW: Get the prefix we saved in Step 1 ---
        t_prefix = meta.get("wallet_address_prefix")

        if not t_id or not t_prefix:
            raise Exception(
                "Cannot activate: Tenant ID or Prefix missing in DB. Run Step 1 first."
            )

        # 1. Rafiki: Asset
        asset = await self.asset_service.create_npr_asset(
            tenant_id=t_id, tenant_secret=t_secret
        )

        # --- THE FIX: Build the address based on the Prefix ---
        # Instead of a top-level slug, we create a wallet called 'main' inside the prefix
        # Result: https://rafiki-backend.testnet.test/rdrcl222/main
        coop_wallet_address = f"{t_prefix.rstrip('/')}/main"

        # 2. Rafiki: Wallet
        logger.info(
            f"Creating fsp Wallet at authorized path: {coop_wallet_address}"
        )
        wallet = await self.wallet_service.create_wallet(
            tenant_id=t_id,
            asset_id=asset["id"],
            public_name=coop["fsp_name"],
            address=coop_wallet_address,  # Pass the authorized address
            secret=t_secret,
        )

        # 3. Final Settlement (The 10M credit line)
        await liquidity_service.fund_asset(asset_id=asset["id"], amount=1000000000)

        # 4. Final Database Patch
        full_metadata = {
            "rafiki_metadata": {
                "tenant_id": t_id,
                "tenants_secret": t_secret,
                "wallet_address_prefix": t_prefix,
                "wallet_address_id": wallet["id"],
                "wallet_address_url": wallet["url"],
                "asset_id": asset["id"],
                "asset_code": "NPR",
                "asset_scale": 2,
            }
        }

        await db_adapter.update_rafiki_info(fsp_id, full_metadata)

        return {"id": fsp_id, "wallet_url": wallet["url"], "status": "ACTIVE"}
