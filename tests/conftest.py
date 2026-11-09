from collections.abc import Iterator
from typing import Any

import pytest
from braintrust import logger
from braintrust.test_helpers import init_test_logger


@pytest.fixture
def spans() -> Iterator[Any]:
    """Capture Braintrust spans in memory (no network). Call `.pop()` to read them."""
    logger._state.reset_parent_state()
    with logger._internal_with_memory_background_logger() as bgl:
        init_test_logger("cv-tailor-py-tests")
        yield bgl
    logger._state.reset_parent_state()
