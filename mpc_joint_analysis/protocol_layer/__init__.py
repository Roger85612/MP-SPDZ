"""
Protocol Layer

This module provides protocol selection and wrapper functionality for various
MPC protocols supported by MP-SPDZ.
"""

from .protocol_selector import ProtocolSelector, ProtocolError
from .mascot_wrapper import MascotWrapper
from .shamir_wrapper import ShamirWrapper
from .atlas_wrapper import AtlasWrapper
from .semi_wrapper import SemiWrapper
from .semi2k_wrapper import Semi2KWrapper
from .brain_wrapper import BrainWrapper

__all__ = [
    'ProtocolSelector',
    'ProtocolError',
    'MascotWrapper',
    'ShamirWrapper',
    'AtlasWrapper',
    'SemiWrapper',
    'Semi2KWrapper',
    'BrainWrapper'
]