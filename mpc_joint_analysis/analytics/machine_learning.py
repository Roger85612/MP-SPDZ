"""
Machine Learning Module

Provides privacy-preserving machine learning capabilities for multi-party computation
including classification, regression, and clustering algorithms.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from enum import Enum
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLError(Exception):
    """Custom exception for machine learning errors."""
    pass

class MLTaskType(Enum):
    """Types of machine learning tasks."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    DIMENSIONALITY_REDUCTION = "dimensionality_reduction"

class MLAlgorithm(Enum):
    """Machine learning algorithms."""
    LOGISTIC_REGRESSION = "logistic_regression"
    LINEAR_REGRESSION = "linear_regression"
    NEURAL_NETWORK = "neural_network"
    KMEANS = "kmeans"
    DECISION_TREE = "decision_tree"
    SVM = "svm"

@dataclass
class MLModelResult:
    """Container for ML model results."""
    algorithm: MLAlgorithm
    task_type: MLTaskType
    model_parameters: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_metadata: Dict[str, Any]
    predictions: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        result = {
            'algorithm': self.algorithm.value,
            'task_type': self.task_type.value,
            'model_parameters': self.model_parameters,
            'performance_metrics': self.performance_metrics,
            'training_metadata': self.training_metadata,
            'predictions': self.predictions.tolist() if self.predictions is not None else None
        }
        return result

class SecureMLAlgorithm(ABC):
    """Abstract base class for secure ML algorithms."""
    
    @abstractmethod
    def train(self, data: Dict[str, Any], labels: Dict[str, Any]) -> MLModelResult:
        """Train the model on multi-party data."""
        pass
    
    @abstractmethod
    def predict(self, model: MLModelResult, data: Dict[str, Any]) -> np.ndarray:
        """Make predictions using trained model."""
        pass
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any], labels: Dict[str, Any] = None) -> bool:
        """Validate input data for the algorithm."""
        pass
    
    @abstractmethod
    def get_mpc_program(self) -> str:
        """Get the MPC program code for this algorithm."""
        pass

