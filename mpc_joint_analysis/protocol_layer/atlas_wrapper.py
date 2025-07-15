"""
Atlas Protocol Wrapper

Provides a wrapper for the Atlas protocol in MP-SPDZ,
optimized for honest majority settings with many parties.
"""

import os
import subprocess
import logging
from typing import Dict, List, Any, Optional, Tuple
import time
from dataclasses import dataclass
from .mascot_wrapper import ProtocolWrapper
from .shamir_wrapper import ShamirError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtlasError(Exception):
    """Custom exception for Atlas protocol errors."""
    pass

@dataclass
class AtlasConfig:
    """Configuration for Atlas protocol execution."""
    n_parties: int
    party_id: int
    program_name: str
    threshold: Optional[int] = None
    data_dir: str = "Player-Data"
    ssl_dir: str = "Player-Data"
    host: str = "localhost"
    port_base: int = 5000
    field_size: int = 64
    online_threads: int = 1
    memory_limit_mb: int = 512
    timeout_seconds: int = 240
    debug_mode: bool = False
    use_optimizations: bool = True
    
    def __post_init__(self):
        if self.threshold is None:
            self.threshold = (self.n_parties - 1) // 2
        
        if self.threshold >= self.n_parties:
            raise AtlasError(f"Threshold {self.threshold} must be less than n_parties {self.n_parties}")
    
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
            'debug_mode': self.debug_mode,
            'use_optimizations': self.use_optimizations
        }

