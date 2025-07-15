"""
Statistical Analysis Module

Provides privacy-preserving statistical analysis capabilities for multi-party computation
including descriptive statistics, hypothesis testing, and correlation analysis.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatisticsError(Exception):
    """Custom exception for statistics errors."""
    pass

class StatisticType(Enum):
    """Types of statistical analyses."""
    DESCRIPTIVE = "descriptive"
    CORRELATION = "correlation"
    HYPOTHESIS_TEST = "hypothesis_test"
    DISTRIBUTION = "distribution"
    REGRESSION = "regression"

@dataclass
class StatisticalResult:
    """Container for statistical analysis results."""
    analysis_type: StatisticType
    statistic_name: str
    value: Union[float, np.ndarray, Dict[str, Any]]
    confidence_interval: Optional[Tuple[float, float]] = None
    p_value: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            'analysis_type': self.analysis_type.value,
            'statistic_name': self.statistic_name,
            'value': self.value,
            'confidence_interval': self.confidence_interval,
            'p_value': self.p_value,
            'metadata': self.metadata
        }
        
        # Convert numpy arrays to lists for JSON serialization
        if isinstance(self.value, np.ndarray):
            result['value'] = self.value.tolist()
        
        return result

class SecureStatistic(ABC):
    """Abstract base class for secure statistical computations."""
    
    @abstractmethod
    def compute(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute the statistic on multi-party data."""
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data for the statistic."""
        pass
    
    @abstractmethod
    def get_mpc_program(self) -> str:
        """Get the MPC program code for computing this statistic."""
        pass

class SecureMean(SecureStatistic):
    """Secure computation of mean across multiple parties."""
    
    def __init__(self, column_indices: Optional[List[int]] = None):
        self.column_indices = column_indices
    
    def compute(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute secure mean."""
        try:
            # This would normally interface with MPC computation
            # For now, we'll implement a placeholder
            total_sum = 0
            total_count = 0
            
            for party_id, party_data in data.items():
                if isinstance(party_data, np.ndarray):
                    if self.column_indices:
                        party_data = party_data[:, self.column_indices]
                    
                    total_sum += np.sum(party_data, axis=0)
                    total_count += len(party_data)
            
            mean_value = total_sum / total_count if total_count > 0 else 0
            
            return StatisticalResult(
                analysis_type=StatisticType.DESCRIPTIVE,
                statistic_name="mean",
                value=mean_value,
                metadata={
                    'total_samples': total_count,
                    'parties': len(data),
                    'columns': self.column_indices
                }
            )
            
        except Exception as e:
            logger.error(f"Error computing secure mean: {e}")
            raise StatisticsError(f"Failed to compute secure mean: {e}")
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for mean computation."""
        if not data:
            return False
        
        for party_id, party_data in data.items():
            if not isinstance(party_data, np.ndarray):
                return False
            if len(party_data) == 0:
                return False
        
        return True
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure mean computation."""
        return """
# Secure Mean Computation
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Input data from all parties
n_parties = len(program.args)
party_data = {}

for i in range(n_parties):
    party_data[i] = sfix.Array(data_sizes[i])
    @for_range(data_sizes[i])
    def _(j):
        party_data[i][j] = sfix.get_input_from(i)

# Compute global sum and count
global_sum = sfix(0)
global_count = sint(0)

for i in range(n_parties):
    party_sum = sum(party_data[i])
    global_sum += party_sum
    global_count += len(party_data[i])

# Compute mean
mean_result = global_sum / global_count

print_ln('Secure Mean: %s', mean_result.reveal())
"""

