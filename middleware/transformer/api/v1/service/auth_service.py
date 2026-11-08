import logging
from backend.services.auth.auth_service import auth_service # Import Team B's Brain logic

logger = logging.getLogger(__name__)

class AuthTransformerService:
    def __init__(self):
        self.brain = auth_service

    async def login(self, payload):
        """
        Relays the login request to the Backend Brain.
        """
        data = payload.model_dump(mode="json")
        email = data.get("email")
        password = data.get("password")

        logger.info(f"Entry Point: Attempting login for {email}")

        # Call the actual logic in Team B's backend
        result = await self.brain.login_fsp(email, password)

        return {
            "status": "success",
            "message": "Login successful",
            "data": result # Contains access_token and token_type
        }