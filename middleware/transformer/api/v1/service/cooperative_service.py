import logging
from typing import Dict, Any

# --- IMPORTS FROM BACKEND ---
from backend.infrastructure.db_adapter import db_adapter
from backend.services.wallet.enrollment_manager import EnrollmentManager
from backend.services.payments.funding_manager import funding_manager

from fastapi import HTTPException

logger = logging.getLogger(__name__)

class fspService:
    def __init__(self):
        self.manager = EnrollmentManager()

    # async def enroll_fsp(self, payload) -> Dict[str, Any]:
    #     """
    #     STEP 1: Stores identity AND creates Rafiki Tenant.
    #     """
    #     data = payload.model_dump(mode="json")
    #     logger.info(f"Entry Point: Starting enrollment for {data.get('fsp_name')}")

    #     # The EnrollmentManager handles the Rafiki Tenant + DB save logic
    #     db_response = await self.manager.enroll_fsp(data)

    #     return {
    #         "message": "fsp enrolled and Tenant created successfully",
    #         "fsp_id": db_response["id"],
    #         "tenant_id": db_response["rafiki_metadata"]["tenant_id"]
    #     }
    
    async def enroll_fsp(self, payload) -> Dict[str, Any]:
        data = payload.model_dump(mode="json")
        
        coop_email = data.get("fsp_email")
        coop_name = data.get("fsp_name")

        logger.info(f"Entry Point: Starting enrollment for {coop_name}")

        data["email"] = coop_email 


        try:
            db_response = await self.manager.enroll_fsp(data)
            return {
                "message": "fsp enrolled successfully",
                "fsp_id": db_response["id"]
            }

        except Exception as e:
            error_str = str(e)
            
            if "Database Service Error:" in error_str:
                json_part = error_str.split("Database Service Error: ")[1]
                try:
                    error_json = json.loads(json_part)
                    detail = error_json.get("detail", "Database error occurred")
                except:
                    detail = json_part
                
                raise HTTPException(status_code=400, detail=detail)
            
            raise HTTPException(status_code=500, detail=error_str)

    async def balance_inquiry(self, fsp_id: str) -> Dict[str, Any]:
        """
        Fetches balance directly from Team C's Database API.
        """
        logger.info(f"Entry Point: Checking balance for Coop ID: {fsp_id}")

        result = await db_adapter.get_balance(fsp_id)

        return {
            "status": "success",
            "fsp_id": fsp_id,
            "balance": result.get("balance"), 
            "currency": result.get("currency", "NPR")
        } 
    
    # async def credit_fsp(self, payload) -> Dict[str, Any]:
    #     """
    #     Funds Rafiki Liquidity and Updates DB Balance.
    #     """
    #     data = payload.model_dump(mode="json")
        
    #     coop_id = str(data.get("fsp_id"))
    #     amount = float(data.get("amount"))
    #     ac_num = data.get("fsp_code") 

    #     logger.info(f"Entry Point: Initiating credit for Coop {coop_id}")

    #     result = await funding_manager.deposit_funds(
    #         fsp_id=coop_id,
    #         account_number=ac_num,
    #         amount=amount
    #     )

    #     return {
    #         "status": "success",
    #         "message": f"Successfully credited {amount} NPR",
    #         "data": {
    #             "fsp": result["fsp_name"],
    #             "new_balance": result["new_db_balance"],
    #             "currency": "NPR"
    #         }
    #     }

    async def get_by_details(self, name: str, account_number: str) -> Dict[str, Any]:
        """
        ENTRY POINT: Searches for a fsp's profile.
        """
        logger.info(f"Entry Point: Looking up: {name} (Reg: {account_number})")

        try:
            result = await db_adapter.get_fsp_by_details(name, account_number)
            
            return {
                "status": "success",
                "message": "fsp found",
                "data": {
                    "id": result.get("id"),
                    "name": result.get("fsp_name"),
                    "status": result.get("status"),
                    "account_number": result.get("account_number"),
                    "fsp_email": result.get("fsp_email"),
                    "wallet_url": result.get("rafiki_metadata", {}).get("wallet_address_url")
                }
            }
        except Exception as e:
            # Handle the 'Not Found' case specifically
            if "not found" in str(e).lower():
                logger.warning(f"fsp not found: {name}")
                return {
                    "status": "error",
                    "message": "fsp not found. Please check the name and account number."
                }
            
            logger.error(f"❌ Lookup failed: {str(e)}")
            raise e

    async def get_all(self) -> Dict[str, Any]:
        """
        ENTRY POINT: Returns a list of all registered fsps.
        Safely handles null metadata for non-activated fsps.
        """
        logger.info("Entry Point: Fetching all fsps from DB")
        
        try:
            raw_data = await db_adapter.get_all_fsps()
            
            clean_list = []
            for coop in raw_data:
                metadata = coop.get("rafiki_metadata") or {}
                
                clean_list.append({
                    "id": coop.get("id"),
                    "name": coop.get("fsp_name"),
                    "account_number": coop.get("account_number"),
                    "fsp_code": coop.get("fsp_code"),
                    "status": coop.get("status"),
                    "fsp_email": coop.get("fsp_email"),
                    "wallet_url": metadata.get("wallet_address_url")
                })

            return {
                "status": "success",
                "count": len(clean_list),
                "data": clean_list
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch list: {str(e)}")
            raise e

    async def get_by_id(self, fsp_id: str) -> Dict[str, Any]:
        """
        ENTRY POINT: Fetches a single fsp and cleans the data.
        """
        logger.info(f"Entry Point: Fetching details for Coop ID: {fsp_id}")

        try:
            coop = await db_adapter.get_fsp(fsp_id)
            
            # Safe access to metadata
            metadata = coop.get("rafiki_metadata") or {}

            # Filter data for security (hide tenants_secret)
            clean_data = {
                "id": coop.get("id"),
                "fsp_name": coop.get("fsp_name"),
                "account_number": coop.get("account_number"),
                "pan_number": coop.get("pan_number"),
                "registration_authority": coop.get("registration_authority"),
                "registration_date": coop.get("registration_date"),
                "fsp_type": coop.get("fsp_type"),
                "fsp_code": coop.get("fsp_code"),
                "email": coop.get("fsp_email"),
                "status": coop.get("status"),
                "created_at": coop.get("created_at"),
                "rafiki": {
                    "wallet_address_url": metadata.get("wallet_address_url"),
                    "wallet_address_id": metadata.get("wallet_address_id"),
                    "asset_code": metadata.get("asset_code"),
                    "asset_scale": metadata.get("asset_scale")
                }
            }

            return {
                "status": "success",
                "data": clean_data
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch coop {fsp_id}: {str(e)}")
            raise e