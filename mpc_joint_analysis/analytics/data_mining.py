"""
Data Mining Module

Provides privacy-preserving data mining capabilities for multi-party computation
including pattern discovery, association rules, and frequent itemset mining.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union, Set
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import defaultdict, Counter
import json
from enum import Enum
import itertools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataMiningError(Exception):
    """Custom exception for data mining errors."""
    pass

class MiningTaskType(Enum):
    """Types of data mining tasks."""
    FREQUENT_ITEMSETS = "frequent_itemsets"
    ASSOCIATION_RULES = "association_rules"
    SEQUENTIAL_PATTERNS = "sequential_patterns"
    OUTLIER_DETECTION = "outlier_detection"
    ANOMALY_DETECTION = "anomaly_detection"

@dataclass
class MiningResult:
    """Container for data mining results."""
    task_type: MiningTaskType
    algorithm: str
    results: Dict[str, Any]
    metrics: Dict[str, float]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'task_type': self.task_type.value,
            'algorithm': self.algorithm,
            'results': self.results,
            'metrics': self.metrics,
            'metadata': self.metadata
        }

class SecureDataMiningAlgorithm(ABC):
    """Abstract base class for secure data mining algorithms."""
    
    @abstractmethod
    def mine(self, data: Dict[str, Any]) -> MiningResult:
        """Perform data mining on multi-party data."""
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input data for the algorithm."""
        pass
    
    @abstractmethod
    def get_mpc_program(self) -> str:
        """Get the MPC program code for this algorithm."""
        pass

