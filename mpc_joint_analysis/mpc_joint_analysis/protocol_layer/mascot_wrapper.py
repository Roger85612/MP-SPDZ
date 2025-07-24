"""
MASCOT Protocol Wrapper

Provides a wrapper for the MASCOT protocol in MP-SPDZ, handling setup,
execution, and result processing for malicious security with dishonest majority.
"""

import os
import subprocess
import tempfile
import logging
from typing import Dict, List, Any, Optional, Tuple
import json
import time
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MascotError(Exception):
    """Custom exception for MASCOT protocol errors."""
    pass

@dataclass
class MascotConfig:
    """Configuration for MASCOT protocol execution."""
    n_parties: int
    party_id: int
    program_name: str
    data_dir: str = "Player-Data"
    ssl_dir: str = "Player-Data"
    host: str = "localhost"
    port_base: int = 5000
    field_size: int = 64
    security_parameter: int = 40
    preprocessing_threads: int = 1
    online_threads: int = 1
    memory_limit_mb: int = 1024
    timeout_seconds: int = 300
    use_preprocessing: bool = True
    debug_mode: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'n_parties': self.n_parties,
            'party_id': self.party_id,
            'program_name': self.program_name,
            'data_dir': self.data_dir,
            'ssl_dir': self.ssl_dir,
            'host': self.host,
            'port_base': self.port_base,
            'field_size': self.field_size,
            'security_parameter': self.security_parameter,
            'preprocessing_threads': self.preprocessing_threads,
            'online_threads': self.online_threads,
            'memory_limit_mb': self.memory_limit_mb,
            'timeout_seconds': self.timeout_seconds,
            'use_preprocessing': self.use_preprocessing,
            'debug_mode': self.debug_mode
        }