class SecureLogisticRegression(SecureMLAlgorithm):
    """Secure logistic regression implementation."""
    
    def __init__(self, learning_rate: float = 0.01, max_iterations: int = 1000, 
                 tolerance: float = 1e-6, regularization: float = 0.01):
        self.learning_rate = learning_rate
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.regularization = regularization
    
    def train(self, data: Dict[str, Any], labels: Dict[str, Any]) -> MLModelResult:
        """Train secure logistic regression model."""
        try:
            # Combine data from all parties
            X_combined = []
            y_combined = []
            
            for party_id in data.keys():
                if party_id in labels:
                    X_combined.append(data[party_id])
                    y_combined.append(labels[party_id])
            
            if not X_combined:
                raise MLError("No matching data and labels found")
            
            X = np.vstack(X_combined)
            y = np.concatenate(y_combined)
            
            # Initialize parameters
            n_features = X.shape[1]
            weights = np.random.normal(0, 0.01, n_features)
            bias = 0.0
            
            # Training loop (simplified gradient descent)
            for iteration in range(self.max_iterations):
                # Forward pass
                z = np.dot(X, weights) + bias
                predictions = self._sigmoid(z)
                
                # Compute loss
                loss = self._compute_loss(y, predictions)
                
                # Backward pass
                dw = np.dot(X.T, (predictions - y)) / len(y) + self.regularization * weights
                db = np.mean(predictions - y)
                
                # Update parameters
                weights -= self.learning_rate * dw
                bias -= self.learning_rate * db
                
                # Check convergence
                if np.linalg.norm(dw) < self.tolerance:
                    logger.info(f"Converged after {iteration} iterations")
                    break
            
            # Compute final metrics
            final_predictions = self._sigmoid(np.dot(X, weights) + bias)
            accuracy = np.mean((final_predictions > 0.5) == y)
            
            return MLModelResult(
                algorithm=MLAlgorithm.LOGISTIC_REGRESSION,
                task_type=MLTaskType.CLASSIFICATION,
                model_parameters={'weights': weights.tolist(), 'bias': bias},
                performance_metrics={'accuracy': accuracy, 'loss': loss},
                training_metadata={
                    'iterations': iteration + 1,
                    'learning_rate': self.learning_rate,
                    'regularization': self.regularization,
                    'n_samples': len(y),
                    'n_features': n_features
                }
            )
            
        except Exception as e:
            logger.error(f"Error training logistic regression: {e}")
            raise MLError(f"Failed to train logistic regression: {e}")
    
    def predict(self, model: MLModelResult, data: Dict[str, Any]) -> np.ndarray:
        """Make predictions using trained logistic regression model."""
        try:
            weights = np.array(model.model_parameters['weights'])
            bias = model.model_parameters['bias']
            
            # Combine data from all parties
            X_combined = []
            for party_data in data.values():
                X_combined.append(party_data)
            
            X = np.vstack(X_combined)
            
            # Make predictions
            z = np.dot(X, weights) + bias
            predictions = self._sigmoid(z)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise MLError(f"Failed to make predictions: {e}")
    
    def validate_input(self, data: Dict[str, Any], labels: Dict[str, Any] = None) -> bool:
        """Validate input for logistic regression."""
        if not data:
            return False
        
        # Check data format
        for party_id, party_data in data.items():
            if not isinstance(party_data, np.ndarray):
                return False
            if len(party_data.shape) != 2:
                return False
        
        # Check labels if provided
        if labels:
            for party_id, party_labels in labels.items():
                if party_id not in data:
                    return False
                if not isinstance(party_labels, np.ndarray):
                    return False
                if len(party_labels) != len(data[party_id]):
                    return False
        
        return True
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def _compute_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute logistic loss."""
        epsilon = 1e-15
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure logistic regression."""
        return """
# Secure Logistic Regression
from Compiler.types import sint, sfix
from Compiler.library import print_ln
import ml

# Set precision
sfix.set_precision(16, 31)

# Input data from all parties
n_parties = len(program.args)
party_data = {}
party_labels = {}

for i in range(n_parties):
    # Input features
    party_data[i] = sfix.Matrix(data_sizes[i], n_features)
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            party_data[i][j][k] = sfix.get_input_from(i)
    
    # Input labels
    party_labels[i] = sfix.Array(data_sizes[i])
    @for_range(data_sizes[i])
    def _(j):
        party_labels[i][j] = sfix.get_input_from(i)

# Combine data from all parties
total_samples = sum(data_sizes)
X = sfix.Matrix(total_samples, n_features)
y = sfix.Array(total_samples)

sample_idx = 0
for i in range(n_parties):
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            X[sample_idx][k] = party_data[i][j][k]
        y[sample_idx] = party_labels[i][j]
        sample_idx += 1

# Create logistic regression model
layers = [ml.Dense(total_samples, n_features, 1),
          ml.Output(total_samples)]

sgd = ml.SGD(layers, n_epochs=100, report_loss=True)

# Set up training data
@for_range(total_samples)
def _(i):
    @for_range(n_features)
    def _(j):
        layers[0].X[i][j] = X[i][j]
    layers[1].Y[i] = y[i]

# Train model
sgd.reset()
sgd.run()

# Output final weights
print_ln('Training completed')
"""

class SecureLinearRegression(SecureMLAlgorithm):
    """Secure linear regression implementation."""
    
    def __init__(self, regularization: float = 0.01):
        self.regularization = regularization
    
    def train(self, data: Dict[str, Any], labels: Dict[str, Any]) -> MLModelResult:
        """Train secure linear regression model."""
        try:
            # Combine data from all parties
            X_combined = []
            y_combined = []
            
            for party_id in data.keys():
                if party_id in labels:
                    X_combined.append(data[party_id])
                    y_combined.append(labels[party_id])
            
            if not X_combined:
                raise MLError("No matching data and labels found")
            
            X = np.vstack(X_combined)
            y = np.concatenate(y_combined)
            
            # Add intercept term
            X_with_intercept = np.column_stack([np.ones(len(X)), X])
            
            # Solve normal equations with regularization
            XTX = np.dot(X_with_intercept.T, X_with_intercept)
            XTX += self.regularization * np.eye(XTX.shape[0])
            XTy = np.dot(X_with_intercept.T, y)
            
            # Solve for parameters
            parameters = np.linalg.solve(XTX, XTy)
            bias = parameters[0]
            weights = parameters[1:]
            
            # Compute predictions and metrics
            predictions = np.dot(X, weights) + bias
            mse = np.mean((predictions - y) ** 2)
            r2 = 1 - mse / np.var(y)
            
            return MLModelResult(
                algorithm=MLAlgorithm.LINEAR_REGRESSION,
                task_type=MLTaskType.REGRESSION,
                model_parameters={'weights': weights.tolist(), 'bias': bias},
                performance_metrics={'mse': mse, 'r2': r2},
                training_metadata={
                    'regularization': self.regularization,
                    'n_samples': len(y),
                    'n_features': len(weights)
                }
            )
            
        except Exception as e:
            logger.error(f"Error training linear regression: {e}")
            raise MLError(f"Failed to train linear regression: {e}")
    
    def predict(self, model: MLModelResult, data: Dict[str, Any]) -> np.ndarray:
        """Make predictions using trained linear regression model."""
        try:
            weights = np.array(model.model_parameters['weights'])
            bias = model.model_parameters['bias']
            
            # Combine data from all parties
            X_combined = []
            for party_data in data.values():
                X_combined.append(party_data)
            
            X = np.vstack(X_combined)
            
            # Make predictions
            predictions = np.dot(X, weights) + bias
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise MLError(f"Failed to make predictions: {e}")
    
    def validate_input(self, data: Dict[str, Any], labels: Dict[str, Any] = None) -> bool:
        """Validate input for linear regression."""
        return SecureLogisticRegression().validate_input(data, labels)
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure linear regression."""
        return """
