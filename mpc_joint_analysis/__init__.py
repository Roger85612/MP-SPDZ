"""
MPC-Based Joint Data Analysis System

A secure multi-party computation system that enables multiple parties to perform 
joint data analysis while keeping their individual datasets private.
Built on the MP-SPDZ framework.

Author: System Architecture Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "System Architecture Team"

# Import main modules
from . import data_ingestion
from . import analytics
from . import protocol_layer
from . import security
from . import results

# Main system configuration
SYSTEM_CONFIG = {
    "default_protocol": "mascot",
    "default_security_level": "semi-honest",
    "max_parties": 10,
    "timeout_seconds": 300,
    "enable_logging": True,
    "log_level": "INFO"
}

def get_version():
    """Get the current version of the system."""
    return __version__

def get_config():
    """Get the current system configuration."""
    return SYSTEM_CONFIG.copy()