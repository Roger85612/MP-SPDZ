"""
Semi2K Protocol Wrapper

Provides a wrapper for the Semi2K protocol in MP-SPDZ,
optimized for high-performance semi-honest computations over Z/2^k rings.
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

class Semi2KError(Exception):
    """Custom exception for Semi2K protocol errors."""
    pass

@dataclass
class Semi2KConfig:
    """Configuration for Semi2K protocol execution."""
    n_parties: int
    party_id: int
    program_name: str
    data_dir: str = "Player-Data"
    ssl_dir: str = "Player-Data"
    host: str = "localhost"
    port_base: int = 5000
    ring_size: int = 64  # 2^k ring size
    security_parameter: int = 40
    preprocessing_threads: int = 1
    online_threads: int = 1
    memory_limit_mb: int = 512
    timeout_seconds: int = 180
    use_preprocessing: bool = True
    debug_mode: bool = False
    optimize_for_lan: bool = True
    
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
            'optimize_for_lan': self.optimize_for_lan
        }

class Semi2KWrapper(ProtocolWrapper):
    """Wrapper for Semi2K protocol execution."""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        """Initialize Semi2K wrapper."""
        self.mp_spdz_path = mp_spdz_path
        self.config = None
        self.temp_files = []
        self.process = None
        self._validate_installation()
    
    def _validate_installation(self):
        """Validate MP-SPDZ installation for Semi2K."""
        try:
            if not os.path.exists(self.mp_spdz_path):
                raise Semi2KError(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            # Check for Semi2K executables
            semi2k_exec = os.path.join(self.mp_spdz_path, "semi2k-party.x")
            semi2k_offline = os.path.join(self.mp_spdz_path, "semi2k-offline.x")
            
            if not os.path.exists(semi2k_exec):
                logger.warning("Semi2K online executable not found - may need compilation")
            
            if not os.path.exists(semi2k_offline):
                logger.warning("Semi2K offline executable not found - may need compilation")
            
            logger.info("Semi2K protocol installation validated")
            
        except Exception as e:
            logger.error(f"Error validating Semi2K installation: {e}")
            raise Semi2KError(f"Invalid Semi2K installation: {e}")
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Setup Semi2K protocol environment."""
        try:
            self.config = Semi2KConfig(**config)
            
            # Validate minimum parties for Semi2K
            if self.config.n_parties < 2:
                raise Semi2KError("Semi2K protocol requires at least 2 parties")
            
            # Validate ring size
            if self.config.ring_size not in [32, 64, 128]:
                raise Semi2KError(f"Invalid ring size: {self.config.ring_size}. Must be 32, 64, or 128")
            
            # Setup directories
            self._setup_directories()
            self._setup_ssl_certificates()
            self._setup_input_files()
            
            logger.info("Semi2K protocol environment setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up Semi2K environment: {e}")
            raise Semi2KError(f"Failed to setup Semi2K environment: {e}")
    
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
                    logger.info("SSL certificates generated for Semi2K")
                else:
                    logger.warning("SSL setup script not found")
            
        except Exception as e:
            logger.error(f"Error setting up SSL certificates: {e}")
            raise Semi2KError(f"Failed to setup SSL certificates: {e}")
    
    def _setup_input_files(self):
        """Setup input data files."""
        data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
        
        for party_id in range(self.config.n_parties):
            input_file = os.path.join(data_dir, f"Input-P{party_id}-0")
            if not os.path.exists(input_file):
                with open(input_file, 'w') as f:
                    f.write("0\n")
    
    def compile_program(self, program_path: str, output_path: Optional[str] = None) -> None:
        """Compile MPC program for Semi2K."""
        try:
            if not os.path.exists(program_path):
                raise Semi2KError(f"Program file not found: {program_path}")
            
            compile_script = os.path.join(self.mp_spdz_path, "compile.py")
            cmd = [
                "python3", compile_script,
                "-R", str(self.config.ring_size),  # Use ring size instead of field size
                program_path
            ]
            
            logger.info(f"Compiling program for Semi2K (ring size {self.config.ring_size}): {program_path}")
            result = subprocess.run(cmd, cwd=self.mp_spdz_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Semi2KError(f"Compilation failed: {result.stderr}")
            
            logger.info("Program compiled successfully for Semi2K")
            
        except Exception as e:
            logger.error(f"Error compiling program: {e}")
            raise Semi2KError(f"Failed to compile program: {e}")
    
    def run_preprocessing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Semi2K preprocessing phase."""
        try:
            if not self.config.use_preprocessing:
                return {'status': 'skipped', 'message': 'Preprocessing disabled'}
            
            preprocessing_exec = os.path.join(self.mp_spdz_path, "semi2k-offline.x")
            if not os.path.exists(preprocessing_exec):
                logger.warning("Preprocessing executable not found - skipping preprocessing")
                return {'status': 'skipped', 'message': 'Preprocessing executable not found'}
            
            start_time = time.time()
            
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
            
            if self.config.optimize_for_lan:
                cmd.append("--direct")
            
            logger.info(f"Running Semi2K preprocessing for party {self.config.party_id}")
            
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
            
            logger.info("Semi2K preprocessing completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout
            }
            
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Preprocessing timed out'}
        except Exception as e:
            logger.error(f"Error running preprocessing: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def run_online(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Semi2K online phase."""
        try:
            online_exec = os.path.join(self.mp_spdz_path, "semi2k-party.x")
            if not os.path.exists(online_exec):
                raise Semi2KError("Online executable not found: semi2k-party.x")
            
            start_time = time.time()
            
            cmd = [
                online_exec,
                "-p", str(self.config.party_id),
                "-N", str(self.config.n_parties),
                "-h", self.config.host,
                "-pn", str(self.config.port_base),
                self.config.program_name
            ]
            
            if self.config.use_preprocessing:
                cmd.append("-F")
            
            if self.config.debug_mode:
                cmd.append("-v")
            
            if self.config.optimize_for_lan:
                cmd.append("--direct")
            
            # Add memory limit
            cmd.extend(["-m", str(self.config.memory_limit_mb)])
            
            logger.info(f"Running Semi2K online phase for party {self.config.party_id}")
            
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
            
            results = self._parse_online_output(result.stdout)
            
            logger.info("Semi2K online phase completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout,
                'results': results
            }
            
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Online phase timed out'}
        except Exception as e:
            logger.error(f"Error running online phase: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _parse_online_output(self, output: str) -> Dict[str, Any]:
        """Parse Semi2K online output."""
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
        """Get Semi2K protocol information."""
        return {
            'protocol_name': 'Semi2K',
            'security_model': 'semi_honest',
            'adversary_model': 'dishonest_majority',
            'computation_domain': 'ring_2k',
            'min_parties': 2,
            'max_parties': None,
            'supports_preprocessing': True,
            'supports_online_only': True,
            'features': [
                'Semi-honest security',
                'Dishonest majority',
                'Ring Z/2^k arithmetic',
                'Integer computations',
                'High performance',
                'OT-based preprocessing',
                'Fixed-point arithmetic support'
            ],
            'typical_use_cases': [
                'Integer arithmetic computations',
                'Fixed-point operations',
                'Statistical analysis on integers',
                'High-performance benchmarking',
                'Machine learning with integer data',
                'Secure aggregation of integers'
            ]
        }
    
    def cleanup(self):
        """Clean up Semi2K wrapper resources."""
        try:
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
            
            logger.info("Semi2K wrapper cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def estimate_resources(self, computation_size: Dict[str, int]) -> Dict[str, Any]:
        """Estimate resources for Semi2K computation."""
        n_multiplications = computation_size.get('multiplications', 1000)
        n_additions = computation_size.get('additions', 5000)
        n_parties = computation_size.get('parties', self.config.n_parties)
        
        # Semi2K is even more efficient than Semi for integer operations
        preprocessing_time = n_multiplications * 0.0004  # 0.4ms per multiplication
        online_time = n_multiplications * 0.000025 + n_additions * 0.0000025
        
        preprocessing_memory = n_multiplications * 0.0004 + 25
        online_memory = n_multiplications * 0.000025 + 35
        
        preprocessing_network = n_multiplications * 0.25 * n_parties
        online_network = n_multiplications * 0.04 * n_parties
        
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
            'performance_notes': {
                'very_high_performance': True,
                'integer_optimized': True,
                'ring_size': self.config.ring_size,
                'fixed_point_support': True
            }
        }