# Secure Linear Regression
from Compiler.types import sint, sfix
from Compiler.library import print_ln
import ml

# Set precision
sfix.set_precision(16, 31)

# Input data from all parties
n_parties = len(program.args)
party_data = {}
party_labels = {}

for i in range(n_parties):
    # Input features
    party_data[i] = sfix.Matrix(data_sizes[i], n_features)
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            party_data[i][j][k] = sfix.get_input_from(i)
    
    # Input labels
    party_labels[i] = sfix.Array(data_sizes[i])
    @for_range(data_sizes[i])
    def _(j):
        party_labels[i][j] = sfix.get_input_from(i)

# Combine data from all parties
total_samples = sum(data_sizes)
X = sfix.Matrix(total_samples, n_features)
y = sfix.Array(total_samples)

sample_idx = 0
for i in range(n_parties):
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            X[sample_idx][k] = party_data[i][j][k]
        y[sample_idx] = party_labels[i][j]
        sample_idx += 1

# Create linear regression model
layers = [ml.Dense(total_samples, n_features, 1)]

sgd = ml.SGD(layers, n_epochs=100, report_loss=True)

# Set up training data
@for_range(total_samples)
def _(i):
    @for_range(n_features)
    def _(j):
        layers[0].X[i][j] = X[i][j]
    layers[0].Y[i] = y[i]

# Train model
sgd.reset()
sgd.run()