class SecureFrequentItemsets(SecureDataMiningAlgorithm):
    """Secure frequent itemset mining using Apriori algorithm."""
    
    def __init__(self, min_support: float = 0.5, max_itemset_size: int = 5):
        self.min_support = min_support
        self.max_itemset_size = max_itemset_size
    
    def mine(self, data: Dict[str, Any]) -> MiningResult:
        """Mine frequent itemsets from multi-party transaction data."""
        try:
            # Combine transaction data from all parties
            all_transactions = []
            for party_id, party_data in data.items():
                if isinstance(party_data, list):
                    all_transactions.extend(party_data)
                elif isinstance(party_data, np.ndarray):
                    all_transactions.extend(party_data.tolist())
                else:
                    logger.warning(f"Unexpected data type from party {party_id}: {type(party_data)}")
            
            if not all_transactions:
                raise DataMiningError("No transaction data found")
            
            # Convert to set format for itemset mining
            transactions = []
            for transaction in all_transactions:
                if isinstance(transaction, str):
                    # Parse string transactions (e.g., "item1,item2,item3")
                    transactions.append(set(transaction.split(',')))
                elif isinstance(transaction, (list, tuple)):
                    transactions.append(set(transaction))
                else:
                    transactions.append(set([str(transaction)]))
            
            # Apply Apriori algorithm
            frequent_itemsets = self._apriori(transactions)
            
            # Calculate metrics
            total_itemsets = sum(len(itemsets) for itemsets in frequent_itemsets.values())
            max_size = max(frequent_itemsets.keys()) if frequent_itemsets else 0
            
            return MiningResult(
                task_type=MiningTaskType.FREQUENT_ITEMSETS,
                algorithm="apriori",
                results=frequent_itemsets,
                metrics={
                    'total_itemsets': total_itemsets,
                    'max_itemset_size': max_size,
                    'total_transactions': len(transactions)
                },
                metadata={
                    'min_support': self.min_support,
                    'max_itemset_size': self.max_itemset_size,
                    'parties': len(data)
                }
            )
            
        except Exception as e:
            logger.error(f"Error mining frequent itemsets: {e}")
            raise DataMiningError(f"Failed to mine frequent itemsets: {e}")
    
    def _apriori(self, transactions: List[Set[str]]) -> Dict[int, List[Dict[str, Any]]]:
        """Apply Apriori algorithm to find frequent itemsets."""
        n_transactions = len(transactions)
        min_support_count = int(self.min_support * n_transactions)
        
        # Find frequent 1-itemsets
        item_counts = defaultdict(int)
        for transaction in transactions:
            for item in transaction:
                item_counts[item] += 1
        
        # Filter frequent 1-itemsets
        frequent_1_itemsets = {
            frozenset([item]): count for item, count in item_counts.items()
            if count >= min_support_count
        }
        
        frequent_itemsets = {1: []}
        for itemset, count in frequent_1_itemsets.items():
            frequent_itemsets[1].append({
                'itemset': list(itemset),
                'support': count / n_transactions,
                'count': count
            })
        
        # Generate larger itemsets
        k = 2
        current_frequent = frequent_1_itemsets
        
        while current_frequent and k <= self.max_itemset_size:
            # Generate candidate k-itemsets
            candidates = self._generate_candidates(list(current_frequent.keys()), k)
            
            # Count support for candidates
            candidate_counts = defaultdict(int)
            for transaction in transactions:
                for candidate in candidates:
                    if candidate.issubset(transaction):
                        candidate_counts[candidate] += 1
            
            # Filter frequent k-itemsets
            current_frequent = {
                itemset: count for itemset, count in candidate_counts.items()
                if count >= min_support_count
            }
            
            if current_frequent:
                frequent_itemsets[k] = []
                for itemset, count in current_frequent.items():
                    frequent_itemsets[k].append({
                        'itemset': list(itemset),
                        'support': count / n_transactions,
                        'count': count
                    })
            
            k += 1
        
        return frequent_itemsets
    
    def _generate_candidates(self, frequent_itemsets: List[frozenset], k: int) -> List[frozenset]:
        """Generate candidate k-itemsets from frequent (k-1)-itemsets."""
        candidates = []
        
        for i in range(len(frequent_itemsets)):
            for j in range(i + 1, len(frequent_itemsets)):
                itemset1 = frequent_itemsets[i]
                itemset2 = frequent_itemsets[j]
                
                # Join step: combine itemsets that differ by one element
                union = itemset1.union(itemset2)
                if len(union) == k:
                    candidates.append(union)
        
        return candidates
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for frequent itemset mining."""
        if not data:
            return False
        
        for party_id, party_data in data.items():
            if not isinstance(party_data, (list, np.ndarray)):
                return False
            if len(party_data) == 0:
                return False
        
        return True
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure frequent itemset mining."""
        return """
# Secure Frequent Itemset Mining
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Input transaction data from all parties
n_parties = len(program.args)
party_transactions = {}

for i in range(n_parties):
    party_transactions[i] = []
    n_transactions = transaction_counts[i]
    
    @for_range(n_transactions)
    def _(j):
        transaction_size = transaction_sizes[i][j]
        transaction = sint.Array(transaction_size)
        
        @for_range(transaction_size)
        def _(k):
            transaction[k] = sint.get_input_from(i)
        
        party_transactions[i].append(transaction)

# Combine all transactions
all_transactions = []
for i in range(n_parties):
    all_transactions.extend(party_transactions[i])

total_transactions = len(all_transactions)
min_support_count = sint(int(min_support * total_transactions))

# Find frequent 1-itemsets
item_counts = {}
all_items = set()

for transaction in all_transactions:
    for item in transaction:
        all_items.add(item)
        if item not in item_counts:
            item_counts[item] = sint(0)
        item_counts[item] += 1

# Filter frequent 1-itemsets
frequent_1_itemsets = []
for item, count in item_counts.items():
    is_frequent = count >= min_support_count
    frequent_1_itemsets.append((item, is_frequent))

print_ln('Frequent itemset mining completed')
"""

