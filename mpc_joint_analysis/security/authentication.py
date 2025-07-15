"""
Authentication Module

Handles party authentication, certificate management, and secure communication
setup for the MPC joint data analysis system.
"""

import os
import ssl
import hashlib
import hmac
import logging
import base64
import json
import time
import ipaddress
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import secrets
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass

@dataclass
class PartyIdentity:
    """Represents the identity of a party in the MPC system."""
    party_id: int
    name: str
    public_key: bytes
    certificate: bytes
    ip_address: str
    port: int
    role: str = "participant"
    authorized_computations: List[str] = None
    
    def __post_init__(self):
        if self.authorized_computations is None:
            self.authorized_computations = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'party_id': self.party_id,
            'name': self.name,
            'public_key': base64.b64encode(self.public_key).decode('utf-8'),
            'certificate': base64.b64encode(self.certificate).decode('utf-8'),
            'ip_address': self.ip_address,
            'port': self.port,
            'role': self.role,
            'authorized_computations': self.authorized_computations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PartyIdentity':
        """Create from dictionary."""
        return cls(
            party_id=data['party_id'],
            name=data['name'],
            public_key=base64.b64decode(data['public_key']),
            certificate=base64.b64decode(data['certificate']),
            ip_address=data['ip_address'],
            port=data['port'],
            role=data.get('role', 'participant'),
            authorized_computations=data.get('authorized_computations', [])
        )

@dataclass
class AuthenticationToken:
    """Represents an authentication token for secure communication."""
    token_id: str
    party_id: int
    issued_at: float
    expires_at: float
    permissions: List[str]
    nonce: str
    
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return time.time() < self.expires_at
    
    def has_permission(self, permission: str) -> bool:
        """Check if token has specific permission."""
        return permission in self.permissions or 'all' in self.permissions
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'token_id': self.token_id,
            'party_id': self.party_id,
            'issued_at': self.issued_at,
            'expires_at': self.expires_at,
            'permissions': self.permissions,
            'nonce': self.nonce
        }

class CertificateManager:
    """Manages SSL certificates for secure communication."""
    
    def __init__(self, cert_dir: str = "certs"):
        self.cert_dir = cert_dir
        os.makedirs(cert_dir, exist_ok=True)
    
    def generate_self_signed_cert(self, party_id: int, common_name: str,
                                 validity_days: int = 365) -> Tuple[bytes, bytes]:
        """Generate self-signed certificate and private key."""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "MPC"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Secure"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "MPC Analysis"),
                x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.datetime.utcnow()
            ).not_valid_after(
                datetime.datetime.utcnow() + datetime.timedelta(days=validity_days)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName("localhost"),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Serialize certificate and private key
            cert_pem = cert.public_bytes(serialization.Encoding.PEM)
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Save to files
            cert_file = os.path.join(self.cert_dir, f"P{party_id}.pem")
            key_file = os.path.join(self.cert_dir, f"P{party_id}.key")
            
            with open(cert_file, 'wb') as f:
                f.write(cert_pem)
            
            with open(key_file, 'wb') as f:
                f.write(key_pem)
            
            logger.info(f"Generated certificate for party {party_id}")
            return cert_pem, key_pem
            
        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            raise AuthenticationError(f"Failed to generate certificate: {e}")
    
    def load_certificate(self, party_id: int) -> Tuple[bytes, bytes]:
        """Load certificate and private key from files."""
        try:
            cert_file = os.path.join(self.cert_dir, f"P{party_id}.pem")
            key_file = os.path.join(self.cert_dir, f"P{party_id}.key")
            
            if not os.path.exists(cert_file) or not os.path.exists(key_file):
                raise AuthenticationError(f"Certificate files not found for party {party_id}")
            
            with open(cert_file, 'rb') as f:
                cert_pem = f.read()
            
            with open(key_file, 'rb') as f:
                key_pem = f.read()
            
            return cert_pem, key_pem
            
        except Exception as e:
            logger.error(f"Error loading certificate: {e}")
            raise AuthenticationError(f"Failed to load certificate: {e}")
    
    def verify_certificate(self, cert_pem: bytes, trusted_certs: List[bytes] = None) -> bool:
        """Verify certificate against trusted certificates."""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem)
            
            # Basic validation
            now = datetime.datetime.utcnow()
            if cert.not_valid_after < now:
                logger.error("Certificate has expired")
                return False
            
            if cert.not_valid_before > now:
                logger.error("Certificate is not yet valid")
                return False
            
            # If trusted certificates provided, verify against them
            if trusted_certs:
                for trusted_cert_pem in trusted_certs:
                    trusted_cert = x509.load_pem_x509_certificate(trusted_cert_pem)
                    if cert.issuer == trusted_cert.subject:
                        # Verify signature (simplified - in production use proper validation)
                        return True
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error verifying certificate: {e}")
            return False