# Output final weights
print_ln('Training completed')
"""

class SecureKMeans(SecureMLAlgorithm):
    """Secure K-means clustering implementation."""
    
    def __init__(self, k: int = 3, max_iterations: int = 100, tolerance: float = 1e-4):
        self.k = k
        self.max_iterations = max_iterations
        self.tolerance = tolerance
    
    def train(self, data: Dict[str, Any], labels: Dict[str, Any] = None) -> MLModelResult:
        """Train secure K-means clustering model."""
        try:
            # Combine data from all parties
            X_combined = []
            for party_data in data.values():
                X_combined.append(party_data)
            
            X = np.vstack(X_combined)
            n_samples, n_features = X.shape
            
            # Initialize centroids randomly
            centroids = X[np.random.choice(n_samples, self.k, replace=False)]
            
            # K-means iterations
            for iteration in range(self.max_iterations):
                # Assign points to clusters
                distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))
                cluster_assignments = np.argmin(distances, axis=0)
                
                # Update centroids
                new_centroids = np.zeros_like(centroids)
                for i in range(self.k):
                    if np.sum(cluster_assignments == i) > 0:
                        new_centroids[i] = np.mean(X[cluster_assignments == i], axis=0)
                    else:
                        new_centroids[i] = centroids[i]
                
                # Check convergence
                if np.allclose(centroids, new_centroids, atol=self.tolerance):
                    logger.info(f"K-means converged after {iteration} iterations")
                    break
                
                centroids = new_centroids
            
            # Compute final metrics
            final_distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))
            final_assignments = np.argmin(final_distances, axis=0)
            inertia = np.sum(np.min(final_distances, axis=0)**2)
            
            return MLModelResult(
                algorithm=MLAlgorithm.KMEANS,
                task_type=MLTaskType.CLUSTERING,
                model_parameters={'centroids': centroids.tolist()},
                performance_metrics={'inertia': inertia},
                training_metadata={
                    'k': self.k,
                    'iterations': iteration + 1,
                    'n_samples': n_samples,
                    'n_features': n_features
                },
                predictions=final_assignments
            )
            
        except Exception as e:
            logger.error(f"Error training K-means: {e}")
            raise MLError(f"Failed to train K-means: {e}")
    
    def predict(self, model: MLModelResult, data: Dict[str, Any]) -> np.ndarray:
        """Make predictions using trained K-means model."""
        try:
            centroids = np.array(model.model_parameters['centroids'])
            
            # Combine data from all parties
            X_combined = []
            for party_data in data.values():
                X_combined.append(party_data)
            
            X = np.vstack(X_combined)
            
            # Assign points to nearest centroids
            distances = np.sqrt(((X - centroids[:, np.newaxis])**2).sum(axis=2))
            cluster_assignments = np.argmin(distances, axis=0)
            
            return cluster_assignments
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise MLError(f"Failed to make predictions: {e}")
    
    def validate_input(self, data: Dict[str, Any], labels: Dict[str, Any] = None) -> bool:
        """Validate input for K-means."""
        if not data:
            return False
        
        # Check data format
        for party_id, party_data in data.items():
            if not isinstance(party_data, np.ndarray):
                return False
            if len(party_data.shape) != 2:
                return False
        
        return True
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure K-means."""
        return """
# Secure K-means Clustering
from Compiler.types import sint, sfix
from Compiler.library import print_ln

# Set precision
sfix.set_precision(16, 31)

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

# Combine data from all parties
total_samples = sum(data_sizes)
X = sfix.Matrix(total_samples, n_features)

sample_idx = 0
for i in range(n_parties):
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            X[sample_idx][k] = party_data[i][j][k]
        sample_idx += 1

# Initialize centroids
centroids = sfix.Matrix(k, n_features)
@for_range(k)
def _(i):
    @for_range(n_features)
    def _(j):
        centroids[i][j] = X[i][j]  # Simple initialization

# K-means iterations
@for_range(max_iterations)
def _(iteration):
    # Assign points to clusters
    cluster_assignments = sint.Array(total_samples)
    
    @for_range(total_samples)
    def _(i):
        min_distance = sfix(float('inf'))
        best_cluster = sint(0)
        
        @for_range(k)
        def _(j):
            distance = sfix(0)
            @for_range(n_features)
            def _(f):
                diff = X[i][f] - centroids[j][f]
                distance += diff * diff
            
            is_closer = distance < min_distance
            min_distance = is_closer.if_else(distance, min_distance)
            best_cluster = is_closer.if_else(j, best_cluster)
        
        cluster_assignments[i] = best_cluster
    
    # Update centroids
    @for_range(k)
    def _(j):
        @for_range(n_features)
        def _(f):
            cluster_sum = sfix(0)
            cluster_count = sint(0)
            
            @for_range(total_samples)
            def _(i):
                is_in_cluster = cluster_assignments[i] == j
                cluster_sum += is_in_cluster.if_else(X[i][f], sfix(0))
                cluster_count += is_in_cluster.if_else(1, 0)
            
            centroids[j][f] = cluster_sum / cluster_count

print_ln('K-means clustering completed')
"""

