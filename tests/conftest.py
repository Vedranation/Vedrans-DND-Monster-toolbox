import pytest
from engine import dice


@pytest.fixture(autouse=True)
def reset_rng():
    """Seed the engine RNG before every test for deterministic isolation."""
    dice.seed(0)
    yield
