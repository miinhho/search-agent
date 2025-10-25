import logging
import os

logger = logging.getLogger(__name__)


def get_workers() -> int:
    """
    Calculate optimal worker count based on CPU cores and I/O-bound nature.

    For I/O-bound tasks (like network requests), more workers can be beneficial.

    Formula: cpu_count * 1.5 to cpu_count * 2.5 (capped at 32 for safety)
    """
    cpu_count = os.cpu_count() or 4
    optimal = min(cpu_count * 2 + 1, 32)

    logger.debug(
        f"CPU cores detected: {cpu_count} → "
        f"Optimal workers for I/O-bound tasks: {optimal}"
    )
    return optimal
