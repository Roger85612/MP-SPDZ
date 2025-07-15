"""
Results Aggregator Module

Handles aggregation of results from multiple parties and MPC computations,
ensuring secure and privacy-preserving combination of outputs.
"""

import logging
import json
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import statistics
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AggregatorError(Exception):
    """Custom exception for aggregator errors."""
    pass

class AggregationType(Enum):
    """Types of aggregation operations."""
    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    STD = "std"
    VAR = "var"
    PERCENTILE = "percentile"
    HISTOGRAM = "histogram"
    WEIGHTED_MEAN = "weighted_mean"

class ResultType(Enum):
    """Types of results that can be aggregated."""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    STATISTICAL = "statistical"
    MODEL_PARAMETERS = "model_parameters"
    BINARY = "binary"
    VECTOR = "vector"
    MATRIX = "matrix"

@dataclass
class ComputationResult:
    """Represents a result from an MPC computation."""
    party_id: int
    computation_id: str
    result_type: ResultType
    data: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    quality_score: float = 1.0
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'party_id': self.party_id,
            'computation_id': self.computation_id,
            'result_type': self.result_type.value,
            'data': self.data,
            'metadata': self.metadata,
            'timestamp': self.timestamp,
            'quality_score': self.quality_score,
            'confidence': self.confidence
        }

@dataclass
class AggregationRequest:
    """Represents a request for result aggregation."""
    request_id: str
    computation_id: str
    aggregation_type: AggregationType
    party_ids: List[int]
    parameters: Dict[str, Any] = field(default_factory=dict)
    weights: Optional[Dict[int, float]] = None
    quality_threshold: float = 0.5
    confidence_threshold: float = 0.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'request_id': self.request_id,
            'computation_id': self.computation_id,
            'aggregation_type': self.aggregation_type.value,
            'party_ids': self.party_ids,
            'parameters': self.parameters,
            'weights': self.weights,
            'quality_threshold': self.quality_threshold,
            'confidence_threshold': self.confidence_threshold
        }

@dataclass
class AggregatedResult:
    """Represents an aggregated result."""
    request_id: str
    computation_id: str
    aggregation_type: AggregationType
    result: Any
    contributing_parties: List[int]
    quality_score: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'request_id': self.request_id,
            'computation_id': self.computation_id,
            'aggregation_type': self.aggregation_type.value,
            'result': self.result,
            'contributing_parties': self.contributing_parties,
            'quality_score': self.quality_score,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'timestamp': self.timestamp
        }

