"""MON (Moson Web Intelligence Engine).

A modular web intelligence engine for inspecting websites, understanding
frontend architecture, discovering backend APIs, and reconstructing
application structure.

Usage:
    from mon import inspect

    result = inspect(domain="example.com", action="all_data")
"""

from mon.sdk import inspect

__version__ = "1.0.0"
__all__ = ["inspect"]