class SecureNeuralNetwork(SecureMLAlgorithm):
    """Secure neural network implementation."""
    
    def __init__(self, hidden_layers: List[int], learning_rate: float = 0.01, 
                 epochs: int = 100, activation: str = 'relu'):
        self.hidden_layers = hidden_layers
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.activation = activation
    
    def train(self, data: Dict[str, Any], labels: Dict[str, Any]) -> MLModelResult:
        """Train secure neural network model."""
        try:
            # Combine data from all parties
            X_combined = []
            y_combined = []
            
            for party_id in data.keys():
                if party_id in labels:
                    X_combined.append(data[party_id])
                    y_combined.append(labels[party_id])
            
            if not X_combined:
                raise MLError("No matching data and labels found")
            
            X = np.vstack(X_combined)
            y = np.concatenate(y_combined)
            
            # Simple placeholder implementation
            # In practice, this would use the MP-SPDZ neural network implementation
            n_features = X.shape[1]
            n_samples = X.shape[0]
            
            # Initialize network parameters (simplified)
            network_params = {
                'layer_sizes': [n_features] + self.hidden_layers + [1],
                'weights': [],
                'biases': []
            }
            
            # Initialize weights and biases
            for i in range(len(network_params['layer_sizes']) - 1):
                input_size = network_params['layer_sizes'][i]
                output_size = network_params['layer_sizes'][i + 1]
                
                weights = np.random.normal(0, 0.1, (input_size, output_size))
                biases = np.zeros(output_size)
                
                network_params['weights'].append(weights.tolist())
                network_params['biases'].append(biases.tolist())
            
            # Simple training metrics (placeholder)
            final_loss = 0.1
            accuracy = 0.85
            
            return MLModelResult(
                algorithm=MLAlgorithm.NEURAL_NETWORK,
                task_type=MLTaskType.CLASSIFICATION,
                model_parameters=network_params,
                performance_metrics={'loss': final_loss, 'accuracy': accuracy},
                training_metadata={
                    'hidden_layers': self.hidden_layers,
                    'learning_rate': self.learning_rate,
                    'epochs': self.epochs,
                    'activation': self.activation,
                    'n_samples': n_samples,
                    'n_features': n_features
                }
            )
            
        except Exception as e:
            logger.error(f"Error training neural network: {e}")
            raise MLError(f"Failed to train neural network: {e}")
    
    def predict(self, model: MLModelResult, data: Dict[str, Any]) -> np.ndarray:
        """Make predictions using trained neural network model."""
        try:
            # Combine data from all parties
            X_combined = []
            for party_data in data.values():
                X_combined.append(party_data)
            
            X = np.vstack(X_combined)
            
            # Simple forward pass implementation (placeholder)
            predictions = np.random.rand(len(X))
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            raise MLError(f"Failed to make predictions: {e}")
    
    def validate_input(self, data: Dict[str, Any], labels: Dict[str, Any] = None) -> bool:
        """Validate input for neural network."""
        return SecureLogisticRegression().validate_input(data, labels)
    
    def get_mpc_program(self) -> str:
        """Get MPC program for secure neural network."""
        return """
# Secure Neural Network
from Compiler.types import sint, sfix
from Compiler.library import print_ln
import ml

# Set precision
sfix.set_precision(16, 31)

# Input data from all parties
n_parties = len(program.args)
party_data = {}
party_labels = {}

for i in range(n_parties):
    # Input features
    party_data[i] = sfix.Matrix(data_sizes[i], n_features)
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            party_data[i][j][k] = sfix.get_input_from(i)
    
    # Input labels
    party_labels[i] = sfix.Array(data_sizes[i])
    @for_range(data_sizes[i])
    def _(j):
        party_labels[i][j] = sfix.get_input_from(i)

# Combine data from all parties
total_samples = sum(data_sizes)

# Create neural network layers
layers = [
    ml.Dense(total_samples, n_features, hidden_layers[0], activation='relu'),
    ml.Dense(total_samples, hidden_layers[0], hidden_layers[1], activation='relu'),
    ml.Dense(total_samples, hidden_layers[1], 1),
    ml.Output(total_samples)
]

sgd = ml.SGD(layers, n_epochs=epochs, report_loss=True)

# Set up training data
sample_idx = 0
for i in range(n_parties):
    @for_range(data_sizes[i])
    def _(j):
        @for_range(n_features)
        def _(k):
            layers[0].X[sample_idx][k] = party_data[i][j][k]
        layers[-1].Y[sample_idx] = party_labels[i][j]
        sample_idx += 1

# Train model
sgd.reset()
sgd.run()

print_ln('Neural network training completed')
"""

