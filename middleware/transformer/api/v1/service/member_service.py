import logging
import json
from fastapi import HTTPException
from backend.services.wallet.member_manager import MemberManager
from backend.services.payments.member_payment_manager import MemberPaymentManager
from backend.infrastructure.db_adapter import db_adapter

logger = logging.getLogger(__name__)


class MemberTransformerService:
    def __init__(self):
        self.manager = MemberManager()
        self.payment_manager = MemberPaymentManager()

    def _parse_error(self, e: Exception) -> str:
        error_str = str(e)
        if "Database Service Error:" in error_str:
            try:
                json_part = error_str.split("Database Service Error: ")[1]
                return json.loads(json_part).get("detail", json_part)
            except:
                return error_str
        return error_str

    async def enroll_member(self, payload) -> dict:
        """
        Relays initial member registration to the Brain.
        """
        data = payload.model_dump(mode="json")
        logger.info(
            f"Entry Point: Enrolling member {data['name']} for {data['fsp_name']}"
        )

        try:
            result = await self.manager.enroll_member(data)

            # --- FIXED: Access the nested 'data' key from Team C's response ---
            db_inner_data = result.get("data", {})
            member_id = db_inner_data.get("id")

            if not member_id:
                logger.error(
                    f"Failed to find ID in nested data. Full response: {result}"
                )
                raise Exception(
                    "Database response format error: missing member ID inside 'data'"
                )

            return {
                "status": "success",
                "message": "Member identity registered successfully",
                "member_id": member_id,
            }
        except Exception as e:
            logger.error(f"❌ Member enrollment failed: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))

    async def activate_member(self, payload) -> dict:
        """
        Triggers the creation of the Rafiki Wallet Address for the member.
        """
        data = payload.model_dump(mode="json")
        member_id = data.get("member_id")

        try:
            result = await self.manager.activate_member_wallet(member_id)
            return {
                "status": "success",
                "message": "Member wallet activated",
                "wallet_url": result["wallet_url"],
            }
        except Exception as e:
            logger.error(f"Member activation failed: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))

    async def transfer_funds(self, payload) -> dict:
        """
        Relays a member-to-member transfer request to the Brain.
        """
        data = payload.model_dump(mode="json")

        try:
            result = await self.payment_manager.execute_member_transfer(
                sender_member_id=str(data["sender_member_id"]),
                receiver_member_id=str(data["receiver_member_id"]),
                amount=float(data["amount"]),
            )
            return {
                "status": "success",
                "message": "Transfer initiated successfully",
                "data": result,  # transaction_id and payment_id
            }
        except Exception as e:
            logger.error(f"❌ Member Transfer API Failed: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))
        
    async def get_all(self) -> dict:
        """
        ENTRY POINT: Returns a list of all registered members.
        Filters out internal Rafiki IDs for security.
        """
        logger.info("Entry Point: Fetching all members from DB")
        
        try:
            result = await db_adapter.get_all_members()
            
            # Team C wraps response in 'data'
            raw_members = result.get("data", [])
            
            clean_list = []
            for member in raw_members:
                # Handle nested status object (same as fsp fix)
                status_obj = member.get("status") or {}
                status_name = status_obj.get("name") if isinstance(status_obj, dict) else status_obj

                clean_list.append({
                    "id": member.get("id"),
                    "fsp_id": member.get("fsp_id"),
                    "name": member.get("name"),
                    "email": member.get("email"),
                    "account_number": member.get("account_number"),
                    "wallet_address": member.get("wallet_address"),
                    "status": status_name,
                    "created_at": member.get("created_at")
                })

            return {
                "status": "success",
                "count": len(clean_list),
                "data": clean_list
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch members list: {str(e)}")
            raise HTTPException(status_code=400, detail=self._parse_error(e))
        
    async def get_by_id(self, member_id: str) -> dict:
        """
        ENTRY POINT: Fetches full details for a specific member.
        """
        logger.info(f"Entry Point: Fetching profile for Member ID: {member_id}")

        try:
            # 1. Fetch from DB via Adapter
            response = await db_adapter.get_member(member_id)
            
            # 2. Extract nested data
            member = response.get("data")
            if not member:
                raise Exception("Member not found in database.")

            # 3. Handle nested status object
            status_obj = member.get("status") or {}
            status_name = status_obj.get("name") if isinstance(status_obj, dict) else status_obj

            # 4. Return clean, formatted profile
            return {
                "status": "success",
                "data": {
                    "id": member.get("id"),
                    "fsp_id": member.get("fsp_id"),
                    "name": member.get("name"),
                    "email": member.get("email"),
                    "account_number": member.get("account_number"),
                    "wallet_address": member.get("wallet_address"),
                    "status": status_name,
                    "kyc": member.get("kyc_details"), # Full KYC is shown for profile view
                    "created_at": member.get("created_at")
                }
            }
        except Exception as e:
            logger.error(f"❌ Failed to fetch member {member_id}: {str(e)}")
            raise HTTPException(status_code=404, detail=self._parse_error(e))
