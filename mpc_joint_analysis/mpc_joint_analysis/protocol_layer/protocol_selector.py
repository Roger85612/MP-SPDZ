"""
Protocol Selector Module

Automatically selects the optimal MPC protocol based on various factors including
number of parties, security requirements, computation type, and performance needs.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProtocolError(Exception):
    """Custom exception for protocol-related errors."""
    pass

class SecurityModel(Enum):
    """Security models for MPC protocols."""
    SEMI_HONEST = "semi_honest"
    MALICIOUS = "malicious"
    COVERT = "covert"

class AdversaryModel(Enum):
    """Adversary models for MPC protocols."""
    HONEST_MAJORITY = "honest_majority"
    DISHONEST_MAJORITY = "dishonest_majority"
    HONEST_SUPERMAJORITY = "honest_supermajority"

class ComputationDomain(Enum):
    """Computation domains for MPC protocols."""
    FIELD_PRIME = "field_prime"
    RING_2K = "ring_2k"
    BINARY = "binary"
    GARBLING = "garbling"

class ProtocolType(Enum):
    """Available MPC protocols."""
    MASCOT = "mascot"
    SPDZ2K = "spdz2k"
    SHAMIR = "shamir"
    ATLAS = "atlas"
    BRAIN = "brain"
    SEMI = "semi"
    SEMI2K = "semi2k"
    REPLICATED = "replicated"
    YAO = "yao"
    BMR = "bmr"
    LOWGEAR = "lowgear"
    HIGHGEAR = "highgear"
    COWGEAR = "cowgear"
    CHAIGEAR = "chaigear"

@dataclass
class ProtocolCapabilities:
    """Capabilities and constraints of an MPC protocol."""
    protocol_type: ProtocolType
    security_model: SecurityModel
    adversary_model: AdversaryModel
    computation_domain: ComputationDomain
    min_parties: int
    max_parties: Optional[int]
    supports_preprocessing: bool
    supports_online_only: bool
    communication_rounds: str  # "constant", "linear", "logarithmic"
    communication_complexity: str  # "low", "medium", "high"
    computational_overhead: str  # "low", "medium", "high"
    memory_requirements: str  # "low", "medium", "high"
    
    def matches_requirements(self, requirements: Dict[str, Any]) -> bool:
        """Check if protocol matches given requirements."""
        # Check number of parties
        n_parties = requirements.get('n_parties', 2)
        if n_parties < self.min_parties:
            return False
        if self.max_parties and n_parties > self.max_parties:
            return False
        
        # Check security model
        required_security = requirements.get('security_model')
        if required_security and SecurityModel(required_security) != self.security_model:
            return False
        
        # Check adversary model
        required_adversary = requirements.get('adversary_model')
        if required_adversary and AdversaryModel(required_adversary) != self.adversary_model:
            return False
        
        # Check computation domain
        required_domain = requirements.get('computation_domain')
        if required_domain and ComputationDomain(required_domain) != self.computation_domain:
            return False
        
        # Check preprocessing requirements
        needs_preprocessing = requirements.get('needs_preprocessing', False)
        if needs_preprocessing and not self.supports_preprocessing:
            return False
        
        return True

class ProtocolSelector:
    """Selects optimal MPC protocol based on requirements and constraints."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize protocol selector.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.protocol_capabilities = {}
        self.performance_profiles = {}
        
        # Initialize protocol capabilities
        self._initialize_protocol_capabilities()
        
        # Load performance profiles
        self._load_performance_profiles()
    
    def _initialize_protocol_capabilities(self):
        """Initialize capabilities for all supported protocols."""
        
        # MASCOT - Malicious, dishonest majority, field prime
        self.protocol_capabilities[ProtocolType.MASCOT] = ProtocolCapabilities(
            protocol_type=ProtocolType.MASCOT,
            security_model=SecurityModel.MALICIOUS,
            adversary_model=AdversaryModel.DISHONEST_MAJORITY,
            computation_domain=ComputationDomain.FIELD_PRIME,
            min_parties=2,
            max_parties=None,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="linear",
            communication_complexity="medium",
            computational_overhead="medium",
            memory_requirements="medium"
        )
        
        # SPDZ2K - Malicious, dishonest majority, ring 2^k
        self.protocol_capabilities[ProtocolType.SPDZ2K] = ProtocolCapabilities(
            protocol_type=ProtocolType.SPDZ2K,
            security_model=SecurityModel.MALICIOUS,
            adversary_model=AdversaryModel.DISHONEST_MAJORITY,
            computation_domain=ComputationDomain.RING_2K,
            min_parties=2,
            max_parties=None,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="linear",
            communication_complexity="medium",
            computational_overhead="medium",
            memory_requirements="medium"
        )
        
        # Shamir - Semi-honest, honest majority, field prime
        self.protocol_capabilities[ProtocolType.SHAMIR] = ProtocolCapabilities(
            protocol_type=ProtocolType.SHAMIR,
            security_model=SecurityModel.SEMI_HONEST,
            adversary_model=AdversaryModel.HONEST_MAJORITY,
            computation_domain=ComputationDomain.FIELD_PRIME,
            min_parties=3,
            max_parties=None,
            supports_preprocessing=False,
            supports_online_only=True,
            communication_rounds="constant",
            communication_complexity="low",
            computational_overhead="low",
            memory_requirements="low"
        )
        
        # ATLAS - Semi-honest, honest majority, field prime (optimized for many parties)
        self.protocol_capabilities[ProtocolType.ATLAS] = ProtocolCapabilities(
            protocol_type=ProtocolType.ATLAS,
            security_model=SecurityModel.SEMI_HONEST,
            adversary_model=AdversaryModel.HONEST_MAJORITY,
            computation_domain=ComputationDomain.FIELD_PRIME,
            min_parties=3,
            max_parties=None,
            supports_preprocessing=False,
            supports_online_only=True,
            communication_rounds="constant",
            communication_complexity="low",
            computational_overhead="low",
            memory_requirements="low"
        )
        
        # Brain - Malicious, honest majority, ring 2^k
        self.protocol_capabilities[ProtocolType.BRAIN] = ProtocolCapabilities(
            protocol_type=ProtocolType.BRAIN,
            security_model=SecurityModel.MALICIOUS,
            adversary_model=AdversaryModel.HONEST_MAJORITY,
            computation_domain=ComputationDomain.RING_2K,
            min_parties=3,
            max_parties=3,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="constant",
            communication_complexity="medium",
            computational_overhead="medium",
            memory_requirements="medium"
        )
        
        # Semi - Semi-honest, dishonest majority, field prime
        self.protocol_capabilities[ProtocolType.SEMI] = ProtocolCapabilities(
            protocol_type=ProtocolType.SEMI,
            security_model=SecurityModel.SEMI_HONEST,
            adversary_model=AdversaryModel.DISHONEST_MAJORITY,
            computation_domain=ComputationDomain.FIELD_PRIME,
            min_parties=2,
            max_parties=None,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="linear",
            communication_complexity="low",
            computational_overhead="low",
            memory_requirements="low"
        )
        
        # Semi2K - Semi-honest, dishonest majority, ring 2^k
        self.protocol_capabilities[ProtocolType.SEMI2K] = ProtocolCapabilities(
            protocol_type=ProtocolType.SEMI2K,
            security_model=SecurityModel.SEMI_HONEST,
            adversary_model=AdversaryModel.DISHONEST_MAJORITY,
            computation_domain=ComputationDomain.RING_2K,
            min_parties=2,
            max_parties=None,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="linear",
            communication_complexity="low",
            computational_overhead="low",
            memory_requirements="low"
        )
        
        # Replicated - Semi-honest, honest majority, various domains
        self.protocol_capabilities[ProtocolType.REPLICATED] = ProtocolCapabilities(
            protocol_type=ProtocolType.REPLICATED,
            security_model=SecurityModel.SEMI_HONEST,
            adversary_model=AdversaryModel.HONEST_MAJORITY,
            computation_domain=ComputationDomain.FIELD_PRIME,
            min_parties=3,
            max_parties=3,
            supports_preprocessing=False,
            supports_online_only=True,
            communication_rounds="constant",
            communication_complexity="low",
            computational_overhead="low",
            memory_requirements="low"
        )
        
        # Yao - Semi-honest, dishonest majority, garbling
        self.protocol_capabilities[ProtocolType.YAO] = ProtocolCapabilities(
            protocol_type=ProtocolType.YAO,
            security_model=SecurityModel.SEMI_HONEST,
            adversary_model=AdversaryModel.DISHONEST_MAJORITY,
            computation_domain=ComputationDomain.GARBLING,
            min_parties=2,
            max_parties=2,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="constant",
            communication_complexity="high",
            computational_overhead="high",
            memory_requirements="high"
        )
        
        # BMR - Various security models, garbling
        self.protocol_capabilities[ProtocolType.BMR] = ProtocolCapabilities(
            protocol_type=ProtocolType.BMR,
            security_model=SecurityModel.MALICIOUS,
            adversary_model=AdversaryModel.DISHONEST_MAJORITY,
            computation_domain=ComputationDomain.GARBLING,
            min_parties=2,
            max_parties=None,
            supports_preprocessing=True,
            supports_online_only=True,
            communication_rounds="constant",
            communication_complexity="high",
            computational_overhead="high",
            memory_requirements="high"
        )
        
        logger.info(f"Initialized {len(self.protocol_capabilities)} protocol capabilities")
    
    def _load_performance_profiles(self):
        """Load performance profiles for different protocols."""
        # This would normally load from configuration or benchmarking data
        # For now, we'll use estimated profiles
        
        self.performance_profiles = {
            ProtocolType.MASCOT: {
                'latency_ms_per_gate': 0.1,
                'throughput_gates_per_sec': 10000,
                'memory_mb_per_party': 100,
                'network_kb_per_gate': 1.0
            },
            ProtocolType.SPDZ2K: {
                'latency_ms_per_gate': 0.08,
                'throughput_gates_per_sec': 12000,
                'memory_mb_per_party': 80,
                'network_kb_per_gate': 0.8
            },
            ProtocolType.SHAMIR: {
                'latency_ms_per_gate': 0.05,
                'throughput_gates_per_sec': 20000,
                'memory_mb_per_party': 50,
                'network_kb_per_gate': 0.5
            },
            ProtocolType.ATLAS: {
                'latency_ms_per_gate': 0.04,
                'throughput_gates_per_sec': 25000,
                'memory_mb_per_party': 40,
                'network_kb_per_gate': 0.4
            },
            ProtocolType.BRAIN: {
                'latency_ms_per_gate': 0.12,
                'throughput_gates_per_sec': 8000,
                'memory_mb_per_party': 120,
                'network_kb_per_gate': 1.2
            },
            ProtocolType.SEMI: {
                'latency_ms_per_gate': 0.03,
                'throughput_gates_per_sec': 30000,
                'memory_mb_per_party': 30,
                'network_kb_per_gate': 0.3
            },
            ProtocolType.SEMI2K: {
                'latency_ms_per_gate': 0.025,
                'throughput_gates_per_sec': 35000,
                'memory_mb_per_party': 25,
                'network_kb_per_gate': 0.25
            },
            ProtocolType.REPLICATED: {
                'latency_ms_per_gate': 0.02,
                'throughput_gates_per_sec': 40000,
                'memory_mb_per_party': 20,
                'network_kb_per_gate': 0.2
            },
            ProtocolType.YAO: {
                'latency_ms_per_gate': 0.5,
                'throughput_gates_per_sec': 2000,
                'memory_mb_per_party': 500,
                'network_kb_per_gate': 5.0
            },
            ProtocolType.BMR: {
                'latency_ms_per_gate': 0.3,
                'throughput_gates_per_sec': 3000,
                'memory_mb_per_party': 300,
                'network_kb_per_gate': 3.0
            }
        }
    
    def select_protocol(self, requirements: Dict[str, Any]) -> Tuple[ProtocolType, Dict[str, Any]]:
        """
        Select the optimal protocol based on requirements.
        
        Args:
            requirements: Dictionary containing requirements and constraints
            
        Returns:
            Tuple of (selected_protocol, selection_metadata)
        """
        try:
            logger.info("Selecting optimal MPC protocol")
            
            # Find compatible protocols
            compatible_protocols = self._find_compatible_protocols(requirements)
            
            if not compatible_protocols:
                raise ProtocolError("No compatible protocols found for given requirements")
            
            # Score and rank protocols
            scored_protocols = self._score_protocols(compatible_protocols, requirements)
            
            # Select the best protocol
            best_protocol = max(scored_protocols, key=lambda x: x[1])
            selected_protocol = best_protocol[0]
            selection_score = best_protocol[1]
            
            # Generate selection metadata
            selection_metadata = {
                'selected_protocol': selected_protocol.value,
                'selection_score': selection_score,
                'compatible_protocols': [p.value for p in compatible_protocols],
                'selection_criteria': self._get_selection_criteria(requirements),
                'protocol_capabilities': self.protocol_capabilities[selected_protocol].__dict__,
                'performance_profile': self.performance_profiles.get(selected_protocol, {})
            }
            
            logger.info(f"Selected protocol: {selected_protocol.value} (score: {selection_score:.3f})")
            return selected_protocol, selection_metadata
            
        except Exception as e:
            logger.error(f"Error selecting protocol: {e}")
            raise ProtocolError(f"Failed to select protocol: {e}")
    
    def _find_compatible_protocols(self, requirements: Dict[str, Any]) -> List[ProtocolType]:
        """Find protocols that are compatible with the given requirements."""
        compatible = []
        
        for protocol_type, capabilities in self.protocol_capabilities.items():
            if capabilities.matches_requirements(requirements):
                compatible.append(protocol_type)
        
        logger.info(f"Found {len(compatible)} compatible protocols")
        return compatible
    
    def _score_protocols(self, protocols: List[ProtocolType], 
                        requirements: Dict[str, Any]) -> List[Tuple[ProtocolType, float]]:
        """Score and rank protocols based on requirements."""
        scored = []
        
        for protocol in protocols:
            score = self._calculate_protocol_score(protocol, requirements)
            scored.append((protocol, score))
        
        # Sort by score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def _calculate_protocol_score(self, protocol: ProtocolType, requirements: Dict[str, Any]) -> float:
        """Calculate a score for a protocol based on requirements."""
        capabilities = self.protocol_capabilities[protocol]
        performance = self.performance_profiles.get(protocol, {})
        
        score = 0.0
        
        # Performance requirements
        if 'performance_priority' in requirements:
            priority = requirements['performance_priority']
            
            if priority == 'latency':
                # Lower latency is better
                latency = performance.get('latency_ms_per_gate', 1.0)
                score += 100.0 / latency
            elif priority == 'throughput':
                # Higher throughput is better
                throughput = performance.get('throughput_gates_per_sec', 1000)
                score += throughput / 1000.0
            elif priority == 'memory':
                # Lower memory usage is better
                memory = performance.get('memory_mb_per_party', 100)
                score += 100.0 / memory
            elif priority == 'network':
                # Lower network usage is better
                network = performance.get('network_kb_per_gate', 1.0)
                score += 100.0 / network
        
        # Security requirements
        if 'security_priority' in requirements:
            priority = requirements['security_priority']
            
            if priority == 'high' and capabilities.security_model == SecurityModel.MALICIOUS:
                score += 50.0
            elif priority == 'medium' and capabilities.security_model == SecurityModel.COVERT:
                score += 30.0
            elif priority == 'low' and capabilities.security_model == SecurityModel.SEMI_HONEST:
                score += 20.0
        
        # Number of parties optimization
        n_parties = requirements.get('n_parties', 2)
        if n_parties <= 3:
            # Favor protocols optimized for few parties
            if protocol in [ProtocolType.YAO, ProtocolType.REPLICATED]:
                score += 20.0
        elif n_parties > 10:
            # Favor protocols that scale well
            if protocol in [ProtocolType.ATLAS, ProtocolType.SHAMIR]:
                score += 30.0
        
        # Computation type optimization
        computation_type = requirements.get('computation_type', 'arithmetic')
        if computation_type == 'arithmetic':
            if capabilities.computation_domain in [ComputationDomain.FIELD_PRIME, ComputationDomain.RING_2K]:
                score += 25.0
        elif computation_type == 'boolean':
            if capabilities.computation_domain in [ComputationDomain.BINARY, ComputationDomain.GARBLING]:
                score += 25.0
        
        # Adversary model preference
        adversary_model = requirements.get('adversary_model')
        if adversary_model == 'honest_majority' and capabilities.adversary_model == AdversaryModel.HONEST_MAJORITY:
            score += 15.0
        elif adversary_model == 'dishonest_majority' and capabilities.adversary_model == AdversaryModel.DISHONEST_MAJORITY:
            score += 15.0
        
        return score
    
    def _get_selection_criteria(self, requirements: Dict[str, Any]) -> Dict[str, str]:
        """Get the criteria used for protocol selection."""
        criteria = {}
        
        criteria['n_parties'] = str(requirements.get('n_parties', 2))
        criteria['security_model'] = requirements.get('security_model', 'semi_honest')
        criteria['adversary_model'] = requirements.get('adversary_model', 'dishonest_majority')
        criteria['computation_domain'] = requirements.get('computation_domain', 'field_prime')
        criteria['performance_priority'] = requirements.get('performance_priority', 'balanced')
        criteria['security_priority'] = requirements.get('security_priority', 'medium')
        criteria['computation_type'] = requirements.get('computation_type', 'arithmetic')
        
        return criteria
    
    def get_protocol_recommendations(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get detailed protocol recommendations with explanations."""
        try:
            compatible_protocols = self._find_compatible_protocols(requirements)
            scored_protocols = self._score_protocols(compatible_protocols, requirements)
            
            recommendations = []
            
            for protocol, score in scored_protocols[:5]:  # Top 5 recommendations
                capabilities = self.protocol_capabilities[protocol]
                performance = self.performance_profiles.get(protocol, {})
                
                recommendation = {
                    'protocol': protocol.value,
                    'score': score,
                    'capabilities': capabilities.__dict__,
                    'performance': performance,
                    'pros': self._get_protocol_pros(protocol, requirements),
                    'cons': self._get_protocol_cons(protocol, requirements),
                    'use_cases': self._get_protocol_use_cases(protocol)
                }
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating protocol recommendations: {e}")
            raise ProtocolError(f"Failed to generate recommendations: {e}")
    
    def _get_protocol_pros(self, protocol: ProtocolType, requirements: Dict[str, Any]) -> List[str]:
        """Get advantages of a protocol for given requirements."""
        capabilities = self.protocol_capabilities[protocol]
        performance = self.performance_profiles.get(protocol, {})
        pros = []
        
        if capabilities.security_model == SecurityModel.MALICIOUS:
            pros.append("Strong security against malicious adversaries")
        
        if capabilities.adversary_model == AdversaryModel.HONEST_MAJORITY:
            pros.append("Efficient with honest majority assumption")
        
        if capabilities.communication_rounds == "constant":
            pros.append("Constant communication rounds")
        
        if capabilities.computational_overhead == "low":
            pros.append("Low computational overhead")
        
        if performance.get('throughput_gates_per_sec', 0) > 20000:
            pros.append("High throughput performance")
        
        if performance.get('latency_ms_per_gate', 1.0) < 0.05:
            pros.append("Low latency")
        
        return pros
    
    def _get_protocol_cons(self, protocol: ProtocolType, requirements: Dict[str, Any]) -> List[str]:
        """Get disadvantages of a protocol for given requirements."""
        capabilities = self.protocol_capabilities[protocol]
        performance = self.performance_profiles.get(protocol, {})
        cons = []
        
        if capabilities.max_parties and capabilities.max_parties < 5:
            cons.append("Limited to small number of parties")
        
        if capabilities.security_model == SecurityModel.SEMI_HONEST:
            cons.append("Assumes semi-honest adversaries only")
        
        if capabilities.communication_complexity == "high":
            cons.append("High communication overhead")
        
        if capabilities.computational_overhead == "high":
            cons.append("High computational overhead")
        
        if performance.get('memory_mb_per_party', 0) > 200:
            cons.append("High memory requirements")
        
        if capabilities.computation_domain == ComputationDomain.GARBLING:
            cons.append("Limited to boolean circuits")
        
        return cons
    
    def _get_protocol_use_cases(self, protocol: ProtocolType) -> List[str]:
        """Get typical use cases for a protocol."""
        use_cases = {
            ProtocolType.MASCOT: [
                "General-purpose MPC with malicious security",
                "Financial applications requiring high security",
                "Multi-party machine learning"
            ],
            ProtocolType.SPDZ2K: [
                "Fixed-point arithmetic computations",
                "Statistical analysis on integers",
                "Secure aggregation"
            ],
            ProtocolType.SHAMIR: [
                "Simple arithmetic computations",
                "Honest majority settings",
                "Educational and research applications"
            ],
            ProtocolType.ATLAS: [
                "Large-scale multi-party computations",
                "Distributed analytics",
                "Honest majority with many parties"
            ],
            ProtocolType.BRAIN: [
                "Three-party computations with malicious security",
                "Integer arithmetic with security",
                "Moderate security requirements"
            ],
            ProtocolType.SEMI: [
                "High-performance semi-honest computations",
                "Benchmarking and research",
                "Applications with trusted parties"
            ],
            ProtocolType.SEMI2K: [
                "Fast integer computations",
                "Semi-honest two-party protocols",
                "Performance-critical applications"
            ],
            ProtocolType.REPLICATED: [
                "Three-party honest majority",
                "Low-latency applications",
                "Simple deployment scenarios"
            ],
            ProtocolType.YAO: [
                "Two-party boolean computations",
                "Specific function evaluation",
                "Moderate-size boolean circuits"
            ],
            ProtocolType.BMR: [
                "Multi-party boolean computations",
                "Complex boolean functions",
                "Garbled circuit applications"
            ]
        }
        
        return use_cases.get(protocol, ["General MPC applications"])
    
    def validate_requirements(self, requirements: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate protocol selection requirements."""
        try:
            # Check required fields
            required_fields = ['n_parties']
            for field in required_fields:
                if field not in requirements:
                    return False, f"Missing required field: {field}"
            
            # Validate number of parties
            n_parties = requirements['n_parties']
            if not isinstance(n_parties, int) or n_parties < 2:
                return False, "Number of parties must be at least 2"
            
            # Validate security model
            security_model = requirements.get('security_model')
            if security_model:
                valid_models = [model.value for model in SecurityModel]
                if security_model not in valid_models:
                    return False, f"Invalid security model: {security_model}"
            
            # Validate adversary model
            adversary_model = requirements.get('adversary_model')
            if adversary_model:
                valid_models = [model.value for model in AdversaryModel]
                if adversary_model not in valid_models:
                    return False, f"Invalid adversary model: {adversary_model}"
            
            # Validate computation domain
            computation_domain = requirements.get('computation_domain')
            if computation_domain:
                valid_domains = [domain.value for domain in ComputationDomain]
                if computation_domain not in valid_domains:
                    return False, f"Invalid computation domain: {computation_domain}"
            
            return True, "Valid requirements"
            
        except Exception as e:
            return False, f"Error validating requirements: {e}"
    
    def get_available_protocols(self) -> List[Dict[str, Any]]:
        """Get information about all available protocols."""
        protocols = []
        
        for protocol_type, capabilities in self.protocol_capabilities.items():
            protocol_info = {
                'protocol': protocol_type.value,
                'capabilities': capabilities.__dict__,
                'performance': self.performance_profiles.get(protocol_type, {}),
                'use_cases': self._get_protocol_use_cases(protocol_type)
            }
            protocols.append(protocol_info)
        
        return protocols
    
    def estimate_performance(self, protocol: ProtocolType, 
                           computation_size: Dict[str, int]) -> Dict[str, float]:
        """Estimate performance metrics for a protocol and computation size."""
        try:
            if protocol not in self.performance_profiles:
                raise ProtocolError(f"No performance profile for {protocol.value}")
            
            profile = self.performance_profiles[protocol]
            
            # Extract computation parameters
            n_gates = computation_size.get('gates', 1000)
            n_parties = computation_size.get('parties', 2)
            n_rounds = computation_size.get('rounds', 10)
            
            # Estimate metrics
            estimated_time = n_gates * profile['latency_ms_per_gate'] / 1000.0  # seconds
            estimated_memory = profile['memory_mb_per_party'] * n_parties
            estimated_network = n_gates * profile['network_kb_per_gate'] * n_parties
            
            return {
                'estimated_time_seconds': estimated_time,
                'estimated_memory_mb': estimated_memory,
                'estimated_network_kb': estimated_network,
                'throughput_gates_per_sec': profile['throughput_gates_per_sec']
            }
            
        except Exception as e:
            logger.error(f"Error estimating performance: {e}")
            raise ProtocolError(f"Failed to estimate performance: {e}")
    
    def compare_protocols(self, protocols: List[str], 
                         requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Compare multiple protocols based on requirements."""
        try:
            comparison = {
                'requirements': requirements,
                'protocols': {},
                'summary': {}
            }
            
            for protocol_name in protocols:
                try:
                    protocol = ProtocolType(protocol_name)
                    capabilities = self.protocol_capabilities[protocol]
                    performance = self.performance_profiles.get(protocol, {})
                    
                    # Check compatibility
                    compatible = capabilities.matches_requirements(requirements)
                    
                    # Calculate score
                    score = self._calculate_protocol_score(protocol, requirements) if compatible else 0.0
                    
                    comparison['protocols'][protocol_name] = {
                        'compatible': compatible,
                        'score': score,
                        'capabilities': capabilities.__dict__,
                        'performance': performance,
                        'pros': self._get_protocol_pros(protocol, requirements),
                        'cons': self._get_protocol_cons(protocol, requirements)
                    }
                    
                except ValueError:
                    comparison['protocols'][protocol_name] = {
                        'error': f"Unknown protocol: {protocol_name}"
                    }
            
            # Generate summary
            compatible_protocols = [p for p, info in comparison['protocols'].items() 
                                  if info.get('compatible', False)]
            
            if compatible_protocols:
                best_protocol = max(compatible_protocols, 
                                  key=lambda p: comparison['protocols'][p]['score'])
                comparison['summary']['best_protocol'] = best_protocol
                comparison['summary']['best_score'] = comparison['protocols'][best_protocol]['score']
            
            comparison['summary']['total_protocols'] = len(protocols)
            comparison['summary']['compatible_protocols'] = len(compatible_protocols)
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing protocols: {e}")
            raise ProtocolError(f"Failed to compare protocols: {e}")