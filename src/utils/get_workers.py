import logging
import os

logger = logging.getLogger(__name__)


def get_workers() -> int:
    """
    Calculate optimal worker count based on CPU cores and I/O-bound nature.

    For I/O-bound tasks (like network requests), more workers can be beneficial:
    - CPU cores = 4 → recommended: 6-8 workers
    - CPU cores = 8 → recommended: 10-12 workers
    - CPU cores = 16 → recommended: 16-20 workers

    Formula: cpu_count * 1.5 to cpu_count * 2.5 (capped at 20 for safety)
    """
    cpu_count = os.cpu_count() or 4
    optimal = min(cpu_count * 2, 20)

    logger.info(
        f"CPU cores detected: {cpu_count} → "
        f"Optimal workers for I/O-bound tasks: {optimal}"
    )
    return optimal
