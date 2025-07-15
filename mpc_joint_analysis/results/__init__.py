"""
Results Layer

This module provides functionality for aggregating, filtering, and visualizing
results from MPC computations in a privacy-preserving manner.
"""

from .aggregator import (
    SecureAggregator,
    AggregatorError,
    ComputationResult,
    AggregationRequest,
    AggregatedResult,
    AggregationType,
    ResultType
)
from .privacy_filter import (
    PrivacyFilter,
    PrivacyFilterError,
    PrivacyBudget,
    PrivacyPolicy,
    PrivacyMechanism,
    NoiseType,
    DifferentialPrivacy,
    KAnonymity,
    LDiversity
)
from .visualizer import (
    PrivacyAwareVisualizer,
    VisualizerError,
    VisualizationConfig,
    VisualizationResult,
    ChartType,
    OutputFormat
)

__all__ = [
    # Aggregator
    'SecureAggregator',
    'AggregatorError',
    'ComputationResult',
    'AggregationRequest',
    'AggregatedResult',
    'AggregationType',
    'ResultType',
    
    # Privacy Filter
    'PrivacyFilter',
    'PrivacyFilterError',
    'PrivacyBudget',
    'PrivacyPolicy',
    'PrivacyMechanism',
    'NoiseType',
    'DifferentialPrivacy',
    'KAnonymity',
    'LDiversity',
    
    # Visualizer
    'PrivacyAwareVisualizer',
    'VisualizerError',
    'VisualizationConfig',
    'VisualizationResult',
    'ChartType',
    'OutputFormat'
]