import logging
from backend.infrastructure.db_adapter import db_adapter
from backend.core.security import verify_password, create_access_token

logger = logging.getLogger(__name__)


class AuthService:
    async def login_fsp(self, email: str, password: str):
        try:
            coop = await db_adapter.get_fsp_by_email(email)
        except Exception as e:
            logger.error(f"Login failed: Email {email} not found. Error: {str(e)}")
            raise Exception("Invalid email or password")

        status_obj = coop.get("status") or {}
        status_name = (
            status_obj.get("name") if isinstance(status_obj, dict) else status_obj
        )

        if status_name != "ACTIVE":
            logger.warning(f"Login blocked: {email} status is {status_name}")
            raise Exception("Account is not yet activated. Please contact ipg admin.")

        stored_hash = coop.get("password_hash")
        if not stored_hash or not verify_password(password, stored_hash):
            logger.warning(f"Login failed: Wrong password for {email}")
            raise Exception("Invalid email or password")

        token = create_access_token(
            data={
                "sub": str(coop["id"]),
                "email": email,
                "name": coop.get("fsp_name"),
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "fsp_id": coop["id"],
        }


auth_service = AuthService()