class SecureVariance(SecureStatistic):
    """Secure computation of variance across multiple parties."""
    
    def __init__(self, column_indices: Optional[List[int]] = None, ddof: int = 1):
        self.column_indices = column_indices
        self.ddof = ddof  # Delta degrees of freedom
    
    def compute(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute secure variance."""
        try:
            # First compute the mean
            mean_computer = SecureMean(self.column_indices)
            mean_result = mean_computer.compute(data)
            mean_value = mean_result.value
            
            # Then compute variance
            total_squared_deviations = 0
            total_count = 0
            
            for party_id, party_data in data.items():
                if isinstance(party_data, np.ndarray):
                    if self.column_indices:
                        party_data = party_data[:, self.column_indices]
                    
                    squared_deviations = np.sum((party_data - mean_value) ** 2, axis=0)
                    total_squared_deviations += squared_deviations
                    total_count += len(party_data)
            
            variance_value = total_squared_deviations / (total_count - self.ddof) if total_count > self.ddof else 0
            
            return StatisticalResult(
                analysis_type=StatisticType.DESCRIPTIVE,
                statistic_name="variance",
                value=variance_value,
                metadata={
                    'total_samples': total_count,
                    'parties': len(data),
                    'columns': self.column_indices,
                    'ddof': self.ddof
                }
            )
            
        except Exception as e:
            logger.error(f"Error computing secure variance: {e}")
            raise StatisticsError(f"Failed to compute secure variance: {e}")
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for variance computation."""
        return SecureMean().validate_input(data)
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure variance computation."""
        return """
# Secure Variance Computation
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Input data from all parties
n_parties = len(program.args)
party_data = {}

for i in range(n_parties):
    party_data[i] = sfix.Array(data_sizes[i])
    @for_range(data_sizes[i])
    def _(j):
        party_data[i][j] = sfix.get_input_from(i)

# Compute global mean first
global_sum = sfix(0)
global_count = sint(0)

for i in range(n_parties):
    party_sum = sum(party_data[i])
    global_sum += party_sum
    global_count += len(party_data[i])

mean_result = global_sum / global_count

# Compute sum of squared deviations
sum_squared_deviations = sfix(0)

for i in range(n_parties):
    @for_range(len(party_data[i]))
    def _(j):
        deviation = party_data[i][j] - mean_result
        sum_squared_deviations += deviation * deviation

# Compute variance
variance_result = sum_squared_deviations / (global_count - 1)

print_ln('Secure Variance: %s', variance_result.reveal())
"""

class SecureCorrelation(SecureStatistic):
    """Secure computation of correlation between variables."""
    
    def __init__(self, column_pairs: List[Tuple[int, int]]):
        self.column_pairs = column_pairs
    
    def compute(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute secure correlation."""
        try:
            correlations = {}
            
            for col1, col2 in self.column_pairs:
                # Extract columns from all parties
                x_values = []
                y_values = []
                
                for party_id, party_data in data.items():
                    if isinstance(party_data, np.ndarray):
                        x_values.extend(party_data[:, col1])
                        y_values.extend(party_data[:, col2])
                
                # Compute correlation
                if len(x_values) > 1:
                    correlation = np.corrcoef(x_values, y_values)[0, 1]
                    correlations[f"col_{col1}_col_{col2}"] = correlation
            
            return StatisticalResult(
                analysis_type=StatisticType.CORRELATION,
                statistic_name="pearson_correlation",
                value=correlations,
                metadata={
                    'column_pairs': self.column_pairs,
                    'parties': len(data)
                }
            )
            
        except Exception as e:
            logger.error(f"Error computing secure correlation: {e}")
            raise StatisticsError(f"Failed to compute secure correlation: {e}")
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for correlation computation."""
        if not data:
            return False
        
        for party_id, party_data in data.items():
            if not isinstance(party_data, np.ndarray):
                return False
            if len(party_data) == 0:
                return False
            
            # Check if all required columns exist
            for col1, col2 in self.column_pairs:
                if col1 >= party_data.shape[1] or col2 >= party_data.shape[1]:
                    return False
        
        return True
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure correlation computation."""
        return """
# Secure Correlation Computation
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Input data from all parties
n_parties = len(program.args)
party_data = {}

for i in range(n_parties):
    party_data[i] = sfix.Matrix(data_sizes[i], n_features)
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            party_data[i][j][k] = sfix.get_input_from(i)

# Compute correlation for specified column pairs
for col1, col2 in column_pairs:
    # Collect all values for both columns
    x_values = sfix.Array(total_samples)
    y_values = sfix.Array(total_samples)
    
    sample_idx = 0
    for i in range(n_parties):
        @for_range(data_sizes[i])
        def _(j):
            x_values[sample_idx] = party_data[i][j][col1]
            y_values[sample_idx] = party_data[i][j][col2]
            sample_idx += 1
    
    # Compute means
    x_mean = sum(x_values) / total_samples
    y_mean = sum(y_values) / total_samples
    
    # Compute correlation components
    numerator = sfix(0)
    x_variance = sfix(0)
    y_variance = sfix(0)
    
    @for_range(total_samples)
    def _(i):
        x_dev = x_values[i] - x_mean
        y_dev = y_values[i] - y_mean
        numerator += x_dev * y_dev
        x_variance += x_dev * x_dev
        y_variance += y_dev * y_dev
    
    # Compute correlation coefficient
    correlation = numerator / (x_variance * y_variance).sqrt()
    
    print_ln('Correlation between columns %s and %s: %s', col1, col2, correlation.reveal())
"""

class SecureHypothesisTest(SecureStatistic):
    """Secure hypothesis testing."""
    
    def __init__(self, test_type: str, alpha: float = 0.05):
        self.test_type = test_type
        self.alpha = alpha
    
    def compute(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute secure hypothesis test."""
        try:
            if self.test_type == "t_test":
                return self._compute_t_test(data)
            elif self.test_type == "chi_square":
                return self._compute_chi_square_test(data)
            else:
                raise StatisticsError(f"Unsupported test type: {self.test_type}")
                
        except Exception as e:
            logger.error(f"Error computing hypothesis test: {e}")
            raise StatisticsError(f"Failed to compute hypothesis test: {e}")
    
    def _compute_t_test(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute t-test."""
        # Simplified t-test implementation
        all_values = []
        for party_id, party_data in data.items():
            if isinstance(party_data, np.ndarray):
                all_values.extend(party_data.flatten())
        
        if len(all_values) < 2:
            raise StatisticsError("Insufficient data for t-test")
        
        # One-sample t-test against mean = 0
        sample_mean = np.mean(all_values)
        sample_std = np.std(all_values, ddof=1)
        n = len(all_values)
        
        t_statistic = sample_mean / (sample_std / np.sqrt(n))
        
        # Simplified p-value calculation (would need proper implementation)
        p_value = 2 * (1 - abs(t_statistic) / 10)  # Placeholder
        
        return StatisticalResult(
            analysis_type=StatisticType.HYPOTHESIS_TEST,
            statistic_name="t_test",
            value=t_statistic,
            p_value=p_value,
            metadata={
                'sample_size': n,
                'sample_mean': sample_mean,
                'sample_std': sample_std,
                'alpha': self.alpha
            }
        )
    
    def _compute_chi_square_test(self, data: Dict[str, Any]) -> StatisticalResult:
        """Compute chi-square test."""
        # Placeholder implementation
        return StatisticalResult(
            analysis_type=StatisticType.HYPOTHESIS_TEST,
            statistic_name="chi_square",
            value=0.0,
            p_value=0.5,
            metadata={'alpha': self.alpha}
        )
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for hypothesis test."""
        return SecureMean().validate_input(data)
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure hypothesis test."""
        return """
# Secure T-Test Computation
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Input data from all parties
n_parties = len(program.args)
party_data = {}

for i in range(n_parties):
    party_data[i] = sfix.Array(data_sizes[i])
    @for_range(data_sizes[i])
    def _(j):
        party_data[i][j] = sfix.get_input_from(i)

# Compute global statistics
global_sum = sfix(0)
global_count = sint(0)

for i in range(n_parties):
    party_sum = sum(party_data[i])
    global_sum += party_sum
    global_count += len(party_data[i])

sample_mean = global_sum / global_count

# Compute sum of squared deviations
sum_squared_deviations = sfix(0)

for i in range(n_parties):
    @for_range(len(party_data[i]))
    def _(j):
        deviation = party_data[i][j] - sample_mean
        sum_squared_deviations += deviation * deviation

# Compute standard error
sample_variance = sum_squared_deviations / (global_count - 1)
standard_error = (sample_variance / global_count).sqrt()

# Compute t-statistic (testing against mean = 0)
t_statistic = sample_mean / standard_error

print_ln('T-Statistic: %s', t_statistic.reveal())
"""

class StatisticalAnalyzer:
    """Main statistical analyzer orchestrating secure computations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize statistical analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.statistics = {}
        self.results = {}
        
        # Initialize available statistics
        self._initialize_statistics()
    
    def _initialize_statistics(self):
        """Initialize available statistical computations."""
        self.statistics = {
            'mean': SecureMean,
            'variance': SecureVariance,
            'correlation': SecureCorrelation,
            'hypothesis_test': SecureHypothesisTest
        }
    
    def compute_descriptive_statistics(self, data: Dict[str, Any], 
                                     statistics: List[str] = None) -> Dict[str, StatisticalResult]:
        """
        Compute descriptive statistics.
        
        Args:
            data: Multi-party data
            statistics: List of statistics to compute
            
        Returns:
            Dictionary of statistical results
        """
        try:
            if statistics is None:
                statistics = ['mean', 'variance']
            
            results = {}
            
            for stat_name in statistics:
                if stat_name in self.statistics:
                    if stat_name == 'mean':
                        computer = SecureMean()
                    elif stat_name == 'variance':
                        computer = SecureVariance()
                    else:
                        continue
                    
                    if computer.validate_input(data):
                        result = computer.compute(data)
                        results[stat_name] = result
                        logger.info(f"Computed {stat_name} successfully")
                    else:
                        logger.warning(f"Invalid input for {stat_name}")
                        
            return results
            
        except Exception as e:
            logger.error(f"Error computing descriptive statistics: {e}")
            raise StatisticsError(f"Failed to compute descriptive statistics: {e}")
    
    def compute_correlation_matrix(self, data: Dict[str, Any], 
                                 columns: List[int] = None) -> StatisticalResult:
        """
        Compute correlation matrix.
        
        Args:
            data: Multi-party data
            columns: List of column indices to include
            
        Returns:
            Correlation matrix result
        """
        try:
            # Determine columns to analyze
            if columns is None:
                # Infer from first party's data
                first_party_data = next(iter(data.values()))
                if isinstance(first_party_data, np.ndarray):
                    columns = list(range(first_party_data.shape[1]))
                else:
                    raise StatisticsError("Cannot infer columns from data")
            
            # Generate all column pairs
            column_pairs = []
            for i in range(len(columns)):
                for j in range(i + 1, len(columns)):
                    column_pairs.append((columns[i], columns[j]))
            
            # Compute correlations
            correlation_computer = SecureCorrelation(column_pairs)
            if correlation_computer.validate_input(data):
                result = correlation_computer.compute(data)
                logger.info("Computed correlation matrix successfully")
                return result
            else:
                raise StatisticsError("Invalid input for correlation computation")
                
        except Exception as e:
            logger.error(f"Error computing correlation matrix: {e}")
            raise StatisticsError(f"Failed to compute correlation matrix: {e}")
    
    def perform_hypothesis_test(self, data: Dict[str, Any], 
                              test_type: str, alpha: float = 0.05) -> StatisticalResult:
        """
        Perform hypothesis test.
        
        Args:
            data: Multi-party data
            test_type: Type of hypothesis test
            alpha: Significance level
            
        Returns:
            Hypothesis test result
        """
        try:
            test_computer = SecureHypothesisTest(test_type, alpha)
            
            if test_computer.validate_input(data):
                result = test_computer.compute(data)
                logger.info(f"Performed {test_type} test successfully")
                return result
            else:
                raise StatisticsError(f"Invalid input for {test_type} test")
                
        except Exception as e:
            logger.error(f"Error performing hypothesis test: {e}")
            raise StatisticsError(f"Failed to perform hypothesis test: {e}")
    
    def generate_statistical_report(self, data: Dict[str, Any], 
                                  include_tests: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive statistical report.
        
        Args:
            data: Multi-party data
            include_tests: Whether to include hypothesis tests
            
        Returns:
            Comprehensive statistical report
        """
        try:
            report = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'data_summary': self._get_data_summary(data),
                'descriptive_statistics': {},
                'correlation_analysis': {},
                'hypothesis_tests': {} if include_tests else None
            }
            
            # Compute descriptive statistics
            descriptive_stats = self.compute_descriptive_statistics(data)
            for stat_name, result in descriptive_stats.items():
                report['descriptive_statistics'][stat_name] = result.to_dict()
            
            # Compute correlation matrix
            try:
                correlation_result = self.compute_correlation_matrix(data)
                report['correlation_analysis'] = correlation_result.to_dict()
            except Exception as e:
                logger.warning(f"Could not compute correlation matrix: {e}")
                report['correlation_analysis'] = {'error': str(e)}
            
            # Perform hypothesis tests
            if include_tests:
                try:
                    t_test_result = self.perform_hypothesis_test(data, 't_test')
                    report['hypothesis_tests']['t_test'] = t_test_result.to_dict()
                except Exception as e:
                    logger.warning(f"Could not perform t-test: {e}")
                    report['hypothesis_tests']['t_test'] = {'error': str(e)}
            
            logger.info("Generated statistical report successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating statistical report: {e}")
            raise StatisticsError(f"Failed to generate statistical report: {e}")
    
    def _get_data_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get summary of input data."""
        summary = {
            'total_parties': len(data),
            'party_details': {},
            'total_samples': 0
        }
        
        for party_id, party_data in data.items():
            if isinstance(party_data, np.ndarray):
                summary['party_details'][party_id] = {
                    'samples': len(party_data),
                    'features': party_data.shape[1] if len(party_data.shape) > 1 else 1,
                    'data_type': str(party_data.dtype)
                }
                summary['total_samples'] += len(party_data)
        
        return summary
    
    def export_results(self, filepath: str, format: str = 'json'):
        """Export analysis results to file."""
        try:
            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(self.results, f, indent=2, default=str)
            else:
                raise StatisticsError(f"Unsupported export format: {format}")
            
            logger.info(f"Exported results to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise StatisticsError(f"Failed to export results: {e}")
    
    def get_mpc_program_template(self, analysis_type: str) -> str:
        """Get MPC program template for specific analysis."""
        if analysis_type in self.statistics:
            stat_class = self.statistics[analysis_type]
            return stat_class().get_mpc_program()
        else:
            raise StatisticsError(f"No MPC program available for {analysis_type}")
    
    def validate_analysis_request(self, analysis_request: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate analysis request."""
        try:
            required_fields = ['analysis_type', 'data_sources', 'parameters']
            
            for field in required_fields:
                if field not in analysis_request:
                    return False, f"Missing required field: {field}"
            
            analysis_type = analysis_request['analysis_type']
            if analysis_type not in self.statistics:
                return False, f"Unsupported analysis type: {analysis_type}"
            
            return True, "Valid analysis request"
            
        except Exception as e:
            return False, f"Error validating request: {e}"