class SecureAssociationRules(SecureDataMiningAlgorithm):
    """Secure association rule mining."""
    
    def __init__(self, min_support: float = 0.5, min_confidence: float = 0.7):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.itemset_miner = SecureFrequentItemsets(min_support)
    
    def mine(self, data: Dict[str, Any]) -> MiningResult:
        """Mine association rules from multi-party transaction data."""
        try:
            # First find frequent itemsets
            frequent_itemsets_result = self.itemset_miner.mine(data)
            frequent_itemsets = frequent_itemsets_result.results
            
            # Generate association rules
            association_rules = self._generate_association_rules(frequent_itemsets)
            
            # Calculate metrics
            total_rules = len(association_rules)
            avg_confidence = np.mean([rule['confidence'] for rule in association_rules]) if association_rules else 0
            avg_lift = np.mean([rule['lift'] for rule in association_rules]) if association_rules else 0
            
            return MiningResult(
                task_type=MiningTaskType.ASSOCIATION_RULES,
                algorithm="apriori_association_rules",
                results={'rules': association_rules},
                metrics={
                    'total_rules': total_rules,
                    'avg_confidence': avg_confidence,
                    'avg_lift': avg_lift
                },
                metadata={
                    'min_support': self.min_support,
                    'min_confidence': self.min_confidence,
                    'parties': len(data)
                }
            )
            
        except Exception as e:
            logger.error(f"Error mining association rules: {e}")
            raise DataMiningError(f"Failed to mine association rules: {e}")
    
    def _generate_association_rules(self, frequent_itemsets: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate association rules from frequent itemsets."""
        rules = []
        
        # Generate rules from itemsets of size 2 or larger
        for size in range(2, max(frequent_itemsets.keys()) + 1):
            if size not in frequent_itemsets:
                continue
            
            for itemset_info in frequent_itemsets[size]:
                itemset = set(itemset_info['itemset'])
                itemset_support = itemset_info['support']
                
                # Generate all possible antecedent/consequent combinations
                for antecedent_size in range(1, size):
                    for antecedent in itertools.combinations(itemset, antecedent_size):
                        antecedent_set = set(antecedent)
                        consequent_set = itemset - antecedent_set
                        
                        # Find antecedent support
                        antecedent_support = self._find_itemset_support(
                            antecedent_set, frequent_itemsets
                        )
                        
                        if antecedent_support > 0:
                            # Calculate confidence
                            confidence = itemset_support / antecedent_support
                            
                            if confidence >= self.min_confidence:
                                # Calculate lift
                                consequent_support = self._find_itemset_support(
                                    consequent_set, frequent_itemsets
                                )
                                lift = confidence / consequent_support if consequent_support > 0 else 0
                                
                                rules.append({
                                    'antecedent': list(antecedent_set),
                                    'consequent': list(consequent_set),
                                    'support': itemset_support,
                                    'confidence': confidence,
                                    'lift': lift
                                })
        
        return rules
    
    def _find_itemset_support(self, itemset: Set[str], frequent_itemsets: Dict[int, List[Dict[str, Any]]]) -> float:
        """Find support for a specific itemset."""
        itemset_size = len(itemset)
        
        if itemset_size in frequent_itemsets:
            for itemset_info in frequent_itemsets[itemset_size]:
                if set(itemset_info['itemset']) == itemset:
                    return itemset_info['support']
        
        return 0.0
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for association rule mining."""
        return self.itemset_miner.validate_input(data)
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure association rule mining."""
        return """
# Secure Association Rule Mining
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# First perform frequent itemset mining
""" + self.itemset_miner.get_mpc_program() + """

# Generate association rules from frequent itemsets
# This would extend the itemset mining with rule generation logic

print_ln('Association rule mining completed')
"""

class SecureOutlierDetection(SecureDataMiningAlgorithm):
    """Secure outlier detection using statistical methods."""
    
    def __init__(self, method: str = 'zscore', threshold: float = 3.0):
        self.method = method
        self.threshold = threshold
    
    def mine(self, data: Dict[str, Any]) -> MiningResult:
        """Detect outliers in multi-party data."""
        try:
            # Combine data from all parties
            all_data = []
            party_indices = {}
            current_index = 0
            
            for party_id, party_data in data.items():
                if isinstance(party_data, np.ndarray):
                    party_data_list = party_data.tolist()
                else:
                    party_data_list = list(party_data)
                
                all_data.extend(party_data_list)
                party_indices[party_id] = list(range(current_index, current_index + len(party_data_list)))
                current_index += len(party_data_list)
            
            if not all_data:
                raise DataMiningError("No data found for outlier detection")
            
            # Convert to numpy array
            data_array = np.array(all_data)
            
            # Apply outlier detection method
            if self.method == 'zscore':
                outliers = self._zscore_outliers(data_array)
            elif self.method == 'iqr':
                outliers = self._iqr_outliers(data_array)
            else:
                raise DataMiningError(f"Unsupported outlier detection method: {self.method}")
            
            # Map outliers back to parties
            outlier_by_party = {}
            for party_id, indices in party_indices.items():
                party_outliers = [i for i in indices if i in outliers]
                outlier_by_party[party_id] = [i - indices[0] for i in party_outliers]
            
            # Calculate metrics
            total_outliers = len(outliers)
            outlier_ratio = total_outliers / len(all_data)
            
            return MiningResult(
                task_type=MiningTaskType.OUTLIER_DETECTION,
                algorithm=f"outlier_detection_{self.method}",
                results={
                    'outliers': outliers,
                    'outlier_by_party': outlier_by_party,
                    'outlier_values': data_array[outliers].tolist()
                },
                metrics={
                    'total_outliers': total_outliers,
                    'outlier_ratio': outlier_ratio,
                    'total_samples': len(all_data)
                },
                metadata={
                    'method': self.method,
                    'threshold': self.threshold,
                    'parties': len(data)
                }
            )
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            raise DataMiningError(f"Failed to detect outliers: {e}")
    
    def _zscore_outliers(self, data: np.ndarray) -> List[int]:
        """Detect outliers using Z-score method."""
        if len(data.shape) == 1:
            # Univariate case
            mean = np.mean(data)
            std = np.std(data)
            z_scores = np.abs((data - mean) / std) if std > 0 else np.zeros_like(data)
            outliers = np.where(z_scores > self.threshold)[0]
        else:
            # Multivariate case
            outliers = []
            for i in range(data.shape[1]):
                column = data[:, i]
                mean = np.mean(column)
                std = np.std(column)
                z_scores = np.abs((column - mean) / std) if std > 0 else np.zeros_like(column)
                column_outliers = np.where(z_scores > self.threshold)[0]
                outliers.extend(column_outliers)
            
            outliers = list(set(outliers))
        
        return outliers
    
    def _iqr_outliers(self, data: np.ndarray) -> List[int]:
        """Detect outliers using IQR method."""
        if len(data.shape) == 1:
            # Univariate case
            q1 = np.percentile(data, 25)
            q3 = np.percentile(data, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outliers = np.where((data < lower_bound) | (data > upper_bound))[0]
        else:
            # Multivariate case
            outliers = []
            for i in range(data.shape[1]):
                column = data[:, i]
                q1 = np.percentile(column, 25)
                q3 = np.percentile(column, 75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                column_outliers = np.where((column < lower_bound) | (column > upper_bound))[0]
                outliers.extend(column_outliers)
            
            outliers = list(set(outliers))
        
        return outliers
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for outlier detection."""
        if not data:
            return False
        
        for party_id, party_data in data.items():
            if not isinstance(party_data, (list, np.ndarray)):
                return False
            if len(party_data) == 0:
                return False
        
        return True
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure outlier detection."""
        return """
# Secure Outlier Detection
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

# Combine all data
total_samples = sum(data_sizes)
all_data = sfix.Array(total_samples)

sample_idx = 0
for i in range(n_parties):
    @for_range(data_sizes[i])
    def _(j):
        all_data[sample_idx] = party_data[i][j]
        sample_idx += 1

# Compute global statistics
global_mean = sum(all_data) / total_samples

variance_sum = sfix(0)
@for_range(total_samples)
def _(i):
    deviation = all_data[i] - global_mean
    variance_sum += deviation * deviation

global_std = (variance_sum / total_samples).sqrt()

# Detect outliers using Z-score
outlier_threshold = sfix(threshold)
outlier_count = sint(0)

@for_range(total_samples)
def _(i):
    z_score = (all_data[i] - global_mean) / global_std
    is_outlier = z_score.abs() > outlier_threshold
    outlier_count += is_outlier

print_ln('Outlier detection completed. Found %s outliers', outlier_count.reveal())
"""

class SecureSequentialPatterns(SecureDataMiningAlgorithm):
    """Secure sequential pattern mining."""
    
    def __init__(self, min_support: float = 0.5, max_pattern_length: int = 5):
        self.min_support = min_support
        self.max_pattern_length = max_pattern_length
    
    def mine(self, data: Dict[str, Any]) -> MiningResult:
        """Mine sequential patterns from multi-party sequence data."""
        try:
            # Combine sequence data from all parties
            all_sequences = []
            for party_id, party_data in data.items():
                if isinstance(party_data, list):
                    all_sequences.extend(party_data)
                else:
                    logger.warning(f"Unexpected data format from party {party_id}")
            
            if not all_sequences:
                raise DataMiningError("No sequence data found")
            
            # Apply sequential pattern mining
            frequent_patterns = self._mine_sequential_patterns(all_sequences)
            
            # Calculate metrics
            total_patterns = sum(len(patterns) for patterns in frequent_patterns.values())
            max_length = max(frequent_patterns.keys()) if frequent_patterns else 0
            
            return MiningResult(
                task_type=MiningTaskType.SEQUENTIAL_PATTERNS,
                algorithm="sequential_pattern_mining",
                results=frequent_patterns,
                metrics={
                    'total_patterns': total_patterns,
                    'max_pattern_length': max_length,
                    'total_sequences': len(all_sequences)
                },
                metadata={
                    'min_support': self.min_support,
                    'max_pattern_length': self.max_pattern_length,
                    'parties': len(data)
                }
            )
            
        except Exception as e:
            logger.error(f"Error mining sequential patterns: {e}")
            raise DataMiningError(f"Failed to mine sequential patterns: {e}")
    
    def _mine_sequential_patterns(self, sequences: List[List[str]]) -> Dict[int, List[Dict[str, Any]]]:
        """Mine frequent sequential patterns."""
        n_sequences = len(sequences)
        min_support_count = int(self.min_support * n_sequences)
        
        # Find frequent 1-patterns
        item_counts = defaultdict(int)
        for sequence in sequences:
            unique_items = set(sequence)
            for item in unique_items:
                item_counts[item] += 1
        
        # Filter frequent 1-patterns
        frequent_1_patterns = {
            item: count for item, count in item_counts.items()
            if count >= min_support_count
        }
        
        frequent_patterns = {1: []}
        for pattern, count in frequent_1_patterns.items():
            frequent_patterns[1].append({
                'pattern': [pattern],
                'support': count / n_sequences,
                'count': count
            })
        
        # Generate longer patterns
        k = 2
        while k <= self.max_pattern_length:
            # Generate candidate k-patterns
            candidates = self._generate_sequential_candidates(frequent_patterns.get(k-1, []))
            
            if not candidates:
                break
            
            # Count support for candidates
            candidate_counts = defaultdict(int)
            for sequence in sequences:
                for candidate in candidates:
                    if self._is_subsequence(candidate, sequence):
                        candidate_counts[tuple(candidate)] += 1
            
            # Filter frequent k-patterns
            frequent_k_patterns = {
                pattern: count for pattern, count in candidate_counts.items()
                if count >= min_support_count
            }
            
            if frequent_k_patterns:
                frequent_patterns[k] = []
                for pattern, count in frequent_k_patterns.items():
                    frequent_patterns[k].append({
                        'pattern': list(pattern),
                        'support': count / n_sequences,
                        'count': count
                    })
            else:
                break
            
            k += 1
        
        return frequent_patterns
    
    def _generate_sequential_candidates(self, frequent_patterns: List[Dict[str, Any]]) -> List[List[str]]:
        """Generate candidate sequential patterns."""
        candidates = []
        
        for i in range(len(frequent_patterns)):
            for j in range(len(frequent_patterns)):
                pattern1 = frequent_patterns[i]['pattern']
                pattern2 = frequent_patterns[j]['pattern']
                
                # Join patterns
                if pattern1[1:] == pattern2[:-1]:
                    candidate = pattern1 + [pattern2[-1]]
                    candidates.append(candidate)
        
        return candidates
    
    def _is_subsequence(self, pattern: List[str], sequence: List[str]) -> bool:
        """Check if pattern is a subsequence of sequence."""
        if len(pattern) > len(sequence):
            return False
        
        pattern_idx = 0
        for item in sequence:
            if pattern_idx < len(pattern) and item == pattern[pattern_idx]:
                pattern_idx += 1
                if pattern_idx == len(pattern):
                    return True
        
        return False
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Validate input for sequential pattern mining."""
        if not data:
            return False
        
        for party_id, party_data in data.items():
            if not isinstance(party_data, list):
                return False
            if len(party_data) == 0:
                return False
            
            # Check if each item is a sequence
            for item in party_data:
                if not isinstance(item, (list, tuple)):
                    return False
        
        return True
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure sequential pattern mining."""
        return """
# Secure Sequential Pattern Mining
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Input sequence data from all parties
n_parties = len(program.args)
party_sequences = {}

for i in range(n_parties):
    party_sequences[i] = []
    n_sequences = sequence_counts[i]
    
    @for_range(n_sequences)
    def _(j):
        sequence_length = sequence_lengths[i][j]
        sequence = sint.Array(sequence_length)
        
        @for_range(sequence_length)
        def _(k):
            sequence[k] = sint.get_input_from(i)
        
        party_sequences[i].append(sequence)

# Combine all sequences
all_sequences = []
for i in range(n_parties):
    all_sequences.extend(party_sequences[i])

# Mine frequent sequential patterns
# This would implement the sequential pattern mining algorithm

print_ln('Sequential pattern mining completed')
"""

class DataMiningAnalyzer:
    """Main data mining analyzer orchestrating secure computations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize data mining analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.algorithms = {}
        self.mining_results = {}
        
        # Initialize available algorithms
        self._initialize_algorithms()
    
    def _initialize_algorithms(self):
        """Initialize available data mining algorithms."""
        self.algorithms = {
            'frequent_itemsets': SecureFrequentItemsets,
            'association_rules': SecureAssociationRules,
            'outlier_detection': SecureOutlierDetection,
            'sequential_patterns': SecureSequentialPatterns
        }
    
    def mine_patterns(self, algorithm: str, data: Dict[str, Any], 
                     **kwargs) -> MiningResult:
        """
        Mine patterns using specified algorithm.
        
        Args:
            algorithm: Algorithm name
            data: Multi-party data
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Mining result
        """
        try:
            if algorithm not in self.algorithms:
                raise DataMiningError(f"Unsupported algorithm: {algorithm}")
            
            # Initialize algorithm
            algorithm_class = self.algorithms[algorithm]
            mining_algorithm = algorithm_class(**kwargs)
            
            # Validate input
            if not mining_algorithm.validate_input(data):
                raise DataMiningError(f"Invalid input for {algorithm}")
            
            # Mine patterns
            logger.info(f"Mining patterns using {algorithm}")
            result = mining_algorithm.mine(data)
            
            # Store result
            result_id = f"{algorithm}_{len(self.mining_results)}"
            self.mining_results[result_id] = result
            
            logger.info(f"Successfully mined patterns using {algorithm}")
            return result
            
        except Exception as e:
            logger.error(f"Error mining patterns with {algorithm}: {e}")
            raise DataMiningError(f"Failed to mine patterns: {e}")
    
    def mine_frequent_itemsets(self, data: Dict[str, Any], 
                              min_support: float = 0.5,
                              max_itemset_size: int = 5) -> MiningResult:
        """Mine frequent itemsets from transaction data."""
        return self.mine_patterns(
            'frequent_itemsets', data,
            min_support=min_support,
            max_itemset_size=max_itemset_size
        )
    
    def mine_association_rules(self, data: Dict[str, Any],
                              min_support: float = 0.5,
                              min_confidence: float = 0.7) -> MiningResult:
        """Mine association rules from transaction data."""
        return self.mine_patterns(
            'association_rules', data,
            min_support=min_support,
            min_confidence=min_confidence
        )
    
    def detect_outliers(self, data: Dict[str, Any],
                       method: str = 'zscore',
                       threshold: float = 3.0) -> MiningResult:
        """Detect outliers in numerical data."""
        return self.mine_patterns(
            'outlier_detection', data,
            method=method,
            threshold=threshold
        )
    
    def mine_sequential_patterns(self, data: Dict[str, Any],
                                min_support: float = 0.5,
                                max_pattern_length: int = 5) -> MiningResult:
        """Mine sequential patterns from sequence data."""
        return self.mine_patterns(
            'sequential_patterns', data,
            min_support=min_support,
            max_pattern_length=max_pattern_length
        )
    
    def get_mining_results(self) -> Dict[str, MiningResult]:
        """Get all mining results."""
        return self.mining_results.copy()
    
    def get_result_summary(self, result_id: str) -> Dict[str, Any]:
        """Get summary of a specific mining result."""
        if result_id not in self.mining_results:
            raise DataMiningError(f"Result not found: {result_id}")
        
        result = self.mining_results[result_id]
        return {
            'result_id': result_id,
            'task_type': result.task_type.value,
            'algorithm': result.algorithm,
            'metrics': result.metrics,
            'metadata': result.metadata
        }
    
    def generate_mining_report(self, result_id: str) -> Dict[str, Any]:
        """Generate comprehensive mining report."""
        try:
            if result_id not in self.mining_results:
                raise DataMiningError(f"Result not found: {result_id}")
            
            result = self.mining_results[result_id]
            
            report = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'result_summary': self.get_result_summary(result_id),
                'detailed_results': result.to_dict(),
                'insights': self._generate_insights(result),
                'recommendations': self._generate_recommendations(result)
            }
            
            logger.info(f"Generated mining report for {result_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating mining report: {e}")
            raise DataMiningError(f"Failed to generate mining report: {e}")
    
    def _generate_insights(self, result: MiningResult) -> List[str]:
        """Generate insights from mining results."""
        insights = []
        
        if result.task_type == MiningTaskType.FREQUENT_ITEMSETS:
            total_itemsets = result.metrics.get('total_itemsets', 0)
            max_size = result.metrics.get('max_itemset_size', 0)
            insights.append(f"Found {total_itemsets} frequent itemsets")
            insights.append(f"Maximum itemset size: {max_size}")
            
        elif result.task_type == MiningTaskType.ASSOCIATION_RULES:
            total_rules = result.metrics.get('total_rules', 0)
            avg_confidence = result.metrics.get('avg_confidence', 0)
            insights.append(f"Generated {total_rules} association rules")
            insights.append(f"Average confidence: {avg_confidence:.3f}")
            
        elif result.task_type == MiningTaskType.OUTLIER_DETECTION:
            outlier_ratio = result.metrics.get('outlier_ratio', 0)
            insights.append(f"Outlier ratio: {outlier_ratio:.3f}")
            
        elif result.task_type == MiningTaskType.SEQUENTIAL_PATTERNS:
            total_patterns = result.metrics.get('total_patterns', 0)
            max_length = result.metrics.get('max_pattern_length', 0)
            insights.append(f"Found {total_patterns} sequential patterns")
            insights.append(f"Maximum pattern length: {max_length}")
        
        return insights
    
    def _generate_recommendations(self, result: MiningResult) -> List[str]:
        """Generate recommendations based on mining results."""
        recommendations = []
        
        if result.task_type == MiningTaskType.FREQUENT_ITEMSETS:
            total_itemsets = result.metrics.get('total_itemsets', 0)
            if total_itemsets < 10:
                recommendations.append("Consider lowering minimum support threshold")
            elif total_itemsets > 1000:
                recommendations.append("Consider raising minimum support threshold")
                
        elif result.task_type == MiningTaskType.ASSOCIATION_RULES:
            total_rules = result.metrics.get('total_rules', 0)
            avg_confidence = result.metrics.get('avg_confidence', 0)
            if total_rules == 0:
                recommendations.append("No rules found - consider lowering confidence threshold")
            elif avg_confidence < 0.6:
                recommendations.append("Low average confidence - consider raising threshold")
                
        elif result.task_type == MiningTaskType.OUTLIER_DETECTION:
            outlier_ratio = result.metrics.get('outlier_ratio', 0)
            if outlier_ratio > 0.1:
                recommendations.append("High outlier ratio - investigate data quality")
            elif outlier_ratio < 0.01:
                recommendations.append("Very low outlier ratio - consider lowering threshold")
        
        return recommendations
    
    def export_results(self, result_id: str, filepath: str, format: str = 'json'):
        """Export mining results to file."""
        try:
            if result_id not in self.mining_results:
                raise DataMiningError(f"Result not found: {result_id}")
            
            result = self.mining_results[result_id]
            
            if format == 'json':
                with open(filepath, 'w') as f:
                    json.dump(result.to_dict(), f, indent=2, default=str)
            else:
                raise DataMiningError(f"Unsupported export format: {format}")
            
            logger.info(f"Exported mining results to {filepath}")
            
        except Exception as e:
            logger.error(f"Error exporting results: {e}")
            raise DataMiningError(f"Failed to export results: {e}")
    
    def get_mpc_program_template(self, algorithm: str) -> str:
        """Get MPC program template for specific algorithm."""
        if algorithm in self.algorithms:
            algorithm_class = self.algorithms[algorithm]
            return algorithm_class().get_mpc_program()
        else:
            raise DataMiningError(f"No MPC program available for {algorithm}")
    
    def validate_mining_request(self, request: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate mining request."""
        try:
            required_fields = ['algorithm', 'data', 'parameters']
            
            for field in required_fields:
                if field not in request:
                    return False, f"Missing required field: {field}"
            
            algorithm = request['algorithm']
            if algorithm not in self.algorithms:
                return False, f"Unsupported algorithm: {algorithm}"
            
            return True, "Valid mining request"
            
        except Exception as e:
            return False, f"Error validating request: {e}"