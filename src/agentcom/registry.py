"""
Global registry for storing registered capabilities.

This module maintains a centralized list of capabilities that are
decorated with @capability decorator across the application.
"""
from typing import List, Dict, Any

# Global structure to register endpoints as capabilities
REGISTERED_ENDPOINTS: List[Dict[str, Any]] = []