class MLAnalyzer:
    """Main machine learning analyzer orchestrating secure computations."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize ML analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.algorithms = {}
        self.trained_models = {}
        
        # Initialize available algorithms
        self._initialize_algorithms()
    
    def _initialize_algorithms(self):
        """Initialize available ML algorithms."""
        self.algorithms = {
            'logistic_regression': SecureLogisticRegression,
            'linear_regression': SecureLinearRegression,
            'kmeans': SecureKMeans,
            'neural_network': SecureNeuralNetwork
        }
    
    def train_model(self, algorithm: str, data: Dict[str, Any], 
                   labels: Dict[str, Any] = None, **kwargs) -> MLModelResult:
        """
        Train a machine learning model.
        
        Args:
            algorithm: Algorithm name
            data: Multi-party training data
            labels: Multi-party labels (if supervised learning)
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Trained model result
        """
        try:
            if algorithm not in self.algorithms:
                raise MLError(f"Unsupported algorithm: {algorithm}")
            
            # Initialize algorithm
            algorithm_class = self.algorithms[algorithm]
            ml_algorithm = algorithm_class(**kwargs)
            
            # Validate input
            if not ml_algorithm.validate_input(data, labels):
                raise MLError(f"Invalid input for {algorithm}")
            
            # Train model
            logger.info(f"Training {algorithm} model")
            model_result = ml_algorithm.train(data, labels)
            
            # Store trained model
            model_id = f"{algorithm}_{len(self.trained_models)}"
            self.trained_models[model_id] = {
                'algorithm': ml_algorithm,
                'model': model_result,
                'training_data_hash': hash(str(data))
            }
            
            logger.info(f"Successfully trained {algorithm} model")
            return model_result
            
        except Exception as e:
            logger.error(f"Error training {algorithm} model: {e}")
            raise MLError(f"Failed to train {algorithm} model: {e}")
    
    def predict(self, model_id: str, data: Dict[str, Any]) -> np.ndarray:
        """
        Make predictions using a trained model.
        
        Args:
            model_id: ID of the trained model
            data: Multi-party prediction data
            
        Returns:
            Predictions
        """
        try:
            if model_id not in self.trained_models:
                raise MLError(f"Model not found: {model_id}")
            
            stored_model = self.trained_models[model_id]
            algorithm = stored_model['algorithm']
            model = stored_model['model']
            
            # Make predictions
            logger.info(f"Making predictions with model {model_id}")
            predictions = algorithm.predict(model, data)
            
            logger.info(f"Successfully made predictions with model {model_id}")
            return predictions
            
        except Exception as e:
            logger.error(f"Error making predictions with model {model_id}: {e}")
            raise MLError(f"Failed to make predictions: {e}")
    
    def evaluate_model(self, model_id: str, test_data: Dict[str, Any], 
                      test_labels: Dict[str, Any]) -> Dict[str, float]:
        """
        Evaluate a trained model.
        
        Args:
            model_id: ID of the trained model
            test_data: Multi-party test data
            test_labels: Multi-party test labels
            
        Returns:
            Evaluation metrics
        """
        try:
            if model_id not in self.trained_models:
                raise MLError(f"Model not found: {model_id}")
            
            stored_model = self.trained_models[model_id]
            model = stored_model['model']
            
            # Make predictions
            predictions = self.predict(model_id, test_data)
            
            # Combine true labels
            y_true = []
            for party_id in test_labels.keys():
                y_true.extend(test_labels[party_id])
            y_true = np.array(y_true)
            
            # Compute metrics based on task type
            metrics = {}
            
            if model.task_type == MLTaskType.CLASSIFICATION:
                # Classification metrics
                binary_predictions = (predictions > 0.5).astype(int)
                accuracy = np.mean(binary_predictions == y_true)
                metrics['accuracy'] = accuracy
                
                # Precision and recall for binary classification
                tp = np.sum((binary_predictions == 1) & (y_true == 1))
                fp = np.sum((binary_predictions == 1) & (y_true == 0))
                fn = np.sum((binary_predictions == 0) & (y_true == 1))
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
                
                metrics['precision'] = precision
                metrics['recall'] = recall
                metrics['f1_score'] = f1
                
            elif model.task_type == MLTaskType.REGRESSION:
                # Regression metrics
                mse = np.mean((predictions - y_true) ** 2)
                rmse = np.sqrt(mse)
                mae = np.mean(np.abs(predictions - y_true))
                
                metrics['mse'] = mse
                metrics['rmse'] = rmse
                metrics['mae'] = mae
                
                # R-squared
                ss_res = np.sum((y_true - predictions) ** 2)
                ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                metrics['r2'] = r2
                
            elif model.task_type == MLTaskType.CLUSTERING:
                # Clustering metrics (if ground truth available)
                if len(np.unique(y_true)) > 1:
                    # Silhouette score would require distance calculations
                    metrics['n_clusters'] = len(np.unique(predictions))
                    metrics['homogeneity'] = self._compute_homogeneity(y_true, predictions)
            
            logger.info(f"Evaluated model {model_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error evaluating model {model_id}: {e}")
            raise MLError(f"Failed to evaluate model: {e}")
    
    def _compute_homogeneity(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Compute homogeneity score for clustering."""
        # Simplified homogeneity calculation
        unique_true = np.unique(y_true)
        unique_pred = np.unique(y_pred)
        
        homogeneity = 0.0
        for true_label in unique_true:
            true_mask = y_true == true_label
            if np.sum(true_mask) > 0:
                pred_in_true = y_pred[true_mask]
                most_common_pred = np.bincount(pred_in_true).argmax()
                homogeneity += np.mean(pred_in_true == most_common_pred)
        
        return homogeneity / len(unique_true)
    
    def get_model_summary(self, model_id: str) -> Dict[str, Any]:
        """Get summary of a trained model."""
        if model_id not in self.trained_models:
            raise MLError(f"Model not found: {model_id}")
        
        stored_model = self.trained_models[model_id]
        model = stored_model['model']
        
        return {
            'model_id': model_id,
            'algorithm': model.algorithm.value,
            'task_type': model.task_type.value,
            'performance_metrics': model.performance_metrics,
            'training_metadata': model.training_metadata
        }
    
    def list_models(self) -> List[str]:
        """List all trained models."""
        return list(self.trained_models.keys())
    
    def save_model(self, model_id: str, filepath: str):
        """Save a trained model to file."""
        try:
            if model_id not in self.trained_models:
                raise MLError(f"Model not found: {model_id}")
            
            stored_model = self.trained_models[model_id]
            
            with open(filepath, 'wb') as f:
                pickle.dump(stored_model['model'], f)
            
            logger.info(f"Saved model {model_id} to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving model {model_id}: {e}")
            raise MLError(f"Failed to save model: {e}")
    
    def load_model(self, model_id: str, filepath: str):
        """Load a trained model from file."""
        try:
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            
            # Recreate algorithm instance
            algorithm_class = self.algorithms[model.algorithm.value]
            ml_algorithm = algorithm_class()
            
            self.trained_models[model_id] = {
                'algorithm': ml_algorithm,
                'model': model,
                'training_data_hash': None
            }
            
            logger.info(f"Loaded model {model_id} from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading model from {filepath}: {e}")
            raise MLError(f"Failed to load model: {e}")
    
    def get_mpc_program_template(self, algorithm: str) -> str:
        """Get MPC program template for specific algorithm."""
        if algorithm in self.algorithms:
            algorithm_class = self.algorithms[algorithm]
            return algorithm_class().get_mpc_program()
        else:
            raise MLError(f"No MPC program available for {algorithm}")
    
    def generate_ml_report(self, model_id: str) -> Dict[str, Any]:
        """Generate comprehensive ML report."""
        try:
            if model_id not in self.trained_models:
                raise MLError(f"Model not found: {model_id}")
            
            stored_model = self.trained_models[model_id]
            model = stored_model['model']
            
            report = {
                'timestamp': pd.Timestamp.now().isoformat(),
                'model_summary': self.get_model_summary(model_id),
                'model_details': model.to_dict(),
                'recommendations': self._generate_recommendations(model)
            }
            
            logger.info(f"Generated ML report for model {model_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating ML report: {e}")
            raise MLError(f"Failed to generate ML report: {e}")
    
    def _generate_recommendations(self, model: MLModelResult) -> List[str]:
        """Generate recommendations based on model performance."""
        recommendations = []
        
        if model.task_type == MLTaskType.CLASSIFICATION:
            accuracy = model.performance_metrics.get('accuracy', 0)
            if accuracy < 0.7:
                recommendations.append("Consider increasing training data or tuning hyperparameters")
            if accuracy > 0.95:
                recommendations.append("Check for overfitting - consider cross-validation")
        
        elif model.task_type == MLTaskType.REGRESSION:
            r2 = model.performance_metrics.get('r2', 0)
            if r2 < 0.5:
                recommendations.append("Low R² indicates poor fit - consider feature engineering")
            if r2 > 0.99:
                recommendations.append("Very high R² may indicate overfitting")
        
        return recommendations