class AuthenticationManager:
    """Manages authentication for MPC parties."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cert_manager = CertificateManager(config.get('cert_dir', 'certs'))
        self.parties = {}  # party_id -> PartyIdentity
        self.active_tokens = {}  # token_id -> AuthenticationToken
        self.shared_secrets = {}  # party_id -> secret
        self.token_expiry = config.get('token_expiry_minutes', 60)
        
        # Initialize encryption for token storage
        self.encryption_key = self._generate_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Load party configurations
        self._load_party_configurations()
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for token storage."""
        password = self.config.get('master_password', 'default_password').encode()
        salt = self.config.get('salt', b'default_salt')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def _load_party_configurations(self):
        """Load party configurations from file."""
        try:
            config_file = self.config.get('party_config_file', 'party_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    party_configs = json.load(f)
                
                for party_data in party_configs:
                    party = PartyIdentity.from_dict(party_data)
                    self.parties[party.party_id] = party
                
                logger.info(f"Loaded {len(self.parties)} party configurations")
            else:
                logger.warning(f"Party configuration file not found: {config_file}")
                
        except Exception as e:
            logger.error(f"Error loading party configurations: {e}")
    
    def register_party(self, party_id: int, name: str, ip_address: str, 
                      port: int, role: str = "participant",
                      authorized_computations: List[str] = None) -> PartyIdentity:
        """Register a new party in the system."""
        try:
            # Generate certificate for the party
            cert_pem, key_pem = self.cert_manager.generate_self_signed_cert(
                party_id, f"party-{party_id}"
            )
            
            # Extract public key
            cert = x509.load_pem_x509_certificate(cert_pem)
            public_key = cert.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            # Create party identity
            party = PartyIdentity(
                party_id=party_id,
                name=name,
                public_key=public_key,
                certificate=cert_pem,
                ip_address=ip_address,
                port=port,
                role=role,
                authorized_computations=authorized_computations or []
            )
            
            self.parties[party_id] = party
            
            # Generate shared secret for this party
            self.shared_secrets[party_id] = secrets.token_bytes(32)
            
            logger.info(f"Registered party {party_id}: {name}")
            return party
            
        except Exception as e:
            logger.error(f"Error registering party: {e}")
            raise AuthenticationError(f"Failed to register party: {e}")
    
    def authenticate_party(self, party_id: int, certificate: bytes,
                          challenge_response: str) -> AuthenticationToken:
        """Authenticate a party and issue a token."""
        try:
            # Verify party exists
            if party_id not in self.parties:
                raise AuthenticationError(f"Unknown party: {party_id}")
            
            party = self.parties[party_id]
            
            # Verify certificate
            if not self.cert_manager.verify_certificate(certificate):
                raise AuthenticationError("Invalid certificate")
            
            # Verify challenge response
            if not self._verify_challenge_response(party_id, challenge_response):
                raise AuthenticationError("Invalid challenge response")
            
            # Issue authentication token
            token = self._issue_token(party_id, party.authorized_computations)
            
            logger.info(f"Authenticated party {party_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error authenticating party: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    def _verify_challenge_response(self, party_id: int, response: str) -> bool:
        """Verify challenge-response authentication."""
        try:
            # In a real implementation, this would verify a signed challenge
            # For now, we'll use a simple HMAC verification
            shared_secret = self.shared_secrets.get(party_id)
            if not shared_secret:
                return False
            
            # Generate expected response
            challenge = f"challenge-{party_id}-{int(time.time() // 60)}"
            expected = hmac.new(shared_secret, challenge.encode(), hashlib.sha256).hexdigest()
            
            return hmac.compare_digest(response, expected)
            
        except Exception as e:
            logger.error(f"Error verifying challenge response: {e}")
            return False
    
    def _issue_token(self, party_id: int, permissions: List[str]) -> AuthenticationToken:
        """Issue an authentication token."""
        try:
            token_id = secrets.token_urlsafe(32)
            current_time = time.time()
            expires_at = current_time + (self.token_expiry * 60)
            
            token = AuthenticationToken(
                token_id=token_id,
                party_id=party_id,
                issued_at=current_time,
                expires_at=expires_at,
                permissions=permissions,
                nonce=secrets.token_urlsafe(16)
            )
            
            self.active_tokens[token_id] = token
            
            # Clean up expired tokens
            self._cleanup_expired_tokens()
            
            logger.info(f"Issued token {token_id} for party {party_id}")
            return token
            
        except Exception as e:
            logger.error(f"Error issuing token: {e}")
            raise AuthenticationError(f"Failed to issue token: {e}")
    
    def verify_token(self, token_id: str) -> Optional[AuthenticationToken]:
        """Verify and return authentication token."""
        try:
            token = self.active_tokens.get(token_id)
            if not token:
                return None
            
            if not token.is_valid():
                del self.active_tokens[token_id]
                return None
            
            return token
            
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def revoke_token(self, token_id: str) -> bool:
        """Revoke an authentication token."""
        try:
            if token_id in self.active_tokens:
                del self.active_tokens[token_id]
                logger.info(f"Revoked token {token_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
            return False
    
    def _cleanup_expired_tokens(self):
        """Remove expired tokens from active tokens."""
        current_time = time.time()
        expired_tokens = [
            token_id for token_id, token in self.active_tokens.items()
            if token.expires_at < current_time
        ]
        
        for token_id in expired_tokens:
            del self.active_tokens[token_id]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
    
    def get_party_info(self, party_id: int) -> Optional[PartyIdentity]:
        """Get information about a registered party."""
        return self.parties.get(party_id)
    
    def get_all_parties(self) -> List[PartyIdentity]:
        """Get all registered parties."""
        return list(self.parties.values())
    
    def create_ssl_context(self, party_id: int) -> ssl.SSLContext:
        """Create SSL context for secure communication."""
        try:
            cert_pem, key_pem = self.cert_manager.load_certificate(party_id)
            
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # In production, use proper verification
            
            # Load certificate and key
            context.load_cert_chain(
                certfile=os.path.join(self.cert_manager.cert_dir, f"P{party_id}.pem"),
                keyfile=os.path.join(self.cert_manager.cert_dir, f"P{party_id}.key")
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error creating SSL context: {e}")
            raise AuthenticationError(f"Failed to create SSL context: {e}")
    
    def save_party_configurations(self):
        """Save party configurations to file."""
        try:
            config_file = self.config.get('party_config_file', 'party_config.json')
            party_configs = [party.to_dict() for party in self.parties.values()]
            
            with open(config_file, 'w') as f:
                json.dump(party_configs, f, indent=2)
            
            logger.info(f"Saved {len(party_configs)} party configurations")
            
        except Exception as e:
            logger.error(f"Error saving party configurations: {e}")
    
    def get_authentication_stats(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        current_time = time.time()
        active_tokens = [
            token for token in self.active_tokens.values()
            if token.is_valid()
        ]
        
        return {
            'total_parties': len(self.parties),
            'active_tokens': len(active_tokens),
            'expired_tokens': len(self.active_tokens) - len(active_tokens),
            'parties_by_role': {
                role: len([p for p in self.parties.values() if p.role == role])
                for role in set(p.role for p in self.parties.values())
            }
        }