# MPC Joint Analysis System - Setup and Usage Guide

## 📋 System Overview

This is a comprehensive Multi-Party Computation (MPC) system for joint data analysis that provides:

- **Secure Multi-Party Computation**: Privacy-preserving analytics across multiple parties
- **Protocol Flexibility**: Support for various MPC protocols (MASCOT, Shamir, Atlas, etc.)
- **Comprehensive Security**: Authentication, authorization, and audit logging
- **Privacy Protection**: Differential privacy, k-anonymity, and other privacy mechanisms
- **Analytics Engine**: Statistics, machine learning, and data mining capabilities

## 🛠️ Prerequisites

### Required Software
1. **MP-SPDZ Framework** (already available at `/mnt/c/Users/Lenovo/source/repos/MP-SPDZ`)
2. **Python 3.7+** with the following packages:
   ```bash
   pip install numpy pandas matplotlib seaborn scipy cryptography pyyaml
   ```

### System Requirements
- Linux/Unix environment (WSL2 is fine)
- At least 4GB RAM
- Network connectivity for multi-party scenarios

## 📁 Directory Structure

```
mpc_joint_analysis/
├── config/                     # Configuration files
│   └── system_config.yaml      # Main system configuration
├── data_ingestion/             # Data input and validation
│   ├── input_validator.py      # Input validation and quality checks
│   ├── preprocessing.py        # Data preprocessing and normalization
│   └── client_interface.py     # REST API for parties
├── analytics/                  # Analysis modules
│   ├── statistics.py          # Statistical analysis
│   ├── machine_learning.py    # ML algorithms
│   └── data_mining.py         # Data mining techniques
├── protocol_layer/            # MPC protocol management
│   ├── protocol_selector.py   # Intelligent protocol selection
│   ├── mascot_wrapper.py      # MASCOT protocol wrapper
│   ├── shamir_wrapper.py      # Shamir secret sharing
│   ├── atlas_wrapper.py       # Atlas protocol
│   ├── semi_wrapper.py        # Semi protocol
│   ├── semi2k_wrapper.py      # Semi2K protocol
│   └── brain_wrapper.py       # Brain protocol
├── security/                  # Security components
│   ├── authentication.py     # Party authentication
│   ├── access_control.py     # Role-based access control
│   └── audit_logger.py       # Comprehensive audit logging
├── results/                   # Results processing
│   ├── aggregator.py         # Secure result aggregation
│   ├── privacy_filter.py     # Privacy filtering mechanisms
│   └── visualizer.py         # Privacy-aware visualization
├── mpc_programs/             # MPC computation programs
│   └── joint_statistics.mpc  # Joint statistics computation
├── run_demo.py               # System demonstration
└── SETUP_AND_USAGE.md       # This file
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Navigate to the system directory
cd /mnt/c/Users/Lenovo/source/repos/MP-SPDZ/mpc_joint_analysis

# Install Python dependencies
pip3 install numpy pandas matplotlib seaborn scipy cryptography pyyaml
```

### 2. Compile MPC Programs
```bash
# Navigate to MP-SPDZ root
cd /mnt/c/Users/Lenovo/source/repos/MP-SPDZ

# Compile the joint statistics program
python3 compile.py mpc_joint_analysis/mpc_programs/joint_statistics.mpc

# This will create compiled bytecode in Programs/Bytecode/
```

### 3. Run System Components

#### A. Start Security Components
```python
from security import AuthenticationManager, AccessControlManager, AuditLogger
import yaml

# Load configuration
with open('config/system_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize security components
auth_manager = AuthenticationManager(config['security'])
access_manager = AccessControlManager(config['security'])
audit_logger = AuditLogger(config['security'])

# Register parties
for i in range(3):
    party = auth_manager.register_party(
        party_id=i,
        name=f"Party_{i}",
        ip_address="127.0.0.1",
        port=5000 + i
    )
    print(f"Registered {party.name}")
```

#### B. Data Ingestion and Validation
```python
from data_ingestion import InputValidator, DataPreprocessor
import pandas as pd

# Initialize components
validator = InputValidator(config['data_processing'])
preprocessor = DataPreprocessor(config['data_processing'])

# Sample data for each party
party_data = {
    0: pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]}),
    1: pd.DataFrame({'x': [2, 3, 4], 'y': [5, 6, 7]}),
    2: pd.DataFrame({'x': [3, 4, 5], 'y': [6, 7, 8]})
}

# Validate and preprocess
for party_id, data in party_data.items():
    # Convert to validation format
    data_dict = {'data': data.to_dict('records')}
    
    # Validate
    validation = validator.validate_input(data_dict, party_id)
    print(f"Party {party_id} validation: {validation['valid']}")
    
    # Preprocess
    processed = preprocessor.preprocess(data.to_dict('records'))
    print(f"Party {party_id} processed: {len(processed)} records")
```

#### C. Protocol Selection and Execution
```python
from protocol_layer import ProtocolSelector, MascotWrapper

# Initialize protocol selector
selector = ProtocolSelector(config)

# Define computation requirements
requirements = {
    'n_parties': 3,
    'security_model': 'malicious',
    'performance_priority': 'security',
    'computation_type': 'arithmetic'
}

# Select optimal protocol
protocol, metadata = selector.select_protocol(requirements)
print(f"Selected protocol: {protocol.value}")
print(f"Selection score: {metadata['selection_score']:.3f}")

# Initialize protocol wrapper
if protocol.value == 'mascot':
    wrapper = MascotWrapper()
    wrapper.setup({
        'n_parties': 3,
        'party_id': 0,  # This would be different for each party
        'program_name': 'joint_statistics'
    })
```

