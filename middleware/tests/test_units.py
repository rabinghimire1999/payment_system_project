import pytest
from backend.services.wallet.wallet import WalletService


def test_slug_generation():
    service = WalletService()
    # Test normalization
    assert service._generate_slug("Nabil fsp") == "nabil-fsp"
    # Test special characters
    assert service._generate_slug("Test! @# Coop") == "test-coop"


def test_currency_scaling():
    # Test NPR to Paisa conversion
    amount = 10.50
    scale = 2
    units = int(amount * (10**scale))
    assert units == 1050
