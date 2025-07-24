"""
Data Preprocessing Module

Handles data preprocessing for multi-party computation including normalization,
encoding, and feature engineering while preserving privacy.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from abc import ABC, abstractmethod
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

class SecurePreprocessor(ABC):
    """Abstract base class for secure preprocessing operations."""
    
    @abstractmethod
    def fit(self, data: Any) -> None:
        """Fit the preprocessor to data."""
        pass
    
    @abstractmethod
    def transform(self, data: Any) -> Any:
        """Transform data using fitted preprocessor."""
        pass
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about the preprocessing operation."""
        pass

class SecureScaler(SecurePreprocessor):
    """Secure scaling that can work with secret-shared data."""
    
    def __init__(self, method: str = 'standard', feature_range: Tuple[float, float] = (0, 1)):
        self.method = method
        self.feature_range = feature_range
        self.scaler = None
        self.fitted = False
        
    def fit(self, data: Union[np.ndarray, pd.DataFrame]) -> None:
        """Fit scaler to data."""
        try:
            if self.method == 'standard':
                self.scaler = StandardScaler()
            elif self.method == 'minmax':
                self.scaler = MinMaxScaler(feature_range=self.feature_range)
            else:
                raise PreprocessingError(f"Unsupported scaling method: {self.method}")
            
            self.scaler.fit(data)
            self.fitted = True
            logger.info(f"Fitted {self.method} scaler to data")
            
        except Exception as e:
            logger.error(f"Error fitting scaler: {e}")
            raise PreprocessingError(f"Failed to fit scaler: {e}")
    
    def transform(self, data: Union[np.ndarray, pd.DataFrame]) -> Union[np.ndarray, pd.DataFrame]:
        """Transform data using fitted scaler."""
        if not self.fitted:
            raise PreprocessingError("Scaler not fitted. Call fit() first.")
        
        try:
            transformed = self.scaler.transform(data)
            logger.info(f"Transformed data using {self.method} scaler")
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming data: {e}")
            raise PreprocessingError(f"Failed to transform data: {e}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get scaler metadata."""
        if not self.fitted:
            return {'fitted': False}
        
        metadata = {
            'fitted': True,
            'method': self.method,
            'feature_range': self.feature_range
        }
        
        if hasattr(self.scaler, 'mean_'):
            metadata['mean'] = self.scaler.mean_.tolist()
        if hasattr(self.scaler, 'scale_'):
            metadata['scale'] = self.scaler.scale_.tolist()
        if hasattr(self.scaler, 'min_'):
            metadata['min'] = self.scaler.min_.tolist()
        if hasattr(self.scaler, 'data_min_'):
            metadata['data_min'] = self.scaler.data_min_.tolist()
        if hasattr(self.scaler, 'data_max_'):
            metadata['data_max'] = self.scaler.data_max_.tolist()
        
        return metadata

class SecureEncoder(SecurePreprocessor):
    """Secure encoding for categorical variables."""
    
    def __init__(self, encoding_type: str = 'label'):
        self.encoding_type = encoding_type
        self.encoders = {}
        self.fitted = False
        
    def fit(self, data: pd.DataFrame, categorical_columns: List[str]) -> None:
        """Fit encoders to categorical columns."""
        try:
            for col in categorical_columns:
                if col not in data.columns:
                    raise PreprocessingError(f"Column {col} not found in data")
                
                if self.encoding_type == 'label':
                    encoder = LabelEncoder()
                    encoder.fit(data[col])
                    self.encoders[col] = encoder
                else:
                    raise PreprocessingError(f"Unsupported encoding type: {self.encoding_type}")
            
            self.fitted = True
            logger.info(f"Fitted {self.encoding_type} encoders to {len(categorical_columns)} columns")
            
        except Exception as e:
            logger.error(f"Error fitting encoders: {e}")
            raise PreprocessingError(f"Failed to fit encoders: {e}")
    
    def transform(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transform categorical columns using fitted encoders."""
        if not self.fitted:
            raise PreprocessingError("Encoders not fitted. Call fit() first.")
        
        try:
            transformed_data = data.copy()
            
            for col, encoder in self.encoders.items():
                if col in transformed_data.columns:
                    transformed_data[col] = encoder.transform(transformed_data[col])
            
            logger.info(f"Transformed {len(self.encoders)} categorical columns")
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error transforming categorical data: {e}")
            raise PreprocessingError(f"Failed to transform categorical data: {e}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get encoder metadata."""
        if not self.fitted:
            return {'fitted': False}
        
        metadata = {
            'fitted': True,
            'encoding_type': self.encoding_type,
            'encoded_columns': list(self.encoders.keys()),
            'class_mappings': {}
        }
        
        for col, encoder in self.encoders.items():
            if hasattr(encoder, 'classes_'):
                metadata['class_mappings'][col] = encoder.classes_.tolist()
        
        return metadata

class SecureImputer(SecurePreprocessor):
    """Secure imputation for missing values."""
    
    def __init__(self, strategy: str = 'mean'):
        self.strategy = strategy
        self.imputer = SimpleImputer(strategy=strategy)
        self.fitted = False
        
    def fit(self, data: Union[np.ndarray, pd.DataFrame]) -> None:
        """Fit imputer to data."""
        try:
            self.imputer.fit(data)
            self.fitted = True
            logger.info(f"Fitted {self.strategy} imputer to data")
            
        except Exception as e:
            logger.error(f"Error fitting imputer: {e}")
            raise PreprocessingError(f"Failed to fit imputer: {e}")
    
    def transform(self, data: Union[np.ndarray, pd.DataFrame]) -> Union[np.ndarray, pd.DataFrame]:
        """Transform data using fitted imputer."""
        if not self.fitted:
            raise PreprocessingError("Imputer not fitted. Call fit() first.")
        
        try:
            transformed = self.imputer.transform(data)
            logger.info(f"Imputed missing values using {self.strategy} strategy")
            return transformed
            
        except Exception as e:
            logger.error(f"Error imputing data: {e}")
            raise PreprocessingError(f"Failed to impute data: {e}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get imputer metadata."""
        if not self.fitted:
            return {'fitted': False}
        
        metadata = {
            'fitted': True,
            'strategy': self.strategy
        }
        
        if hasattr(self.imputer, 'statistics_'):
            metadata['statistics'] = self.imputer.statistics_.tolist()
        
        return metadata

class DataPreprocessor:
    """Main data preprocessing orchestrator for multi-party data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize preprocessor with configuration.
        
        Args:
            config: Configuration dictionary containing preprocessing rules
        """
        self.config = config
        self.preprocessors = {}
        self.processing_pipeline = []
        self.fitted = False
        
        # Initialize preprocessing pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize preprocessing pipeline from configuration."""
        try:
            if 'preprocessing_steps' in self.config:
                for step_config in self.config['preprocessing_steps']:
                    step_type = step_config['type']
                    step_params = step_config.get('parameters', {})
                    
                    if step_type == 'scaling':
                        preprocessor = SecureScaler(**step_params)
                    elif step_type == 'encoding':
                        preprocessor = SecureEncoder(**step_params)
                    elif step_type == 'imputation':
                        preprocessor = SecureImputer(**step_params)
                    else:
                        raise PreprocessingError(f"Unknown preprocessing step: {step_type}")
                    
                    self.preprocessors[step_config['name']] = preprocessor
                    self.processing_pipeline.append(step_config['name'])
            
            logger.info(f"Initialized preprocessing pipeline with {len(self.processing_pipeline)} steps")
            
        except Exception as e:
            logger.error(f"Error initializing preprocessing pipeline: {e}")
            raise PreprocessingError(f"Failed to initialize pipeline: {e}")
    
    def fit_party_data(self, party_id: str, data: Union[np.ndarray, pd.DataFrame]) -> Dict[str, Any]:
        """
        Fit preprocessing pipeline to party data.
        
        Args:
            party_id: Identifier for the party
            data: Party's data
            
        Returns:
            Metadata about the fitting process
        """
        try:
            logger.info(f"Fitting preprocessing pipeline for party {party_id}")
            
            metadata = {
                'party_id': party_id,
                'original_shape': data.shape if hasattr(data, 'shape') else len(data),
                'preprocessing_steps': {}
            }
            
            # Apply each preprocessing step
            current_data = data
            for step_name in self.processing_pipeline:
                preprocessor = self.preprocessors[step_name]
                
                # Special handling for different preprocessor types
                if isinstance(preprocessor, SecureScaler):
                    preprocessor.fit(current_data)
                elif isinstance(preprocessor, SecureEncoder):
                    categorical_cols = self._get_categorical_columns(step_name)
                    preprocessor.fit(current_data, categorical_cols)
                elif isinstance(preprocessor, SecureImputer):
                    preprocessor.fit(current_data)
                
                # Store metadata
                metadata['preprocessing_steps'][step_name] = preprocessor.get_metadata()
                
                # Update current data for next step
                current_data = preprocessor.transform(current_data)
            
            metadata['final_shape'] = current_data.shape if hasattr(current_data, 'shape') else len(current_data)
            
            logger.info(f"Successfully fitted preprocessing pipeline for party {party_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error fitting preprocessing for party {party_id}: {e}")
            raise PreprocessingError(f"Failed to fit preprocessing: {e}")
    
    def transform_party_data(self, party_id: str, data: Union[np.ndarray, pd.DataFrame]) -> Tuple[Union[np.ndarray, pd.DataFrame], Dict[str, Any]]:
        """
        Transform party data using fitted preprocessing pipeline.
        
        Args:
            party_id: Identifier for the party
            data: Party's data to transform
            
        Returns:
            Tuple of (transformed_data, metadata)
        """
        try:
            logger.info(f"Transforming data for party {party_id}")
            
            if not self.fitted:
                logger.warning("Preprocessing pipeline not fitted. Fitting now...")
                self.fit_party_data(party_id, data)
            
            metadata = {
                'party_id': party_id,
                'original_shape': data.shape if hasattr(data, 'shape') else len(data),
                'transformation_steps': {}
            }
            
            # Apply each preprocessing step
            current_data = data
            for step_name in self.processing_pipeline:
                preprocessor = self.preprocessors[step_name]
                
                # Transform data
                transformed_data = preprocessor.transform(current_data)
                
                # Store transformation metadata
                metadata['transformation_steps'][step_name] = {
                    'input_shape': current_data.shape if hasattr(current_data, 'shape') else len(current_data),
                    'output_shape': transformed_data.shape if hasattr(transformed_data, 'shape') else len(transformed_data)
                }
                
                current_data = transformed_data
            
            metadata['final_shape'] = current_data.shape if hasattr(current_data, 'shape') else len(current_data)
            
            logger.info(f"Successfully transformed data for party {party_id}")
            return current_data, metadata
            
        except Exception as e:
            logger.error(f"Error transforming data for party {party_id}: {e}")
            raise PreprocessingError(f"Failed to transform data: {e}")
    
    def _get_categorical_columns(self, step_name: str) -> List[str]:
        """Get categorical columns for encoding step."""
        step_config = None
        for step in self.config.get('preprocessing_steps', []):
            if step['name'] == step_name:
                step_config = step
                break
        
        if step_config and 'categorical_columns' in step_config['parameters']:
            return step_config['parameters']['categorical_columns']
        
        return []
    
    def prepare_for_mpc(self, party_data: Dict[str, Union[np.ndarray, pd.DataFrame]]) -> Dict[str, Any]:
        """
        Prepare all party data for MPC computation.
        
        Args:
            party_data: Dictionary mapping party IDs to their data
            
        Returns:
            Prepared data and metadata for MPC computation
        """
        try:
            logger.info(f"Preparing data from {len(party_data)} parties for MPC")
            
            prepared_data = {}
            metadata = {
                'total_parties': len(party_data),
                'party_metadata': {},
                'global_metadata': {}
            }
            
            # Process each party's data
            for party_id, data in party_data.items():
                transformed_data, party_metadata = self.transform_party_data(party_id, data)
                prepared_data[party_id] = transformed_data
                metadata['party_metadata'][party_id] = party_metadata
            
            # Validate compatibility across parties
            is_compatible, global_meta = self._validate_compatibility(prepared_data)
            metadata['global_metadata'] = global_meta
            
            if not is_compatible:
                raise PreprocessingError("Data incompatible across parties after preprocessing")
            
            # Convert to MPC-compatible format
            mpc_data = self._convert_to_mpc_format(prepared_data)
            
            logger.info("Successfully prepared data for MPC computation")
            return {
                'mpc_data': mpc_data,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"Error preparing data for MPC: {e}")
            raise PreprocessingError(f"Failed to prepare data for MPC: {e}")
    
    def _validate_compatibility(self, prepared_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Validate that preprocessed data is compatible across parties."""
        try:
            party_shapes = {}
            for party_id, data in prepared_data.items():
                if hasattr(data, 'shape'):
                    party_shapes[party_id] = data.shape
                else:
                    party_shapes[party_id] = (len(data),)
            
            # Check feature dimension compatibility
            feature_dims = [shape[1] if len(shape) > 1 else 1 for shape in party_shapes.values()]
            
            global_metadata = {
                'party_shapes': party_shapes,
                'feature_dimensions': feature_dims,
                'compatible': len(set(feature_dims)) == 1,
                'total_samples': sum(shape[0] for shape in party_shapes.values())
            }
            
            return global_metadata['compatible'], global_metadata
            
        except Exception as e:
            logger.error(f"Error validating compatibility: {e}")
            return False, {'error': str(e)}
    
    def _convert_to_mpc_format(self, prepared_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert prepared data to MPC-compatible format."""
        try:
            mpc_data = {}
            
            for party_id, data in prepared_data.items():
                # Convert to numpy array if needed
                if isinstance(data, pd.DataFrame):
                    data = data.values
                
                # Ensure data is in the correct format for MPC
                if not isinstance(data, np.ndarray):
                    data = np.array(data)
                
                # Convert to appropriate data type
                if data.dtype == np.object:
                    data = data.astype(np.float64)
                
                mpc_data[party_id] = data
            
            return mpc_data
            
        except Exception as e:
            logger.error(f"Error converting to MPC format: {e}")
            raise PreprocessingError(f"Failed to convert to MPC format: {e}")
    
    def get_preprocessing_summary(self) -> Dict[str, Any]:
        """Get summary of preprocessing configuration and status."""
        summary = {
            'preprocessing_steps': self.processing_pipeline,
            'fitted': self.fitted,
            'preprocessor_details': {}
        }
        
        for name, preprocessor in self.preprocessors.items():
            summary['preprocessor_details'][name] = preprocessor.get_metadata()
        
        return summary
    
    def save_preprocessing_state(self, filepath: str) -> None:
        """Save preprocessing state to file."""
        try:
            state = {
                'config': self.config,
                'processing_pipeline': self.processing_pipeline,
                'fitted': self.fitted,
                'preprocessor_metadata': {}
            }
            
            for name, preprocessor in self.preprocessors.items():
                state['preprocessor_metadata'][name] = preprocessor.get_metadata()
            
            with open(filepath, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Saved preprocessing state to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving preprocessing state: {e}")
            raise PreprocessingError(f"Failed to save preprocessing state: {e}")
    
    def load_preprocessing_state(self, filepath: str) -> None:
        """Load preprocessing state from file."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.config = state['config']
            self.processing_pipeline = state['processing_pipeline']
            self.fitted = state['fitted']
            
            # Reinitialize preprocessors
            self._initialize_pipeline()
            
            logger.info(f"Loaded preprocessing state from {filepath}")
            
        except Exception as e:
            logger.error(f"Error loading preprocessing state: {e}")
            raise PreprocessingError(f"Failed to load preprocessing state: {e}")