### 4. Run MPC Computation

#### A. Prepare Input Data
```bash
# Create input files for each party in MP-SPDZ format
# Party 0 input (Input-P0-0):
echo "1.5 2.3 3.1" > Player-Data/Input-P0-0

# Party 1 input (Input-P1-0):
echo "2.1 3.4 4.2" > Player-Data/Input-P1-0

# Party 2 input (Input-P2-0):
echo "1.8 2.9 3.7" > Player-Data/Input-P2-0
```

#### B. Execute MPC Computation
```bash
# Navigate to MP-SPDZ root
cd /mnt/c/Users/Lenovo/source/repos/MP-SPDZ

# Run the computation (example with MASCOT protocol)
# Terminal 1 (Party 0):
./mascot-party.x -p 0 -N 3 joint_statistics

# Terminal 2 (Party 1):
./mascot-party.x -p 1 -N 3 joint_statistics

# Terminal 3 (Party 2):
./mascot-party.x -p 2 -N 3 joint_statistics
```

### 5. Process Results
```python
from results import SecureAggregator, PrivacyFilter
from results.aggregator import ComputationResult, ResultType, AggregationRequest, AggregationType

# Initialize results processing
aggregator = SecureAggregator(config['results'])
privacy_filter = PrivacyFilter(config['privacy'])

# Add computation results from parties
for party_id in range(3):
    result = ComputationResult(
        party_id=party_id,
        computation_id="joint_stats_demo",
        result_type=ResultType.STATISTICAL,
        data={'mean': 2.5 + party_id * 0.1, 'std': 1.2},
        quality_score=0.95,
        confidence=0.9
    )
    aggregator.add_result(result)

# Aggregate results
request = AggregationRequest(
    request_id="demo_agg",
    computation_id="joint_stats_demo",
    aggregation_type=AggregationType.MEAN,
    party_ids=[0, 1, 2]
)

aggregated = aggregator.aggregate_results(request)
print(f"Aggregated result: {aggregated.result}")

# Apply privacy filtering
filtered = privacy_filter.filter_result(aggregated.result, 'statistical')
print(f"Privacy-filtered result: {filtered}")
```

## 📊 Available MPC Programs

### 1. Joint Statistics (`joint_statistics.mpc`)
Computes secure statistics across multiple parties:
- **Secure Mean**: Aggregate mean without revealing individual values
- **Secure Variance**: Population and sample variance
- **Secure Correlation**: Pearson correlation coefficients
- **Secure Quantiles**: Median, quartiles, percentiles
- **Secure Histograms**: Frequency distributions
- **Covariance Matrix**: Multi-variable covariance analysis

**Usage:**
```bash
python3 compile.py mpc_joint_analysis/mpc_programs/joint_statistics.mpc
./mascot-party.x -p PARTY_ID -N NUM_PARTIES joint_statistics
```

## 🔧 Configuration

### Protocol Configuration
Edit `config/system_config.yaml` to customize:
- Protocol preferences
- Security parameters
- Privacy settings
- Network configuration

### Security Settings
- **Authentication**: Certificate-based party authentication
- **Access Control**: Role-based permissions
- **Audit Logging**: Comprehensive activity logging

### Privacy Settings
- **Differential Privacy**: Configurable ε and δ parameters
- **K-Anonymity**: Minimum group size requirements
- **Result Filtering**: Automatic privacy protection

## 🚨 Security Considerations

1. **Certificate Management**: Use proper SSL certificates in production
2. **Network Security**: Ensure secure communication channels
3. **Data Isolation**: Keep party data separate until computation
4. **Audit Trails**: Monitor all system activities
5. **Privacy Budget**: Track differential privacy usage

## 🔍 Monitoring and Debugging

### Logging
- System logs: `demo.log`
- Audit logs: `audit_logs/`
- Protocol logs: Check MP-SPDZ output

### Performance Monitoring
```python
# Get system statistics
stats = aggregator.get_statistics()
audit_stats = audit_logger.get_statistics()
privacy_stats = privacy_filter.get_privacy_statistics()

print("System Performance:")
print(f"Total computations: {stats['total_computations']}")
print(f"Total audit events: {audit_stats['total_events']}")
print(f"Privacy budget used: {privacy_stats['privacy_budget_status']}")
```

## 🎯 Example Use Cases

1. **Healthcare Research**: Joint analysis of patient data across hospitals
2. **Financial Analytics**: Risk assessment across multiple banks
3. **Market Research**: Consumer behavior analysis across companies
4. **Scientific Collaboration**: Research data sharing without disclosure
5. **Government Statistics**: Census and survey data aggregation

## 📈 Next Steps

1. **Scale Testing**: Test with larger datasets and more parties
2. **Performance Optimization**: Tune protocol parameters
3. **Custom Analytics**: Implement domain-specific algorithms
4. **Integration**: Connect with existing data systems
5. **Deployment**: Set up production infrastructure

---

For more detailed information, see the individual module documentation in each directory.