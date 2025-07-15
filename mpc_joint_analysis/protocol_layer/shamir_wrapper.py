"""
Shamir Protocol Wrapper

Provides a wrapper for the Shamir secret sharing protocol in MP-SPDZ,
suitable for honest majority settings with semi-honest security.
"""

import os
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass
from .mascot_wrapper import ProtocolWrapper, MascotError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ShamirError(Exception):
    """Custom exception for Shamir protocol errors."""
    pass

@dataclass
class ShamirConfig:
    """Configuration for Shamir protocol execution."""
    n_parties: int
    party_id: int
    program_name: str
    threshold: Optional[int] = None  # Default: (n_parties - 1) // 2
    data_dir: str = "Player-Data"
    ssl_dir: str = "Player-Data"
    host: str = "localhost"
    port_base: int = 5000
    field_size: int = 64
    online_threads: int = 1
    memory_limit_mb: int = 512
    timeout_seconds: int = 180
    debug_mode: bool = False
    
    def __post_init__(self):
        if self.threshold is None:
            self.threshold = (self.n_parties - 1) // 2
        
        # Validate threshold
        if self.threshold >= self.n_parties:
            raise ShamirError(f"Threshold {self.threshold} must be less than n_parties {self.n_parties}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'n_parties': self.n_parties,
            'party_id': self.party_id,
            'program_name': self.program_name,
            'threshold': self.threshold,
            'data_dir': self.data_dir,
            'ssl_dir': self.ssl_dir,
            'host': self.host,
            'port_base': self.port_base,
            'field_size': self.field_size,
            'online_threads': self.online_threads,
            'memory_limit_mb': self.memory_limit_mb,
            'timeout_seconds': self.timeout_seconds,
            'debug_mode': self.debug_mode
        }

