"""Services package shim for tests.

This file turns the services/ directory into a regular package so tests can
import services.api.app.* reliably during test collection.
"""

__all__ = ["api"]
