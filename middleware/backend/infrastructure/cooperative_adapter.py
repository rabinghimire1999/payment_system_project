import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger(__name__)


class fspAdapter:
    """
    This adapter is responsible for communicating with the fsp's
    actual Core Banking System (CBS).

    For now, it mimics the behavior. Later, it will be replaced
    with real REST/SOAP calls to the fsp's API.
    """

    def __init__(self):
        # In the future, this would be the fsp's API Base URL
        self.timeout = 5.0

    async def check_balance(self, account_number: str, amount: float) -> bool:
        """
        Verify if the fsp has enough funds in their REAL account.
        """
        logger.info(
            f"Checking real-world balance for AC: {account_number} for amount: {amount} NPR"
        )

        # --- MIMIC LOGIC ---
        # For now, we assume everyone has money up to 1,000,000 NPR
        if amount <= 100000:
            logger.info(f"Real-world balance verified for {account_number}")
            return True

        logger.warning(f"❌ Insufficient real-world funds for {account_number}")
        return False

    async def lock_funds(
        self, account_number: str, amount: float, reference: str
    ) -> bool:
        """
        Optional: Instructs the fsp's CBS to put a 'Hold' on the funds
        so they cannot be spent elsewhere while Rafiki settles.
        """
        logger.info(
            f"Placing hold of {amount} NPR on AC: {account_number}. Ref: {reference}"
        )
        # Mimic success
        return True


# Instantiate the singleton
coop_adapter = fspAdapter()