class ProtocolWrapper(ABC):
    """Abstract base class for protocol wrappers."""
    
    @abstractmethod
    def setup(self, config: Dict[str, Any]) -> None:
        """Setup the protocol environment."""
        pass
    
    @abstractmethod
    def compile_program(self, program_path: str, output_path: str) -> None:
        """Compile MPC program."""
        pass
    
    @abstractmethod
    def run_preprocessing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run preprocessing phase."""
        pass
    
    @abstractmethod
    def run_online(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run online phase."""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Clean up resources."""
        pass

class MascotWrapper(ProtocolWrapper):
    """Wrapper for MASCOT protocol execution."""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        """
        Initialize MASCOT wrapper.
        
        Args:
            mp_spdz_path: Path to MP-SPDZ installation
        """
        self.mp_spdz_path = mp_spdz_path
        self.config = None
        self.temp_files = []
        self.process = None
        
        # Validate MP-SPDZ installation
        self._validate_installation()
    
    def _validate_installation(self):
        """Validate MP-SPDZ installation."""
        try:
            # Check if MP-SPDZ directory exists
            if not os.path.exists(self.mp_spdz_path):
                raise MascotError(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            # Check for required executables
            required_files = [
                "mascot-party.x",
                "mascot-offline.x",
                "compile.py"
            ]
            
            for file_name in required_files:
                file_path = os.path.join(self.mp_spdz_path, file_name)
                if not os.path.exists(file_path):
                    logger.warning(f"Required file not found: {file_path}")
            
            logger.info("MP-SPDZ installation validated")
            
        except Exception as e:
            logger.error(f"Error validating MP-SPDZ installation: {e}")
            raise MascotError(f"Invalid MP-SPDZ installation: {e}")
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Setup MASCOT protocol environment."""
        try:
            # Create MascotConfig from dictionary
            self.config = MascotConfig(**config)
            
            # Setup directories
            self._setup_directories()
            
            # Setup SSL certificates if needed
            self._setup_ssl_certificates()
            
            # Setup input data files
            self._setup_input_files()
            
            logger.info("MASCOT protocol environment setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up MASCOT environment: {e}")
            raise MascotError(f"Failed to setup MASCOT environment: {e}")
    
    def _setup_directories(self):
        """Setup required directories."""
        try:
            directories = [
                self.config.data_dir,
                self.config.ssl_dir,
                "Programs/Bytecode",
                "Programs/Schedules"
            ]
            
            for directory in directories:
                dir_path = os.path.join(self.mp_spdz_path, directory)
                os.makedirs(dir_path, exist_ok=True)
            
            logger.info("Directories setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up directories: {e}")
            raise MascotError(f"Failed to setup directories: {e}")
    
    def _setup_ssl_certificates(self):
        """Setup SSL certificates for secure communication."""
        try:
            ssl_dir = os.path.join(self.mp_spdz_path, self.config.ssl_dir)
            
            # Check if certificates already exist
            cert_file = os.path.join(ssl_dir, f"P{self.config.party_id}.pem")
            if os.path.exists(cert_file):
                logger.info("SSL certificates already exist")
                return
            
            # Generate certificates using MP-SPDZ script
            setup_script = os.path.join(self.mp_spdz_path, "Scripts/setup-ssl.sh")
            if os.path.exists(setup_script):
                cmd = [setup_script, str(self.config.n_parties), ssl_dir]
                result = subprocess.run(cmd, cwd=self.mp_spdz_path, 
                                      capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.warning(f"SSL setup script failed: {result.stderr}")
                else:
                    logger.info("SSL certificates generated successfully")
            else:
                logger.warning("SSL setup script not found - certificates may need manual setup")
                
        except Exception as e:
            logger.error(f"Error setting up SSL certificates: {e}")
            raise MascotError(f"Failed to setup SSL certificates: {e}")
    
    def _setup_input_files(self):
        """Setup input data files for the protocol."""
        try:
            data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
            
            # Create placeholder input files if they don't exist
            for party_id in range(self.config.n_parties):
                input_file = os.path.join(data_dir, f"Input-P{party_id}-0")
                if not os.path.exists(input_file):
                    with open(input_file, 'w') as f:
                        f.write("0\n")  # Placeholder input
            
            logger.info("Input files setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up input files: {e}")
            raise MascotError(f"Failed to setup input files: {e}")
    
    def compile_program(self, program_path: str, output_path: Optional[str] = None) -> None:
        """Compile MPC program for MASCOT."""
        try:
            if not os.path.exists(program_path):
                raise MascotError(f"Program file not found: {program_path}")
            
            # Determine output path
            if output_path is None:
                program_name = os.path.splitext(os.path.basename(program_path))[0]
                output_path = os.path.join(self.mp_spdz_path, "Programs/Bytecode", f"{program_name}.bc")
            
            # Compile command
            compile_script = os.path.join(self.mp_spdz_path, "compile.py")
            cmd = [
                "python3", compile_script,
                "-F", str(self.config.field_size),
                program_path
            ]
            
            logger.info(f"Compiling program: {program_path}")
            result = subprocess.run(cmd, cwd=self.mp_spdz_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Compilation failed: {result.stderr}")
                raise MascotError(f"Program compilation failed: {result.stderr}")
            
            logger.info(f"Program compiled successfully: {output_path}")
            
        except Exception as e:
            logger.error(f"Error compiling program: {e}")
            raise MascotError(f"Failed to compile program: {e}")
    
    def run_preprocessing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run MASCOT preprocessing phase."""
        try:
            if not self.config.use_preprocessing:
                return {'status': 'skipped', 'message': 'Preprocessing disabled'}
            
            # Check if preprocessing executable exists
            preprocessing_exec = os.path.join(self.mp_spdz_path, "mascot-offline.x")
            if not os.path.exists(preprocessing_exec):
                logger.warning("Preprocessing executable not found - skipping preprocessing")
                return {'status': 'skipped', 'message': 'Preprocessing executable not found'}
            
            start_time = time.time()
            
            # Build preprocessing command
            cmd = [
                preprocessing_exec,
                "-p", str(self.config.party_id),
                "-N", str(self.config.n_parties),
                "-h", self.config.host,
                "-pn", str(self.config.port_base),
                "-c"  # Generate triples
            ]
            
            if self.config.debug_mode:
                cmd.append("-v")
            
            logger.info(f"Running MASCOT preprocessing for party {self.config.party_id}")
            
            # Run preprocessing
            result = subprocess.run(cmd, cwd=self.mp_spdz_path,
                                  capture_output=True, text=True,
                                  timeout=self.config.timeout_seconds)
            
            end_time = time.time()
            
            if result.returncode != 0:
                logger.error(f"Preprocessing failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'duration': end_time - start_time
                }
            
            logger.info("MASCOT preprocessing completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Preprocessing timeout")
            return {'status': 'timeout', 'message': 'Preprocessing timed out'}
        except Exception as e:
            logger.error(f"Error running preprocessing: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def run_online(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run MASCOT online phase."""
        try:
            # Check if online executable exists
            online_exec = os.path.join(self.mp_spdz_path, "mascot-party.x")
            if not os.path.exists(online_exec):
                raise MascotError("Online executable not found: mascot-party.x")
            
            start_time = time.time()
            
            # Build online command
            cmd = [
                online_exec,
                "-p", str(self.config.party_id),
                "-N", str(self.config.n_parties),
                "-h", self.config.host,
                "-pn", str(self.config.port_base),
                self.config.program_name
            ]
            
            if self.config.use_preprocessing:
                cmd.append("-F")  # Read preprocessing from files
            
            if self.config.debug_mode:
                cmd.append("-v")
            
            # Add memory limit
            cmd.extend(["-m", str(self.config.memory_limit_mb)])
            
            logger.info(f"Running MASCOT online phase for party {self.config.party_id}")
            
            # Run online phase
            result = subprocess.run(cmd, cwd=self.mp_spdz_path,
                                  capture_output=True, text=True,
                                  timeout=self.config.timeout_seconds)
            
            end_time = time.time()
            
            if result.returncode != 0:
                logger.error(f"Online phase failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'duration': end_time - start_time
                }
            
            # Parse output for results
            results = self._parse_online_output(result.stdout)
            
            logger.info("MASCOT online phase completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout,
                'results': results
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Online phase timeout")
            return {'status': 'timeout', 'message': 'Online phase timed out'}
        except Exception as e:
            logger.error(f"Error running online phase: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _parse_online_output(self, output: str) -> Dict[str, Any]:
        """Parse output from online phase to extract results."""
        try:
            results = {
                'computation_results': [],
                'timing_info': {},
                'communication_stats': {}
            }
            
            lines = output.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Extract computation results
                if line.startswith('Result:') or line.startswith('Output:'):
                    result_value = line.split(':', 1)[1].strip()
                    results['computation_results'].append(result_value)
                
                # Extract timing information
                elif 'Time:' in line or 'Duration:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        key = parts[0].strip().lower().replace(' ', '_')
                        value = parts[1].strip()
                        results['timing_info'][key] = value
                
                # Extract communication statistics
                elif 'Sent:' in line or 'Received:' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        key = parts[0].strip().lower().replace(' ', '_')
                        value = parts[1].strip()
                        results['communication_stats'][key] = value
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing online output: {e}")
            return {'parse_error': str(e)}
    
    def run_complete_protocol(self, program_path: str, party_inputs: Dict[int, List[Any]]) -> Dict[str, Any]:
        """Run complete MASCOT protocol (preprocessing + online)."""
        try:
            logger.info("Starting complete MASCOT protocol execution")
            
            # Setup input files
            self._setup_party_inputs(party_inputs)
            
            # Compile program
            program_name = os.path.splitext(os.path.basename(program_path))[0]
            self.config.program_name = program_name
            self.compile_program(program_path)
            
            # Run preprocessing if enabled
            preprocessing_result = None
            if self.config.use_preprocessing:
                preprocessing_result = self.run_preprocessing({})
                if preprocessing_result['status'] != 'success':
                    return {
                        'status': 'failed',
                        'phase': 'preprocessing',
                        'result': preprocessing_result
                    }
            
            # Run online phase
            online_result = self.run_online({})
            
            # Combine results
            complete_result = {
                'status': online_result['status'],
                'preprocessing': preprocessing_result,
                'online': online_result,
                'total_duration': (preprocessing_result.get('duration', 0) + 
                                 online_result.get('duration', 0) if preprocessing_result else 
                                 online_result.get('duration', 0))
            }
            
            logger.info("Complete MASCOT protocol execution finished")
            return complete_result
            
        except Exception as e:
            logger.error(f"Error running complete protocol: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _setup_party_inputs(self, party_inputs: Dict[int, List[Any]]):
        """Setup input files for each party."""
        try:
            data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
            
            for party_id, inputs in party_inputs.items():
                input_file = os.path.join(data_dir, f"Input-P{party_id}-0")
                
                with open(input_file, 'w') as f:
                    for input_value in inputs:
                        f.write(f"{input_value}\n")
                
                logger.info(f"Setup input file for party {party_id}: {len(inputs)} values")
                
        except Exception as e:
            logger.error(f"Error setting up party inputs: {e}")
            raise MascotError(f"Failed to setup party inputs: {e}")
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get information about the MASCOT protocol."""
        return {
            'protocol_name': 'MASCOT',
            'security_model': 'malicious',
            'adversary_model': 'dishonest_majority',
            'computation_domain': 'field_prime',
            'min_parties': 2,
            'max_parties': None,
            'supports_preprocessing': True,
            'supports_online_only': True,
            'features': [
                'Malicious security',
                'Dishonest majority',
                'Field arithmetic',
                'OT-based preprocessing',
                'High performance'
            ],
            'typical_use_cases': [
                'Financial computations',
                'Machine learning',
                'Statistical analysis',
                'General arithmetic MPC'
            ]
        }
    
    def estimate_resources(self, computation_size: Dict[str, int]) -> Dict[str, Any]:
        """Estimate resource requirements for given computation size."""
        try:
            # Extract computation parameters
            n_multiplications = computation_size.get('multiplications', 1000)
            n_additions = computation_size.get('additions', 5000)
            n_parties = computation_size.get('parties', self.config.n_parties)
            
            # Estimate based on MASCOT characteristics
            # These are rough estimates based on typical MASCOT performance
            
            # Time estimates (seconds)
            preprocessing_time = n_multiplications * 0.001  # 1ms per multiplication
            online_time = n_multiplications * 0.0001 + n_additions * 0.00001
            
            # Memory estimates (MB)
            preprocessing_memory = n_multiplications * 0.001  # 1KB per multiplication
            online_memory = n_multiplications * 0.0001 + 50  # Base memory + computation
            
            # Network estimates (KB)
            preprocessing_network = n_multiplications * 0.5 * n_parties  # Per party
            online_network = n_multiplications * 0.1 * n_parties
            
            return {
                'time_estimates': {
                    'preprocessing_seconds': preprocessing_time,
                    'online_seconds': online_time,
                    'total_seconds': preprocessing_time + online_time
                },
                'memory_estimates': {
                    'preprocessing_mb': preprocessing_memory,
                    'online_mb': online_memory,
                    'peak_mb': max(preprocessing_memory, online_memory)
                },
                'network_estimates': {
                    'preprocessing_kb': preprocessing_network,
                    'online_kb': online_network,
                    'total_kb': preprocessing_network + online_network
                },
                'computation_parameters': {
                    'multiplications': n_multiplications,
                    'additions': n_additions,
                    'parties': n_parties
                }
            }
            
        except Exception as e:
            logger.error(f"Error estimating resources: {e}")
            return {'error': str(e)}
    
    def cleanup(self):
        """Clean up temporary files and resources."""
        try:
            # Clean up temporary files
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            # Terminate any running processes
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
            
            logger.info("MASCOT wrapper cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the MASCOT wrapper."""
        status = {
            'initialized': self.config is not None,
            'mp_spdz_path': self.mp_spdz_path,
            'temp_files': len(self.temp_files),
            'process_running': self.process is not None and self.process.poll() is None
        }
        
        if self.config:
            status['config'] = self.config.to_dict()
        
        return status
    
    def validate_setup(self) -> Tuple[bool, List[str]]:
        """Validate that the setup is correct for MASCOT execution."""
        issues = []
        
        try:
            # Check MP-SPDZ installation
            if not os.path.exists(self.mp_spdz_path):
                issues.append(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            # Check executables
            executables = ["mascot-party.x", "compile.py"]
            for exe in executables:
                exe_path = os.path.join(self.mp_spdz_path, exe)
                if not os.path.exists(exe_path):
                    issues.append(f"Required executable not found: {exe}")
            
            # Check configuration
            if not self.config:
                issues.append("Configuration not initialized")
            else:
                if self.config.n_parties < 2:
                    issues.append("Number of parties must be at least 2")
                if self.config.party_id >= self.config.n_parties:
                    issues.append("Party ID must be less than number of parties")
            
            # Check directories
            if self.config:
                data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
                if not os.path.exists(data_dir):
                    issues.append(f"Data directory not found: {data_dir}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Error during validation: {e}")
            return False, issues