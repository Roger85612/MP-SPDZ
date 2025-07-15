"""
Input Validator Module

Validates data input from multiple parties to ensure compatibility and security
for joint MPC analysis without revealing sensitive information.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
import logging
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class SchemaValidator(ABC):
    """Abstract base class for schema validation."""
    
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """Validate data against schema."""
        pass

class NumericSchemaValidator(SchemaValidator):
    """Validator for numeric data schemas."""
    
    def __init__(self, expected_columns: int, data_types: List[str]):
        self.expected_columns = expected_columns
        self.data_types = data_types
    
    def validate(self, data: np.ndarray) -> bool:
        """Validate numeric data structure."""
        if data.shape[1] != self.expected_columns:
            return False
        
        # Check data types compatibility
        for i, expected_type in enumerate(self.data_types):
            if expected_type == 'int' and not np.issubdtype(data[:, i].dtype, np.integer):
                return False
            elif expected_type == 'float' and not np.issubdtype(data[:, i].dtype, np.floating):
                return False
                
        return True

class CategoricalSchemaValidator(SchemaValidator):
    """Validator for categorical data schemas."""
    
    def __init__(self, expected_categories: Dict[str, List[str]]):
        self.expected_categories = expected_categories
    
    def validate(self, data: pd.DataFrame) -> bool:
        """Validate categorical data structure."""
        for column, expected_cats in self.expected_categories.items():
            if column not in data.columns:
                return False
            
            unique_values = data[column].unique()
            if not all(val in expected_cats for val in unique_values):
                return False
                
        return True

class InputValidator:
    """Main input validator for multi-party data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize validator with configuration.
        
        Args:
            config: Configuration dictionary containing validation rules
        """
        self.config = config
        self.party_schemas = {}
        self.global_schema = None
        
        # Load validation rules
        self._load_validation_rules()
        
    def _load_validation_rules(self):
        """Load validation rules from configuration."""
        try:
            # Load global schema requirements
            if 'global_schema' in self.config:
                self.global_schema = self.config['global_schema']
            
            # Load party-specific schemas
            if 'party_schemas' in self.config:
                for party_id, schema in self.config['party_schemas'].items():
                    self.party_schemas[party_id] = schema
                    
            logger.info(f"Loaded validation rules for {len(self.party_schemas)} parties")
            
        except Exception as e:
            logger.error(f"Error loading validation rules: {e}")
            raise ValidationError(f"Failed to load validation rules: {e}")
    
    def validate_party_data(self, party_id: str, data: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate data from a specific party.
        
        Args:
            party_id: Identifier for the party
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, metadata)
        """
        try:
            logger.info(f"Validating data from party {party_id}")
            
            # Get party schema
            if party_id not in self.party_schemas:
                raise ValidationError(f"No schema defined for party {party_id}")
            
            schema = self.party_schemas[party_id]
            metadata = {}
            
            # Basic data type validation
            if isinstance(data, np.ndarray):
                is_valid = self._validate_numpy_data(data, schema)
                metadata['data_type'] = 'numpy'
                metadata['shape'] = data.shape
                metadata['dtype'] = str(data.dtype)
            elif isinstance(data, pd.DataFrame):
                is_valid = self._validate_pandas_data(data, schema)
                metadata['data_type'] = 'pandas'
                metadata['shape'] = data.shape
                metadata['columns'] = list(data.columns)
            else:
                raise ValidationError(f"Unsupported data type: {type(data)}")
            
            # Check for missing values
            if isinstance(data, pd.DataFrame):
                missing_count = data.isnull().sum().sum()
            else:
                missing_count = np.isnan(data).sum()
            
            metadata['missing_values'] = int(missing_count)
            
            # Size validation
            if 'max_rows' in schema:
                if len(data) > schema['max_rows']:
                    raise ValidationError(f"Data exceeds maximum rows: {len(data)} > {schema['max_rows']}")
            
            if 'min_rows' in schema:
                if len(data) < schema['min_rows']:
                    raise ValidationError(f"Data below minimum rows: {len(data)} < {schema['min_rows']}")
            
            # Additional custom validations
            if 'custom_validations' in schema:
                for validation in schema['custom_validations']:
                    if not self._apply_custom_validation(data, validation):
                        is_valid = False
                        break
            
            metadata['validation_passed'] = is_valid
            logger.info(f"Party {party_id} validation result: {is_valid}")
            
            return is_valid, metadata
            
        except Exception as e:
            logger.error(f"Error validating party {party_id} data: {e}")
            return False, {'error': str(e)}
    
    def _validate_numpy_data(self, data: np.ndarray, schema: Dict[str, Any]) -> bool:
        """Validate numpy array data."""
        try:
            # Check dimensions
            if 'expected_columns' in schema:
                if data.shape[1] != schema['expected_columns']:
                    return False
            
            # Check data types
            if 'data_types' in schema:
                validator = NumericSchemaValidator(
                    schema['expected_columns'], 
                    schema['data_types']
                )
                return validator.validate(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating numpy data: {e}")
            return False
    
    def _validate_pandas_data(self, data: pd.DataFrame, schema: Dict[str, Any]) -> bool:
        """Validate pandas DataFrame data."""
        try:
            # Check required columns
            if 'required_columns' in schema:
                required_cols = set(schema['required_columns'])
                actual_cols = set(data.columns)
                if not required_cols.issubset(actual_cols):
                    return False
            
            # Check categorical data
            if 'categorical_columns' in schema:
                validator = CategoricalSchemaValidator(schema['categorical_columns'])
                return validator.validate(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating pandas data: {e}")
            return False
    
    def _apply_custom_validation(self, data: Any, validation: Dict[str, Any]) -> bool:
        """Apply custom validation rule."""
        try:
            validation_type = validation.get('type')
            
            if validation_type == 'range_check':
                column = validation['column']
                min_val = validation.get('min')
                max_val = validation.get('max')
                
                if isinstance(data, pd.DataFrame):
                    values = data[column]
                else:
                    values = data[:, column]
                
                if min_val is not None and values.min() < min_val:
                    return False
                if max_val is not None and values.max() > max_val:
                    return False
            
            elif validation_type == 'uniqueness_check':
                column = validation['column']
                if isinstance(data, pd.DataFrame):
                    unique_count = data[column].nunique()
                    total_count = len(data)
                else:
                    unique_count = len(np.unique(data[:, column]))
                    total_count = len(data)
                
                min_unique_ratio = validation.get('min_unique_ratio', 0.0)
                if unique_count / total_count < min_unique_ratio:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying custom validation: {e}")
            return False
    
    def validate_global_compatibility(self, party_metadata: Dict[str, Dict[str, Any]]) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate compatibility across all parties for joint analysis.
        
        Args:
            party_metadata: Metadata from all parties
            
        Returns:
            Tuple of (is_compatible, global_metadata)
        """
        try:
            logger.info("Validating global compatibility across parties")
            
            global_metadata = {
                'total_parties': len(party_metadata),
                'total_samples': 0,
                'common_features': None,
                'compatible': True
            }
            
            # Check if all parties have compatible schemas
            schemas = []
            for party_id, metadata in party_metadata.items():
                if not metadata.get('validation_passed', False):
                    global_metadata['compatible'] = False
                    global_metadata['error'] = f"Party {party_id} failed validation"
                    return False, global_metadata
                
                schemas.append(metadata)
                global_metadata['total_samples'] += metadata['shape'][0]
            
            # Check feature compatibility
            if self.global_schema and 'require_same_features' in self.global_schema:
                if self.global_schema['require_same_features']:
                    first_schema = schemas[0]
                    feature_count = first_schema['shape'][1]
                    
                    for schema in schemas[1:]:
                        if schema['shape'][1] != feature_count:
                            global_metadata['compatible'] = False
                            global_metadata['error'] = "Inconsistent feature count across parties"
                            return False, global_metadata
                    
                    global_metadata['common_features'] = feature_count
            
            # Check minimum total samples
            if self.global_schema and 'min_total_samples' in self.global_schema:
                min_samples = self.global_schema['min_total_samples']
                if global_metadata['total_samples'] < min_samples:
                    global_metadata['compatible'] = False
                    global_metadata['error'] = f"Insufficient total samples: {global_metadata['total_samples']} < {min_samples}"
                    return False, global_metadata
            
            logger.info("Global compatibility validation passed")
            return True, global_metadata
            
        except Exception as e:
            logger.error(f"Error validating global compatibility: {e}")
            return False, {'error': str(e)}
    
    def get_validation_report(self, party_metadata: Dict[str, Dict[str, Any]], 
                            global_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive validation report.
        
        Args:
            party_metadata: Metadata from all parties
            global_metadata: Global compatibility metadata
            
        Returns:
            Comprehensive validation report
        """
        report = {
            'timestamp': pd.Timestamp.now().isoformat(),
            'global_status': global_metadata.get('compatible', False),
            'total_parties': len(party_metadata),
            'total_samples': global_metadata.get('total_samples', 0),
            'party_details': {},
            'recommendations': []
        }
        
        # Add party-specific details
        for party_id, metadata in party_metadata.items():
            report['party_details'][party_id] = {
                'validation_passed': metadata.get('validation_passed', False),
                'data_shape': metadata.get('shape', None),
                'missing_values': metadata.get('missing_values', 0),
                'data_type': metadata.get('data_type', 'unknown')
            }
        
        # Add recommendations
        if not global_metadata.get('compatible', False):
            report['recommendations'].append("Address validation errors before proceeding")
        
        if global_metadata.get('total_samples', 0) < 1000:
            report['recommendations'].append("Consider increasing sample size for better statistical power")
        
        return report