class SecureAggregator:
    """Handles secure aggregation of MPC results."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.results_cache = {}  # computation_id -> list of ComputationResult
        self.aggregated_results = {}  # request_id -> AggregatedResult
        self.aggregation_functions = self._initialize_aggregation_functions()
        self.quality_weights = config.get('quality_weights', True)
        self.confidence_weights = config.get('confidence_weights', True)
        
        logger.info("Secure aggregator initialized")
    
    def _initialize_aggregation_functions(self) -> Dict[AggregationType, callable]:
        """Initialize aggregation functions."""
        return {
            AggregationType.SUM: self._aggregate_sum,
            AggregationType.MEAN: self._aggregate_mean,
            AggregationType.MEDIAN: self._aggregate_median,
            AggregationType.COUNT: self._aggregate_count,
            AggregationType.MIN: self._aggregate_min,
            AggregationType.MAX: self._aggregate_max,
            AggregationType.STD: self._aggregate_std,
            AggregationType.VAR: self._aggregate_var,
            AggregationType.PERCENTILE: self._aggregate_percentile,
            AggregationType.HISTOGRAM: self._aggregate_histogram,
            AggregationType.WEIGHTED_MEAN: self._aggregate_weighted_mean
        }
    
    def add_result(self, result: ComputationResult):
        """Add a computation result to the aggregator."""
        try:
            if result.computation_id not in self.results_cache:
                self.results_cache[result.computation_id] = []
            
            self.results_cache[result.computation_id].append(result)
            logger.info(f"Added result from party {result.party_id} for computation {result.computation_id}")
            
        except Exception as e:
            logger.error(f"Error adding result: {e}")
            raise AggregatorError(f"Failed to add result: {e}")
    
    def aggregate_results(self, request: AggregationRequest) -> AggregatedResult:
        """Aggregate results based on the request."""
        try:
            # Get results for the computation
            computation_results = self.results_cache.get(request.computation_id, [])
            
            if not computation_results:
                raise AggregatorError(f"No results found for computation {request.computation_id}")
            
            # Filter results by party IDs and quality/confidence thresholds
            filtered_results = self._filter_results(computation_results, request)
            
            if not filtered_results:
                raise AggregatorError("No results meet the quality and confidence thresholds")
            
            # Perform aggregation
            aggregation_func = self.aggregation_functions.get(request.aggregation_type)
            if not aggregation_func:
                raise AggregatorError(f"Unsupported aggregation type: {request.aggregation_type}")
            
            aggregated_value = aggregation_func(filtered_results, request)
            
            # Calculate aggregate quality and confidence
            quality_score = self._calculate_aggregate_quality(filtered_results, request)
            confidence = self._calculate_aggregate_confidence(filtered_results, request)
            
            # Create aggregated result
            aggregated_result = AggregatedResult(
                request_id=request.request_id,
                computation_id=request.computation_id,
                aggregation_type=request.aggregation_type,
                result=aggregated_value,
                contributing_parties=[r.party_id for r in filtered_results],
                quality_score=quality_score,
                confidence=confidence,
                metadata={
                    'num_contributing_parties': len(filtered_results),
                    'aggregation_parameters': request.parameters
                }
            )
            
            # Cache the result
            self.aggregated_results[request.request_id] = aggregated_result
            
            logger.info(f"Aggregated results for request {request.request_id}")
            return aggregated_result
            
        except Exception as e:
            logger.error(f"Error aggregating results: {e}")
            raise AggregatorError(f"Failed to aggregate results: {e}")
    
    def _filter_results(self, results: List[ComputationResult], 
                       request: AggregationRequest) -> List[ComputationResult]:
        """Filter results based on request criteria."""
        filtered = []
        
        for result in results:
            # Check if party is in the request
            if request.party_ids and result.party_id not in request.party_ids:
                continue
            
            # Check quality threshold
            if result.quality_score < request.quality_threshold:
                continue
            
            # Check confidence threshold
            if result.confidence < request.confidence_threshold:
                continue
            
            filtered.append(result)
        
        return filtered
    
    def _calculate_aggregate_quality(self, results: List[ComputationResult],
                                   request: AggregationRequest) -> float:
        """Calculate aggregate quality score."""
        if not results:
            return 0.0
        
        if self.quality_weights and request.weights:
            # Weighted average
            total_weight = 0
            weighted_sum = 0
            for result in results:
                weight = request.weights.get(result.party_id, 1.0)
                weighted_sum += result.quality_score * weight
                total_weight += weight
            return weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            # Simple average
            return sum(r.quality_score for r in results) / len(results)
    
    def _calculate_aggregate_confidence(self, results: List[ComputationResult],
                                      request: AggregationRequest) -> float:
        """Calculate aggregate confidence score."""
        if not results:
            return 0.0
        
        if self.confidence_weights and request.weights:
            # Weighted average
            total_weight = 0
            weighted_sum = 0
            for result in results:
                weight = request.weights.get(result.party_id, 1.0)
                weighted_sum += result.confidence * weight
                total_weight += weight
            return weighted_sum / total_weight if total_weight > 0 else 0.0
        else:
            # Simple average
            return sum(r.confidence for r in results) / len(results)
    
    def _aggregate_sum(self, results: List[ComputationResult], 
                      request: AggregationRequest) -> Union[float, List, np.ndarray]:
        """Aggregate using sum."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            return sum(values)
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            return np.sum(values, axis=0).tolist()
        else:
            raise AggregatorError("Sum aggregation requires numeric values")
    
    def _aggregate_mean(self, results: List[ComputationResult], 
                       request: AggregationRequest) -> Union[float, List]:
        """Aggregate using mean."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            if request.weights:
                # Weighted mean
                total_weight = 0
                weighted_sum = 0
                for result in results:
                    weight = request.weights.get(result.party_id, 1.0)
                    weighted_sum += result.data * weight
                    total_weight += weight
                return weighted_sum / total_weight if total_weight > 0 else 0.0
            else:
                return statistics.mean(values)
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            return np.mean(values, axis=0).tolist()
        else:
            raise AggregatorError("Mean aggregation requires numeric values")
    
    def _aggregate_median(self, results: List[ComputationResult], 
                         request: AggregationRequest) -> float:
        """Aggregate using median."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            return statistics.median(values)
        else:
            raise AggregatorError("Median aggregation requires numeric scalar values")
    
    def _aggregate_count(self, results: List[ComputationResult], 
                        request: AggregationRequest) -> int:
        """Aggregate using count."""
        return len(results)
    
    def _aggregate_min(self, results: List[ComputationResult], 
                      request: AggregationRequest) -> Union[float, List]:
        """Aggregate using minimum."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            return min(values)
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            return np.min(values, axis=0).tolist()
        else:
            raise AggregatorError("Min aggregation requires numeric values")
    
    def _aggregate_max(self, results: List[ComputationResult], 
                      request: AggregationRequest) -> Union[float, List]:
        """Aggregate using maximum."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            return max(values)
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            return np.max(values, axis=0).tolist()
        else:
            raise AggregatorError("Max aggregation requires numeric values")
    
    def _aggregate_std(self, results: List[ComputationResult], 
                      request: AggregationRequest) -> Union[float, List]:
        """Aggregate using standard deviation."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            return statistics.stdev(values) if len(values) > 1 else 0.0
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            return np.std(values, axis=0).tolist()
        else:
            raise AggregatorError("Std aggregation requires numeric values")
    
    def _aggregate_var(self, results: List[ComputationResult], 
                      request: AggregationRequest) -> Union[float, List]:
        """Aggregate using variance."""
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            return statistics.variance(values) if len(values) > 1 else 0.0
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            return np.var(values, axis=0).tolist()
        else:
            raise AggregatorError("Variance aggregation requires numeric values")
    
    def _aggregate_percentile(self, results: List[ComputationResult], 
                            request: AggregationRequest) -> float:
        """Aggregate using percentile."""
        values = [r.data for r in results]
        percentile = request.parameters.get('percentile', 50)
        
        if all(isinstance(v, (int, float)) for v in values):
            return np.percentile(values, percentile)
        else:
            raise AggregatorError("Percentile aggregation requires numeric scalar values")
    
    def _aggregate_histogram(self, results: List[ComputationResult], 
                           request: AggregationRequest) -> Dict[str, List]:
        """Aggregate using histogram."""
        values = [r.data for r in results]
        bins = request.parameters.get('bins', 10)
        
        if all(isinstance(v, (int, float)) for v in values):
            hist, bin_edges = np.histogram(values, bins=bins)
            return {
                'counts': hist.tolist(),
                'bin_edges': bin_edges.tolist()
            }
        else:
            raise AggregatorError("Histogram aggregation requires numeric values")
    
    def _aggregate_weighted_mean(self, results: List[ComputationResult], 
                               request: AggregationRequest) -> Union[float, List]:
        """Aggregate using weighted mean."""
        if not request.weights:
            raise AggregatorError("Weighted mean requires weights")
        
        values = [r.data for r in results]
        
        if all(isinstance(v, (int, float)) for v in values):
            total_weight = 0
            weighted_sum = 0
            for result in results:
                weight = request.weights.get(result.party_id, 1.0)
                weighted_sum += result.data * weight
                total_weight += weight
            return weighted_sum / total_weight if total_weight > 0 else 0.0
        elif all(isinstance(v, (list, np.ndarray)) for v in values):
            weights = [request.weights.get(r.party_id, 1.0) for r in results]
            return np.average(values, weights=weights, axis=0).tolist()
        else:
            raise AggregatorError("Weighted mean aggregation requires numeric values")
    
    def get_aggregated_result(self, request_id: str) -> Optional[AggregatedResult]:
        """Get an aggregated result by request ID."""
        return self.aggregated_results.get(request_id)
    
    def get_computation_results(self, computation_id: str) -> List[ComputationResult]:
        """Get all results for a computation."""
        return self.results_cache.get(computation_id, [])
    
    def clear_results(self, computation_id: str):
        """Clear results for a computation."""
        if computation_id in self.results_cache:
            del self.results_cache[computation_id]
            logger.info(f"Cleared results for computation {computation_id}")
    
    def clear_aggregated_results(self, request_id: str):
        """Clear aggregated results for a request."""
        if request_id in self.aggregated_results:
            del self.aggregated_results[request_id]
            logger.info(f"Cleared aggregated results for request {request_id}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics."""
        return {
            'total_computations': len(self.results_cache),
            'total_results': sum(len(results) for results in self.results_cache.values()),
            'total_aggregated_results': len(self.aggregated_results),
            'computations_by_result_count': {
                comp_id: len(results) for comp_id, results in self.results_cache.items()
            }
        }
    
    def export_results(self, computation_id: str, format: str = 'json') -> str:
        """Export results for a computation."""
        results = self.get_computation_results(computation_id)
        
        if format == 'json':
            return json.dumps([r.to_dict() for r in results], indent=2)
        elif format == 'csv':
            # Convert to pandas DataFrame and export as CSV
            data = []
            for result in results:
                row = {
                    'party_id': result.party_id,
                    'computation_id': result.computation_id,
                    'result_type': result.result_type.value,
                    'timestamp': result.timestamp,
                    'quality_score': result.quality_score,
                    'confidence': result.confidence,
                    'data': json.dumps(result.data)
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        else:
            raise AggregatorError(f"Unsupported export format: {format}")
    
    def validate_results(self, computation_id: str) -> Dict[str, Any]:
        """Validate results for a computation."""
        results = self.get_computation_results(computation_id)
        
        if not results:
            return {'valid': False, 'error': 'No results found'}
        
        # Check result consistency
        result_types = set(r.result_type for r in results)
        if len(result_types) > 1:
            return {'valid': False, 'error': 'Inconsistent result types'}
        
        # Check data format consistency
        first_result = results[0]
        for result in results[1:]:
            if type(result.data) != type(first_result.data):
                return {'valid': False, 'error': 'Inconsistent data formats'}
        
        return {
            'valid': True,
            'num_results': len(results),
            'result_type': first_result.result_type.value,
            'average_quality': sum(r.quality_score for r in results) / len(results),
            'average_confidence': sum(r.confidence for r in results) / len(results)
        }