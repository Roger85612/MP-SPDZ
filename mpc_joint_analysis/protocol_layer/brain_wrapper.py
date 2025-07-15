"""
Brain Protocol Wrapper

Provides a wrapper for the Brain protocol in MP-SPDZ,
designed for three-party malicious secure computations over Z/2^k rings.
"""

import os
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass
from .mascot_wrapper import ProtocolWrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrainError(Exception):
    """Custom exception for Brain protocol errors."""
    pass

@dataclass
class BrainConfig:
    """Configuration for Brain protocol execution."""
    n_parties: int = 3  # Brain is fixed to 3 parties
    party_id: int = 0
    program_name: str = ""
    data_dir: str = "Player-Data"
    ssl_dir: str = "Player-Data"
    host: str = "localhost"
    port_base: int = 5000
    ring_size: int = 64  # 2^k ring size
    security_parameter: int = 40
    preprocessing_threads: int = 1
    online_threads: int = 1
    memory_limit_mb: int = 512
    timeout_seconds: int = 240
    use_preprocessing: bool = True
    debug_mode: bool = False
    use_edabits: bool = True  # Use edabits for efficient conversions
    
    def __post_init__(self):
        if self.n_parties != 3:
            raise BrainError("Brain protocol requires exactly 3 parties")
        if self.party_id >= 3:
            raise BrainError("Party ID must be 0, 1, or 2 for Brain protocol")
    
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
            'ring_size': self.ring_size,
            'security_parameter': self.security_parameter,
            'preprocessing_threads': self.preprocessing_threads,
            'online_threads': self.online_threads,
            'memory_limit_mb': self.memory_limit_mb,
            'timeout_seconds': self.timeout_seconds,
            'use_preprocessing': self.use_preprocessing,
            'debug_mode': self.debug_mode,
            'use_edabits': self.use_edabits
        }