class ShamirWrapper(ProtocolWrapper):
    """Wrapper for Shamir secret sharing protocol."""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        """Initialize Shamir wrapper."""
        self.mp_spdz_path = mp_spdz_path
        self.config = None
        self.temp_files = []
        self.process = None
        self._validate_installation()
    
    def _validate_installation(self):
        """Validate MP-SPDZ installation for Shamir."""
        try:
            if not os.path.exists(self.mp_spdz_path):
                raise ShamirError(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            # Check for Shamir executable
            shamir_exec = os.path.join(self.mp_spdz_path, "shamir-party.x")
            if not os.path.exists(shamir_exec):
                logger.warning("Shamir executable not found - may need compilation")
            
            logger.info("Shamir protocol installation validated")
            
        except Exception as e:
            logger.error(f"Error validating Shamir installation: {e}")
            raise ShamirError(f"Invalid Shamir installation: {e}")
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Setup Shamir protocol environment."""
        try:
            self.config = ShamirConfig(**config)
            
            # Validate minimum parties for Shamir
            if self.config.n_parties < 3:
                raise ShamirError("Shamir protocol requires at least 3 parties")
            
            # Setup directories
            self._setup_directories()
            self._setup_ssl_certificates()
            self._setup_input_files()
            
            logger.info("Shamir protocol environment setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up Shamir environment: {e}")
            raise ShamirError(f"Failed to setup Shamir environment: {e}")
    
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
        """Setup SSL certificates (required for honest majority)."""
        try:
            ssl_dir = os.path.join(self.mp_spdz_path, self.config.ssl_dir)
            cert_file = os.path.join(ssl_dir, f"P{self.config.party_id}.pem")
            
            if not os.path.exists(cert_file):
                setup_script = os.path.join(self.mp_spdz_path, "Scripts/setup-ssl.sh")
                if os.path.exists(setup_script):
                    cmd = [setup_script, str(self.config.n_parties), ssl_dir]
                    subprocess.run(cmd, cwd=self.mp_spdz_path, check=True)
                    logger.info("SSL certificates generated for Shamir")
                else:
                    logger.warning("SSL setup script not found")
            
        except Exception as e:
            logger.error(f"Error setting up SSL certificates: {e}")
            raise ShamirError(f"Failed to setup SSL certificates: {e}")
    
    def _setup_input_files(self):
        """Setup input data files."""
        data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
        
        for party_id in range(self.config.n_parties):
            input_file = os.path.join(data_dir, f"Input-P{party_id}-0")
            if not os.path.exists(input_file):
                with open(input_file, 'w') as f:
                    f.write("0\n")
    
    def compile_program(self, program_path: str, output_path: Optional[str] = None) -> None:
        """Compile MPC program for Shamir."""
        try:
            if not os.path.exists(program_path):
                raise ShamirError(f"Program file not found: {program_path}")
            
            compile_script = os.path.join(self.mp_spdz_path, "compile.py")
            cmd = [
                "python3", compile_script,
                "-F", str(self.config.field_size),
                program_path
            ]
            
            logger.info(f"Compiling program for Shamir: {program_path}")
            result = subprocess.run(cmd, cwd=self.mp_spdz_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                raise ShamirError(f"Compilation failed: {result.stderr}")
            
            logger.info("Program compiled successfully for Shamir")
            
        except Exception as e:
            logger.error(f"Error compiling program: {e}")
            raise ShamirError(f"Failed to compile program: {e}")
    
    def run_preprocessing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Shamir doesn't require preprocessing."""
        return {
            'status': 'skipped',
            'message': 'Shamir protocol does not require preprocessing',
            'duration': 0
        }
    
    def run_online(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Shamir online phase."""
        try:
            shamir_exec = os.path.join(self.mp_spdz_path, "shamir-party.x")
            if not os.path.exists(shamir_exec):
                raise ShamirError("Shamir executable not found")
            
            start_time = time.time()
            
            cmd = [
                shamir_exec,
                "-p", str(self.config.party_id),
                "-N", str(self.config.n_parties),
                "-T", str(self.config.threshold),
                "-h", self.config.host,
                "-pn", str(self.config.port_base),
                self.config.program_name
            ]
            
            if self.config.debug_mode:
                cmd.append("-v")
            
            logger.info(f"Running Shamir online phase for party {self.config.party_id}")
            
            result = subprocess.run(cmd, cwd=self.mp_spdz_path,
                                  capture_output=True, text=True,
                                  timeout=self.config.timeout_seconds)
            
            end_time = time.time()
            
            if result.returncode != 0:
                logger.error(f"Shamir online phase failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'duration': end_time - start_time
                }
            
            results = self._parse_online_output(result.stdout)
            
            logger.info("Shamir online phase completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout,
                'results': results
            }
            
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Shamir online phase timed out'}
        except Exception as e:
            logger.error(f"Error running Shamir online phase: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _parse_online_output(self, output: str) -> Dict[str, Any]:
        """Parse Shamir online output."""
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
        """Get Shamir protocol information."""
        return {
            'protocol_name': 'Shamir',
            'security_model': 'semi_honest',
            'adversary_model': 'honest_majority',
            'computation_domain': 'field_prime',
            'min_parties': 3,
            'max_parties': None,
            'supports_preprocessing': False,
            'supports_online_only': True,
            'features': [
                'Semi-honest security',
                'Honest majority',
                'Field arithmetic',
                'No preprocessing required',
                'Threshold secret sharing'
            ]
        }
    
    def cleanup(self):
        """Clean up Shamir wrapper resources."""
        try:
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
            
            logger.info("Shamir wrapper cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def estimate_resources(self, computation_size: Dict[str, int]) -> Dict[str, Any]:
        """Estimate resources for Shamir computation."""
        n_multiplications = computation_size.get('multiplications', 1000)
        n_additions = computation_size.get('additions', 5000)
        n_parties = computation_size.get('parties', self.config.n_parties)
        
        # Shamir is generally more efficient than MASCOT
        online_time = n_multiplications * 0.00005 + n_additions * 0.000005
        online_memory = n_multiplications * 0.00005 + 20
        online_network = n_multiplications * 0.05 * n_parties
        
        return {
            'time_estimates': {
                'preprocessing_seconds': 0,
                'online_seconds': online_time,
                'total_seconds': online_time
            },
            'memory_estimates': {
                'preprocessing_mb': 0,
                'online_mb': online_memory,
                'peak_mb': online_memory
            },
            'network_estimates': {
                'preprocessing_kb': 0,
                'online_kb': online_network,
                'total_kb': online_network
            }
        }