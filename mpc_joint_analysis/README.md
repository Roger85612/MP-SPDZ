# MPC-Based Joint Data Analysis System

A secure multi-party computation system that enables multiple parties to perform joint data analysis while keeping their individual datasets private. Built on the MP-SPDZ framework.

## Features

- **Privacy-Preserving Analytics**: Perform statistical analysis, machine learning, and data mining without revealing individual data
- **Multi-Protocol Support**: Automatic selection of optimal MPC protocols based on security requirements and performance needs
- **Flexible Data Ingestion**: Support for various data formats and external client interfaces
- **Comprehensive Security**: SSL/TLS communication, authentication, access control, and audit logging
- **Scalable Architecture**: Designed to handle large datasets and multiple parties efficiently

## System Architecture

```
mpc_joint_analysis/
├── data_ingestion/          # Data input validation and preprocessing
├── analytics/               # Statistical analysis and ML modules
├── protocol_layer/          # MPC protocol selection and wrappers
├── security/               # Authentication, access control, and auditing
├── results/                # Result aggregation and visualization
├── mpc_programs/           # MPC program implementations
├── config/                 # Configuration files
├── deployment/             # Deployment scripts and containers
├── scripts/                # Utility scripts
├── tests/                  # Unit and integration tests
├── docs/                   # Documentation
└── web_dashboard/          # Web-based monitoring interface
```

## Quick Start

1. **Setup Environment**:
   ```bash
   # Make sure MP-SPDZ is properly installed
   cd /path/to/MP-SPDZ
   make setup
   ```

2. **Configure System**:
   ```bash
   cp config/protocol_configs.yaml.example config/protocol_configs.yaml
   # Edit configuration files as needed
   ```

3. **Run Example Analysis**:
   ```bash
   # Setup SSL certificates
   Scripts/setup-ssl.sh 3
   
   # Run joint statistics analysis
   python3 -m mpc_joint_analysis.scripts.run_analysis \
     --protocol mascot \
     --parties 3 \
     --analysis joint_statistics \
     --config config/protocol_configs.yaml
   ```

## Supported Analytics

- **Statistical Analysis**: Mean, median, variance, correlation, hypothesis testing
- **Machine Learning**: Linear/logistic regression, neural networks, clustering
- **Data Mining**: Association rules, decision trees, pattern discovery
- **Custom Analysis**: Extensible framework for custom MPC computations

## Security Features

- **Cryptographic Security**: Based on proven MPC protocols
- **Access Control**: Role-based permissions and authentication
- **Audit Logging**: Complete audit trail of all operations
- **Differential Privacy**: Optional noise addition for additional privacy protection

## Documentation

- [User Guide](docs/user_guide/README.md) - Complete user documentation
- [API Reference](docs/api/README.md) - Developer API documentation
- [Examples](docs/examples/README.md) - Working examples and tutorials

## Contributing

Please read our contributing guidelines and code of conduct before submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.