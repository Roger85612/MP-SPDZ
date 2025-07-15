"""
Privacy Filter Module

Handles privacy filtering and protection of sensitive results before they are
shared, including differential privacy, k-anonymity, and other privacy mechanisms.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import random
import math
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PrivacyFilterError(Exception):
    """Custom exception for privacy filter errors."""
    pass

class PrivacyMechanism(Enum):
    """Types of privacy mechanisms."""
    DIFFERENTIAL_PRIVACY = "differential_privacy"
    K_ANONYMITY = "k_anonymity"
    L_DIVERSITY = "l_diversity"
    T_CLOSENESS = "t_closeness"
    NOISE_ADDITION = "noise_addition"
    SUPPRESSION = "suppression"
    GENERALIZATION = "generalization"
    ROUNDING = "rounding"
    THRESHOLD_FILTERING = "threshold_filtering"

class NoiseType(Enum):
    """Types of noise for differential privacy."""
    LAPLACE = "laplace"
    GAUSSIAN = "gaussian"
    EXPONENTIAL = "exponential"

@dataclass
class PrivacyBudget:
    """Represents a privacy budget for differential privacy."""
    epsilon: float
    delta: float = 0.0
    consumed_epsilon: float = 0.0
    consumed_delta: float = 0.0
    
    def is_exhausted(self) -> bool:
        """Check if privacy budget is exhausted."""
        return (self.consumed_epsilon >= self.epsilon or 
                self.consumed_delta >= self.delta)
    
    def consume(self, epsilon: float, delta: float = 0.0) -> bool:
        """Consume privacy budget."""
        if self.consumed_epsilon + epsilon > self.epsilon:
            return False
        if self.consumed_delta + delta > self.delta:
            return False
        
        self.consumed_epsilon += epsilon
        self.consumed_delta += delta
        return True
    
    def remaining(self) -> Tuple[float, float]:
        """Get remaining privacy budget."""
        return (self.epsilon - self.consumed_epsilon, 
                self.delta - self.consumed_delta)

@dataclass
class PrivacyPolicy:
    """Represents a privacy policy for result filtering."""
    mechanism: PrivacyMechanism
    parameters: Dict[str, Any]
    applicable_result_types: List[str]
    minimum_group_size: int = 1
    maximum_precision: Optional[int] = None
    suppress_small_counts: bool = True
    small_count_threshold: int = 5

class DifferentialPrivacy:
    """Implements differential privacy mechanisms."""
    
    def __init__(self, epsilon: float, delta: float = 0.0):
        self.epsilon = epsilon
        self.delta = delta
        self.budget = PrivacyBudget(epsilon, delta)
    
    def add_laplace_noise(self, value: Union[float, np.ndarray], 
                         sensitivity: float, epsilon: float = None) -> Union[float, np.ndarray]:
        """Add Laplace noise for differential privacy."""
        if epsilon is None:
            epsilon = self.epsilon
        
        if not self.budget.consume(epsilon):
            raise PrivacyFilterError("Privacy budget exhausted")
        
        scale = sensitivity / epsilon
        
        if isinstance(value, np.ndarray):
            noise = np.random.laplace(0, scale, value.shape)
            return value + noise
        else:
            noise = np.random.laplace(0, scale)
            return value + noise
    
    def add_gaussian_noise(self, value: Union[float, np.ndarray], 
                          sensitivity: float, epsilon: float = None,
                          delta: float = None) -> Union[float, np.ndarray]:
        """Add Gaussian noise for differential privacy."""
        if epsilon is None:
            epsilon = self.epsilon
        if delta is None:
            delta = self.delta
        
        if not self.budget.consume(epsilon, delta):
            raise PrivacyFilterError("Privacy budget exhausted")
        
        # Calculate standard deviation for Gaussian mechanism
        if delta <= 0:
            raise PrivacyFilterError("Delta must be positive for Gaussian mechanism")
        
        sigma = sensitivity * math.sqrt(2 * math.log(1.25 / delta)) / epsilon
        
        if isinstance(value, np.ndarray):
            noise = np.random.normal(0, sigma, value.shape)
            return value + noise
        else:
            noise = np.random.normal(0, sigma)
            return value + noise
    
    def exponential_mechanism(self, candidates: List[Any], 
                            utility_function: callable,
                            sensitivity: float, epsilon: float = None) -> Any:
        """Implement exponential mechanism for differential privacy."""
        if epsilon is None:
            epsilon = self.epsilon
        
        if not self.budget.consume(epsilon):
            raise PrivacyFilterError("Privacy budget exhausted")
        
        # Calculate utilities
        utilities = [utility_function(candidate) for candidate in candidates]
        
        # Calculate probabilities
        max_utility = max(utilities)
        exp_utilities = [math.exp(epsilon * (u - max_utility) / (2 * sensitivity)) 
                        for u in utilities]
        
        total_prob = sum(exp_utilities)
        probabilities = [exp_util / total_prob for exp_util in exp_utilities]
        
        # Sample according to probabilities
        rand_val = random.random()
        cumulative_prob = 0
        
        for i, prob in enumerate(probabilities):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                return candidates[i]
        
        return candidates[-1]  # Fallback

class KAnonymity:
    """Implements k-anonymity privacy mechanism."""
    
    def __init__(self, k: int):
        self.k = k
    
    def apply_k_anonymity(self, data: pd.DataFrame, 
                         quasi_identifiers: List[str]) -> pd.DataFrame:
        """Apply k-anonymity to a dataset."""
        if self.k <= 1:
            return data
        
        # Group by quasi-identifiers
        grouped = data.groupby(quasi_identifiers)
        
        # Filter out groups with less than k members
        valid_groups = []
        for name, group in grouped:
            if len(group) >= self.k:
                valid_groups.append(group)
        
        if not valid_groups:
            raise PrivacyFilterError(f"No groups meet k-anonymity requirement (k={self.k})")
        
        # Combine valid groups
        result = pd.concat(valid_groups, ignore_index=True)
        
        logger.info(f"Applied k-anonymity (k={self.k}), retained {len(result)} out of {len(data)} records")
        return result
    
    def generalize_column(self, data: pd.Series, 
                         generalization_levels: Dict[str, Any]) -> pd.Series:
        """Generalize a column for k-anonymity."""
        if data.dtype in ['int64', 'float64']:
            # Numeric generalization
            bins = generalization_levels.get('bins', 10)
            return pd.cut(data, bins=bins, include_lowest=True)
        else:
            # Categorical generalization
            mapping = generalization_levels.get('mapping', {})
            return data.map(mapping).fillna(data)

class LDiversity:
    """Implements l-diversity privacy mechanism."""
    
    def __init__(self, l: int):
        self.l = l
    
    def apply_l_diversity(self, data: pd.DataFrame, 
                         quasi_identifiers: List[str],
                         sensitive_attribute: str) -> pd.DataFrame:
        """Apply l-diversity to a dataset."""
        if self.l <= 1:
            return data
        
        # Group by quasi-identifiers
        grouped = data.groupby(quasi_identifiers)
        
        # Filter groups that meet l-diversity requirement
        valid_groups = []
        for name, group in grouped:
            unique_sensitive = group[sensitive_attribute].nunique()
            if unique_sensitive >= self.l:
                valid_groups.append(group)
        
        if not valid_groups:
            raise PrivacyFilterError(f"No groups meet l-diversity requirement (l={self.l})")
        
        # Combine valid groups
        result = pd.concat(valid_groups, ignore_index=True)
        
        logger.info(f"Applied l-diversity (l={self.l}), retained {len(result)} out of {len(data)} records")
        return result

class PrivacyFilter:
    """Main privacy filter class that applies various privacy mechanisms."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.privacy_policies = {}
        self.differential_privacy = None
        self.k_anonymity = None
        self.l_diversity = None
        
        # Initialize privacy mechanisms
        self._initialize_mechanisms()
        
        logger.info("Privacy filter initialized")
    
    def _initialize_mechanisms(self):
        """Initialize privacy mechanisms based on configuration."""
        # Differential Privacy
        if 'differential_privacy' in self.config:
            dp_config = self.config['differential_privacy']
            self.differential_privacy = DifferentialPrivacy(
                epsilon=dp_config.get('epsilon', 1.0),
                delta=dp_config.get('delta', 0.0)
            )
        
        # K-Anonymity
        if 'k_anonymity' in self.config:
            k_config = self.config['k_anonymity']
            self.k_anonymity = KAnonymity(k=k_config.get('k', 2))
        
        # L-Diversity
        if 'l_diversity' in self.config:
            l_config = self.config['l_diversity']
            self.l_diversity = LDiversity(l=l_config.get('l', 2))
    
    def add_privacy_policy(self, policy_id: str, policy: PrivacyPolicy):
        """Add a privacy policy."""
        self.privacy_policies[policy_id] = policy
        logger.info(f"Added privacy policy: {policy_id}")
    
    def filter_result(self, result: Any, result_type: str, 
                     metadata: Dict[str, Any] = None) -> Any:
        """Apply privacy filtering to a result."""
        if metadata is None:
            metadata = {}
        
        # Find applicable privacy policies
        applicable_policies = []
        for policy_id, policy in self.privacy_policies.items():
            if result_type in policy.applicable_result_types:
                applicable_policies.append(policy)
        
        if not applicable_policies:
            logger.warning(f"No privacy policies found for result type: {result_type}")
            return result
        
        # Apply privacy mechanisms
        filtered_result = result
        for policy in applicable_policies:
            filtered_result = self._apply_privacy_mechanism(
                filtered_result, policy, metadata
            )
        
        return filtered_result
    
    def _apply_privacy_mechanism(self, result: Any, policy: PrivacyPolicy,
                               metadata: Dict[str, Any]) -> Any:
        """Apply a specific privacy mechanism."""
        mechanism = policy.mechanism
        parameters = policy.parameters
        
        try:
            if mechanism == PrivacyMechanism.DIFFERENTIAL_PRIVACY:
                return self._apply_differential_privacy(result, parameters, metadata)
            
            elif mechanism == PrivacyMechanism.K_ANONYMITY:
                return self._apply_k_anonymity(result, parameters, metadata)
            
            elif mechanism == PrivacyMechanism.L_DIVERSITY:
                return self._apply_l_diversity(result, parameters, metadata)
            
            elif mechanism == PrivacyMechanism.NOISE_ADDITION:
                return self._apply_noise_addition(result, parameters)
            
            elif mechanism == PrivacyMechanism.SUPPRESSION:
                return self._apply_suppression(result, policy, metadata)
            
            elif mechanism == PrivacyMechanism.GENERALIZATION:
                return self._apply_generalization(result, parameters)
            
            elif mechanism == PrivacyMechanism.ROUNDING:
                return self._apply_rounding(result, parameters)
            
            elif mechanism == PrivacyMechanism.THRESHOLD_FILTERING:
                return self._apply_threshold_filtering(result, parameters)
            
            else:
                logger.warning(f"Unknown privacy mechanism: {mechanism}")
                return result
                
        except Exception as e:
            logger.error(f"Error applying privacy mechanism {mechanism}: {e}")
            raise PrivacyFilterError(f"Failed to apply privacy mechanism: {e}")
    
    def _apply_differential_privacy(self, result: Any, parameters: Dict[str, Any],
                                  metadata: Dict[str, Any]) -> Any:
        """Apply differential privacy."""
        if not self.differential_privacy:
            raise PrivacyFilterError("Differential privacy not configured")
        
        noise_type = parameters.get('noise_type', NoiseType.LAPLACE)
        sensitivity = parameters.get('sensitivity', 1.0)
        epsilon = parameters.get('epsilon')
        delta = parameters.get('delta')
        
        if noise_type == NoiseType.LAPLACE:
            return self.differential_privacy.add_laplace_noise(
                result, sensitivity, epsilon
            )
        elif noise_type == NoiseType.GAUSSIAN:
            return self.differential_privacy.add_gaussian_noise(
                result, sensitivity, epsilon, delta
            )
        else:
            raise PrivacyFilterError(f"Unsupported noise type: {noise_type}")
    
    def _apply_k_anonymity(self, result: Any, parameters: Dict[str, Any],
                          metadata: Dict[str, Any]) -> Any:
        """Apply k-anonymity."""
        if not self.k_anonymity:
            raise PrivacyFilterError("K-anonymity not configured")
        
        if not isinstance(result, pd.DataFrame):
            raise PrivacyFilterError("K-anonymity requires DataFrame input")
        
        quasi_identifiers = parameters.get('quasi_identifiers', [])
        if not quasi_identifiers:
            raise PrivacyFilterError("K-anonymity requires quasi-identifiers")
        
        return self.k_anonymity.apply_k_anonymity(result, quasi_identifiers)
    
    def _apply_l_diversity(self, result: Any, parameters: Dict[str, Any],
                          metadata: Dict[str, Any]) -> Any:
        """Apply l-diversity."""
        if not self.l_diversity:
            raise PrivacyFilterError("L-diversity not configured")
        
        if not isinstance(result, pd.DataFrame):
            raise PrivacyFilterError("L-diversity requires DataFrame input")
        
        quasi_identifiers = parameters.get('quasi_identifiers', [])
        sensitive_attribute = parameters.get('sensitive_attribute')
        
        if not quasi_identifiers or not sensitive_attribute:
            raise PrivacyFilterError("L-diversity requires quasi-identifiers and sensitive attribute")
        
        return self.l_diversity.apply_l_diversity(
            result, quasi_identifiers, sensitive_attribute
        )
    
    def _apply_noise_addition(self, result: Any, parameters: Dict[str, Any]) -> Any:
        """Apply simple noise addition."""
        noise_level = parameters.get('noise_level', 0.1)
        
        if isinstance(result, (int, float)):
            noise = np.random.normal(0, abs(result) * noise_level)
            return result + noise
        elif isinstance(result, np.ndarray):
            noise = np.random.normal(0, np.abs(result) * noise_level)
            return result + noise
        else:
            return result
    
    def _apply_suppression(self, result: Any, policy: PrivacyPolicy,
                          metadata: Dict[str, Any]) -> Any:
        """Apply suppression mechanism."""
        if policy.suppress_small_counts:
            threshold = policy.small_count_threshold
            
            if isinstance(result, (int, float)):
                if result < threshold:
                    return "<suppressed>"
                return result
            elif isinstance(result, dict):
                filtered_result = {}
                for key, value in result.items():
                    if isinstance(value, (int, float)) and value < threshold:
                        filtered_result[key] = "<suppressed>"
                    else:
                        filtered_result[key] = value
                return filtered_result
        
        return result
    
    def _apply_generalization(self, result: Any, parameters: Dict[str, Any]) -> Any:
        """Apply generalization mechanism."""
        if isinstance(result, (int, float)):
            # Numeric generalization
            precision = parameters.get('precision', 0)
            return round(result, precision)
        elif isinstance(result, pd.DataFrame):
            # DataFrame generalization
            generalization_rules = parameters.get('generalization_rules', {})
            generalized_df = result.copy()
            
            for column, rules in generalization_rules.items():
                if column in generalized_df.columns:
                    if generalized_df[column].dtype in ['int64', 'float64']:
                        # Numeric generalization
                        bins = rules.get('bins', 10)
                        generalized_df[column] = pd.cut(
                            generalized_df[column], bins=bins, include_lowest=True
                        )
                    else:
                        # Categorical generalization
                        mapping = rules.get('mapping', {})
                        generalized_df[column] = generalized_df[column].map(mapping).fillna(generalized_df[column])
            
            return generalized_df
        
        return result
    
    def _apply_rounding(self, result: Any, parameters: Dict[str, Any]) -> Any:
        """Apply rounding mechanism."""
        decimals = parameters.get('decimals', 2)
        
        if isinstance(result, (int, float)):
            return round(result, decimals)
        elif isinstance(result, np.ndarray):
            return np.round(result, decimals)
        elif isinstance(result, list):
            return [round(x, decimals) if isinstance(x, (int, float)) else x for x in result]
        
        return result
    
    def _apply_threshold_filtering(self, result: Any, parameters: Dict[str, Any]) -> Any:
        """Apply threshold filtering."""
        min_threshold = parameters.get('min_threshold', 0)
        max_threshold = parameters.get('max_threshold', float('inf'))
        
        if isinstance(result, (int, float)):
            if result < min_threshold or result > max_threshold:
                return None
            return result
        elif isinstance(result, dict):
            filtered_result = {}
            for key, value in result.items():
                if isinstance(value, (int, float)):
                    if min_threshold <= value <= max_threshold:
                        filtered_result[key] = value
                else:
                    filtered_result[key] = value
            return filtered_result
        
        return result
    
    def get_privacy_budget_status(self) -> Dict[str, Any]:
        """Get privacy budget status."""
        if not self.differential_privacy:
            return {'differential_privacy': 'not_configured'}
        
        budget = self.differential_privacy.budget
        remaining_epsilon, remaining_delta = budget.remaining()
        
        return {
            'total_epsilon': budget.epsilon,
            'total_delta': budget.delta,
            'consumed_epsilon': budget.consumed_epsilon,
            'consumed_delta': budget.consumed_delta,
            'remaining_epsilon': remaining_epsilon,
            'remaining_delta': remaining_delta,
            'exhausted': budget.is_exhausted()
        }
    
    def reset_privacy_budget(self):
        """Reset privacy budget."""
        if self.differential_privacy:
            self.differential_privacy.budget.consumed_epsilon = 0.0
            self.differential_privacy.budget.consumed_delta = 0.0
            logger.info("Privacy budget reset")
    
    def validate_privacy_requirements(self, result: Any, result_type: str,
                                    metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate that privacy requirements are met."""
        if metadata is None:
            metadata = {}
        
        validation_result = {
            'valid': True,
            'violations': [],
            'warnings': []
        }
        
        # Check applicable privacy policies
        applicable_policies = []
        for policy_id, policy in self.privacy_policies.items():
            if result_type in policy.applicable_result_types:
                applicable_policies.append((policy_id, policy))
        
        if not applicable_policies:
            validation_result['warnings'].append(
                f"No privacy policies defined for result type: {result_type}"
            )
        
        # Validate each policy
        for policy_id, policy in applicable_policies:
            # Check minimum group size
            if hasattr(result, '__len__') and len(result) < policy.minimum_group_size:
                validation_result['valid'] = False
                validation_result['violations'].append(
                    f"Policy {policy_id}: Result size {len(result)} below minimum {policy.minimum_group_size}"
                )
            
            # Check maximum precision
            if policy.maximum_precision is not None:
                if isinstance(result, float):
                    decimal_places = len(str(result).split('.')[-1])
                    if decimal_places > policy.maximum_precision:
                        validation_result['warnings'].append(
                            f"Policy {policy_id}: Result precision {decimal_places} exceeds maximum {policy.maximum_precision}"
                        )
        
        return validation_result
    
    def get_privacy_statistics(self) -> Dict[str, Any]:
        """Get privacy filter statistics."""
        return {
            'total_policies': len(self.privacy_policies),
            'mechanisms_configured': {
                'differential_privacy': self.differential_privacy is not None,
                'k_anonymity': self.k_anonymity is not None,
                'l_diversity': self.l_diversity is not None
            },
            'privacy_budget_status': self.get_privacy_budget_status()
        }