class BrainWrapper(ProtocolWrapper):
    """Wrapper for Brain protocol execution."""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        """Initialize Brain wrapper."""
        self.mp_spdz_path = mp_spdz_path
        self.config = None
        self.temp_files = []
        self.process = None
        self._validate_installation()
    
    def _validate_installation(self):
        """Validate MP-SPDZ installation for Brain."""
        try:
            if not os.path.exists(self.mp_spdz_path):
                raise BrainError(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            # Check for Brain executables
            brain_exec = os.path.join(self.mp_spdz_path, "brain-party.x")
            
            if not os.path.exists(brain_exec):
                logger.warning("Brain executable not found - may need compilation")
            
            logger.info("Brain protocol installation validated")
            
        except Exception as e:
            logger.error(f"Error validating Brain installation: {e}")
            raise BrainError(f"Invalid Brain installation: {e}")
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Setup Brain protocol environment."""
        try:
            self.config = BrainConfig(**config)
            
            # Setup directories
            self._setup_directories()
            self._setup_ssl_certificates()
            self._setup_input_files()
            
            logger.info("Brain protocol environment setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up Brain environment: {e}")
            raise BrainError(f"Failed to setup Brain environment: {e}")
    
    def _setup_directories(self):
        """Setup required directories."""
        directories = [
            self.config.data_dir,
            self.config.ssl_dir,
            "Programs/Bytecode",
            "Programs/Schedules"
        ]
        
        for directory in directories:
            dir_path = os.path.join(self.mp_spdz_path, directory)
            os.makedirs(dir_path, exist_ok=True)
    
    def _setup_ssl_certificates(self):
        """Setup SSL certificates for secure communication."""
        try:
            ssl_dir = os.path.join(self.mp_spdz_path, self.config.ssl_dir)
            cert_file = os.path.join(ssl_dir, f"P{self.config.party_id}.pem")
            
            if not os.path.exists(cert_file):
                setup_script = os.path.join(self.mp_spdz_path, "Scripts/setup-ssl.sh")
                if os.path.exists(setup_script):
                    cmd = [setup_script, str(self.config.n_parties), ssl_dir]
                    subprocess.run(cmd, cwd=self.mp_spdz_path, check=True)
                    logger.info("SSL certificates generated for Brain")
                else:
                    logger.warning("SSL setup script not found")
            
        except Exception as e:
            logger.error(f"Error setting up SSL certificates: {e}")
            raise BrainError(f"Failed to setup SSL certificates: {e}")
    
    def _setup_input_files(self):
        """Setup input data files."""
        data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
        
        for party_id in range(self.config.n_parties):
            input_file = os.path.join(data_dir, f"Input-P{party_id}-0")
            if not os.path.exists(input_file):
                with open(input_file, 'w') as f:
                    f.write("0\n")
    
    def compile_program(self, program_path: str, output_path: Optional[str] = None) -> None:
        """Compile MPC program for Brain."""
        try:
            if not os.path.exists(program_path):
                raise BrainError(f"Program file not found: {program_path}")
            
            compile_script = os.path.join(self.mp_spdz_path, "compile.py")
            cmd = [
                "python3", compile_script,
                "-R", str(self.config.ring_size),  # Use ring size for Z/2^k
                program_path
            ]
            
            if self.config.use_edabits:
                cmd.append("-e")  # Enable edabits for efficient conversions
            
            logger.info(f"Compiling program for Brain (ring size {self.config.ring_size}): {program_path}")
            result = subprocess.run(cmd, cwd=self.mp_spdz_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                raise BrainError(f"Compilation failed: {result.stderr}")
            
            logger.info("Program compiled successfully for Brain")
            
        except Exception as e:
            logger.error(f"Error compiling program: {e}")
            raise BrainError(f"Failed to compile program: {e}")
    
    def run_preprocessing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Brain protocol includes preprocessing in the online phase."""
        if not self.config.use_preprocessing:
            return {'status': 'skipped', 'message': 'Preprocessing disabled'}
        
        return {
            'status': 'integrated',
            'message': 'Brain preprocessing is integrated into online phase',
            'duration': 0
        }
    
    def run_online(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Brain online phase (includes preprocessing)."""
        try:
            brain_exec = os.path.join(self.mp_spdz_path, "brain-party.x")
            if not os.path.exists(brain_exec):
                raise BrainError("Brain executable not found: brain-party.x")
            
            start_time = time.time()
            
            cmd = [
                brain_exec,
                "-p", str(self.config.party_id),
                "-N", str(self.config.n_parties),
                "-h", self.config.host,
                "-pn", str(self.config.port_base),
                self.config.program_name
            ]
            
            if self.config.debug_mode:
                cmd.append("-v")
            
            if self.config.use_edabits:
                cmd.append("-e")
            
            # Add memory limit
            cmd.extend(["-m", str(self.config.memory_limit_mb)])
            
            logger.info(f"Running Brain online phase for party {self.config.party_id}")
            
            result = subprocess.run(cmd, cwd=self.mp_spdz_path,
                                  capture_output=True, text=True,
                                  timeout=self.config.timeout_seconds)
            
            end_time = time.time()
            
            if result.returncode != 0:
                logger.error(f"Brain online phase failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'duration': end_time - start_time
                }
            
            results = self._parse_online_output(result.stdout)
            
            logger.info("Brain online phase completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout,
                'results': results
            }
            
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Brain online phase timed out'}
        except Exception as e:
            logger.error(f"Error running Brain online phase: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _parse_online_output(self, output: str) -> Dict[str, Any]:
        """Parse Brain online output."""
        results = {
            'computation_results': [],
            'timing_info': {},
            'communication_stats': {}
        }
        
        lines = output.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('Result:') or line.startswith('Output:'):
                result_value = line.split(':', 1)[1].strip()
                results['computation_results'].append(result_value)
        
        return results
    
    def get_protocol_info(self) -> Dict[str, Any]:
        """Get Brain protocol information."""
        return {
            'protocol_name': 'Brain',
            'security_model': 'malicious',
            'adversary_model': 'honest_majority',
            'computation_domain': 'ring_2k',
            'min_parties': 3,
            'max_parties': 3,
            'supports_preprocessing': True,
            'supports_online_only': True,
            'features': [
                'Malicious security',
                'Honest majority (exactly 3 parties)',
                'Ring Z/2^k arithmetic',
                'Integer computations',
                'Integrated preprocessing',
                'Edabits for efficient conversions',
                'Constant round complexity'
            ],
            'typical_use_cases': [
                'Three-party secure computations',
                'Malicious security with honest majority',
                'Integer arithmetic with security',
                'Moderate security requirements',
                'Applications requiring exactly 3 parties',
                'Secure multi-party integer operations'
            ]
        }
    
    def cleanup(self):
        """Clean up Brain wrapper resources."""
        try:
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
            
            logger.info("Brain wrapper cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def estimate_resources(self, computation_size: Dict[str, int]) -> Dict[str, Any]:
        """Estimate resources for Brain computation."""
        n_multiplications = computation_size.get('multiplications', 1000)
        n_additions = computation_size.get('additions', 5000)
        n_parties = 3  # Brain is fixed to 3 parties
        
        # Brain has integrated preprocessing so we estimate total time
        total_time = n_multiplications * 0.0008 + n_additions * 0.00008
        
        total_memory = n_multiplications * 0.0008 + 60
        
        total_network = n_multiplications * 0.8 * n_parties
        
        return {
            'time_estimates': {
                'preprocessing_seconds': 0,  # Integrated
                'online_seconds': total_time,
                'total_seconds': total_time
            },
            'memory_estimates': {
                'preprocessing_mb': 0,  # Integrated
                'online_mb': total_memory,
                'peak_mb': total_memory
            },
            'network_estimates': {
                'preprocessing_kb': 0,  # Integrated
                'online_kb': total_network,
                'total_kb': total_network
            },
            'brain_specific': {
                'parties': 3,
                'malicious_security': True,
                'honest_majority': True,
                'integrated_preprocessing': True,
                'edabits_support': self.config.use_edabits
            }
        }
    
    def validate_setup(self) -> Tuple[bool, List[str]]:
        """Validate Brain-specific setup requirements."""
        issues = []
        
        try:
            # Check MP-SPDZ installation
            if not os.path.exists(self.mp_spdz_path):
                issues.append(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            # Check Brain executable
            brain_exec = os.path.join(self.mp_spdz_path, "brain-party.x")
            if not os.path.exists(brain_exec):
                issues.append("Brain executable not found: brain-party.x")
            
            # Check configuration
            if not self.config:
                issues.append("Configuration not initialized")
            else:
                if self.config.n_parties != 3:
                    issues.append("Brain protocol requires exactly 3 parties")
                if self.config.party_id >= 3:
                    issues.append("Party ID must be 0, 1, or 2 for Brain protocol")
                if self.config.ring_size not in [32, 64, 128]:
                    issues.append(f"Invalid ring size: {self.config.ring_size}")
            
            # Check directories
            if self.config:
                data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
                if not os.path.exists(data_dir):
                    issues.append(f"Data directory not found: {data_dir}")
            
            return len(issues) == 0, issues
            
        except Exception as e:
            issues.append(f"Error during validation: {e}")
            return False, issues