class AtlasWrapper(ProtocolWrapper):
    """Wrapper for Atlas protocol execution."""
    
    def __init__(self, mp_spdz_path: str = "/mnt/c/Users/Lenovo/source/repos/MP-SPDZ"):
        """Initialize Atlas wrapper."""
        self.mp_spdz_path = mp_spdz_path
        self.config = None
        self.temp_files = []
        self.process = None
        self._validate_installation()
    
    def _validate_installation(self):
        """Validate MP-SPDZ installation for Atlas."""
        try:
            if not os.path.exists(self.mp_spdz_path):
                raise AtlasError(f"MP-SPDZ path not found: {self.mp_spdz_path}")
            
            atlas_exec = os.path.join(self.mp_spdz_path, "atlas-party.x")
            if not os.path.exists(atlas_exec):
                logger.warning("Atlas executable not found - may need compilation")
            
            logger.info("Atlas protocol installation validated")
            
        except Exception as e:
            logger.error(f"Error validating Atlas installation: {e}")
            raise AtlasError(f"Invalid Atlas installation: {e}")
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Setup Atlas protocol environment."""
        try:
            self.config = AtlasConfig(**config)
            
            if self.config.n_parties < 3:
                raise AtlasError("Atlas protocol requires at least 3 parties")
            
            self._setup_directories()
            self._setup_ssl_certificates()
            self._setup_input_files()
            
            logger.info("Atlas protocol environment setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up Atlas environment: {e}")
            raise AtlasError(f"Failed to setup Atlas environment: {e}")
    
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
        """Setup SSL certificates."""
        try:
            ssl_dir = os.path.join(self.mp_spdz_path, self.config.ssl_dir)
            cert_file = os.path.join(ssl_dir, f"P{self.config.party_id}.pem")
            
            if not os.path.exists(cert_file):
                setup_script = os.path.join(self.mp_spdz_path, "Scripts/setup-ssl.sh")
                if os.path.exists(setup_script):
                    cmd = [setup_script, str(self.config.n_parties), ssl_dir]
                    subprocess.run(cmd, cwd=self.mp_spdz_path, check=True)
                    logger.info("SSL certificates generated for Atlas")
                else:
                    logger.warning("SSL setup script not found")
            
        except Exception as e:
            logger.error(f"Error setting up SSL certificates: {e}")
            raise AtlasError(f"Failed to setup SSL certificates: {e}")
    
    def _setup_input_files(self):
        """Setup input data files."""
        data_dir = os.path.join(self.mp_spdz_path, self.config.data_dir)
        
        for party_id in range(self.config.n_parties):
            input_file = os.path.join(data_dir, f"Input-P{party_id}-0")
            if not os.path.exists(input_file):
                with open(input_file, 'w') as f:
                    f.write("0\n")
    
    def compile_program(self, program_path: str, output_path: Optional[str] = None) -> None:
        """Compile MPC program for Atlas."""
        try:
            if not os.path.exists(program_path):
                raise AtlasError(f"Program file not found: {program_path}")
            
            compile_script = os.path.join(self.mp_spdz_path, "compile.py")
            cmd = [
                "python3", compile_script,
                "-F", str(self.config.field_size),
                program_path
            ]
            
            logger.info(f"Compiling program for Atlas: {program_path}")
            result = subprocess.run(cmd, cwd=self.mp_spdz_path, 
                                  capture_output=True, text=True)
            
            if result.returncode != 0:
                raise AtlasError(f"Compilation failed: {result.stderr}")
            
            logger.info("Program compiled successfully for Atlas")
            
        except Exception as e:
            logger.error(f"Error compiling program: {e}")
            raise AtlasError(f"Failed to compile program: {e}")
    
    def run_preprocessing(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Atlas doesn't require preprocessing."""
        return {
            'status': 'skipped',
            'message': 'Atlas protocol does not require preprocessing',
            'duration': 0
        }
    
    def run_online(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Run Atlas online phase."""
        try:
            atlas_exec = os.path.join(self.mp_spdz_path, "atlas-party.x")
            if not os.path.exists(atlas_exec):
                raise AtlasError("Atlas executable not found")
            
            start_time = time.time()
            
            cmd = [
                atlas_exec,
                "-p", str(self.config.party_id),
                "-N", str(self.config.n_parties),
                "-T", str(self.config.threshold),
                "-h", self.config.host,
                "-pn", str(self.config.port_base),
                self.config.program_name
            ]
            
            if self.config.debug_mode:
                cmd.append("-v")
            
            if self.config.use_optimizations:
                cmd.append("--direct")  # Use direct communication for better performance
            
            logger.info(f"Running Atlas online phase for party {self.config.party_id}")
            
            result = subprocess.run(cmd, cwd=self.mp_spdz_path,
                                  capture_output=True, text=True,
                                  timeout=self.config.timeout_seconds)
            
            end_time = time.time()
            
            if result.returncode != 0:
                logger.error(f"Atlas online phase failed: {result.stderr}")
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'duration': end_time - start_time
                }
            
            results = self._parse_online_output(result.stdout)
            
            logger.info("Atlas online phase completed successfully")
            return {
                'status': 'success',
                'duration': end_time - start_time,
                'output': result.stdout,
                'results': results
            }
            
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'message': 'Atlas online phase timed out'}
        except Exception as e:
            logger.error(f"Error running Atlas online phase: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _parse_online_output(self, output: str) -> Dict[str, Any]:
        """Parse Atlas online output."""
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
        """Get Atlas protocol information."""
        return {
            'protocol_name': 'Atlas',
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
                'Optimized for many parties',
                'No preprocessing required',
                'Scalable communication'
            ],
            'typical_use_cases': [
                'Large-scale multi-party computations',
                'Distributed analytics with many parties',
                'Scalable honest majority protocols',
                'High-performance field arithmetic'
            ]
        }
    
    def cleanup(self):
        """Clean up Atlas wrapper resources."""
        try:
            for temp_file in self.temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
            if self.process and self.process.poll() is None:
                self.process.terminate()
                self.process.wait()
            
            logger.info("Atlas wrapper cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def estimate_resources(self, computation_size: Dict[str, int]) -> Dict[str, Any]:
        """Estimate resources for Atlas computation."""
        n_multiplications = computation_size.get('multiplications', 1000)
        n_additions = computation_size.get('additions', 5000)
        n_parties = computation_size.get('parties', self.config.n_parties)
        
        # Atlas is optimized for many parties and scales well
        online_time = n_multiplications * 0.00003 + n_additions * 0.000003
        online_memory = n_multiplications * 0.00003 + 15
        online_network = n_multiplications * 0.03 * n_parties
        
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
            },
            'scalability_notes': {
                'optimized_for_many_parties': True,
                'communication_complexity': 'O(n log n)',
                'memory_per_party': 'O(log n)',
                'recommended_min_parties': 5
            }
        }