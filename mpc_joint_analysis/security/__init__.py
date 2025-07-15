"""
Security Layer

This module provides comprehensive security functionality for the MPC joint
data analysis system, including authentication, authorization, and audit logging.
"""

from .authentication import (
    AuthenticationManager,
    AuthenticationError,
    PartyIdentity,
    AuthenticationToken,
    CertificateManager
)
from .access_control import (
    AccessControlManager,
    AccessControlError,
    RoleManager,
    PolicyManager,
    AccessPolicy,
    AccessRequest,
    AccessDecision,
    Permission,
    Role,
    ResourceType
)
from .audit_logger import (
    AuditLogger,
    AuditLoggerError,
    AuditEvent,
    AuditFilter,
    EventType,
    EventSeverity
)

__all__ = [
    # Authentication
    'AuthenticationManager',
    'AuthenticationError',
    'PartyIdentity',
    'AuthenticationToken',
    'CertificateManager',
    
    # Access Control
    'AccessControlManager',
    'AccessControlError',
    'RoleManager',
    'PolicyManager',
    'AccessPolicy',
    'AccessRequest',
    'AccessDecision',
    'Permission',
    'Role',
    'ResourceType',
    
    # Audit Logging
    'AuditLogger',
    'AuditLoggerError',
    'AuditEvent',
    'AuditFilter',
    'EventType',
    'EventSeverity'
]