"""
Access Control Module

Handles permission management, role-based access control, and computation
authorization for the MPC joint data analysis system.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessControlError(Exception):
    """Custom exception for access control errors."""
    pass

class Permission(Enum):
    """System permissions."""
    READ_DATA = "read_data"
    WRITE_DATA = "write_data"
    EXECUTE_COMPUTATION = "execute_computation"
    MANAGE_PARTIES = "manage_parties"
    VIEW_RESULTS = "view_results"
    CONFIGURE_PROTOCOLS = "configure_protocols"
    AUDIT_LOGS = "audit_logs"
    SYSTEM_ADMIN = "system_admin"

class Role(Enum):
    """System roles."""
    PARTICIPANT = "participant"
    COORDINATOR = "coordinator"
    ADMIN = "admin"
    OBSERVER = "observer"

class ResourceType(Enum):
    """Types of resources that can be accessed."""
    DATASET = "dataset"
    COMPUTATION = "computation"
    RESULT = "result"
    PROTOCOL = "protocol"
    SYSTEM = "system"

@dataclass
class AccessPolicy:
    """Defines access policy for a resource."""
    resource_id: str
    resource_type: ResourceType
    owner_party_id: int
    required_permissions: List[Permission]
    allowed_parties: Set[int] = field(default_factory=set)
    denied_parties: Set[int] = field(default_factory=set)
    time_constraints: Optional[Dict[str, float]] = None
    data_constraints: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.time_constraints is None:
            self.time_constraints = {}
        if self.data_constraints is None:
            self.data_constraints = {}

@dataclass
class AccessRequest:
    """Represents an access request."""
    party_id: int
    resource_id: str
    resource_type: ResourceType
    requested_permissions: List[Permission]
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AccessDecision:
    """Represents an access control decision."""
    granted: bool
    reason: str
    granted_permissions: List[Permission]
    denied_permissions: List[Permission]
    conditions: List[str] = field(default_factory=list)
    expires_at: Optional[float] = None

class RoleManager:
    """Manages roles and their permissions."""
    
    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
        self.party_roles = {}  # party_id -> set of roles
        self.custom_permissions = {}  # party_id -> set of permissions
    
    def _initialize_role_permissions(self) -> Dict[Role, Set[Permission]]:
        """Initialize default role permissions."""
        return {
            Role.PARTICIPANT: {
                Permission.READ_DATA,
                Permission.WRITE_DATA,
                Permission.EXECUTE_COMPUTATION,
                Permission.VIEW_RESULTS
            },
            Role.COORDINATOR: {
                Permission.READ_DATA,
                Permission.WRITE_DATA,
                Permission.EXECUTE_COMPUTATION,
                Permission.VIEW_RESULTS,
                Permission.MANAGE_PARTIES,
                Permission.CONFIGURE_PROTOCOLS
            },
            Role.ADMIN: {
                Permission.READ_DATA,
                Permission.WRITE_DATA,
                Permission.EXECUTE_COMPUTATION,
                Permission.VIEW_RESULTS,
                Permission.MANAGE_PARTIES,
                Permission.CONFIGURE_PROTOCOLS,
                Permission.AUDIT_LOGS,
                Permission.SYSTEM_ADMIN
            },
            Role.OBSERVER: {
                Permission.READ_DATA,
                Permission.VIEW_RESULTS,
                Permission.AUDIT_LOGS
            }
        }
    
    def assign_role(self, party_id: int, role: Role):
        """Assign a role to a party."""
        if party_id not in self.party_roles:
            self.party_roles[party_id] = set()
        self.party_roles[party_id].add(role)
        logger.info(f"Assigned role {role.value} to party {party_id}")
    
    def revoke_role(self, party_id: int, role: Role):
        """Revoke a role from a party."""
        if party_id in self.party_roles:
            self.party_roles[party_id].discard(role)
            if not self.party_roles[party_id]:
                del self.party_roles[party_id]
        logger.info(f"Revoked role {role.value} from party {party_id}")
    
    def grant_permission(self, party_id: int, permission: Permission):
        """Grant a custom permission to a party."""
        if party_id not in self.custom_permissions:
            self.custom_permissions[party_id] = set()
        self.custom_permissions[party_id].add(permission)
        logger.info(f"Granted permission {permission.value} to party {party_id}")
    
    def revoke_permission(self, party_id: int, permission: Permission):
        """Revoke a custom permission from a party."""
        if party_id in self.custom_permissions:
            self.custom_permissions[party_id].discard(permission)
            if not self.custom_permissions[party_id]:
                del self.custom_permissions[party_id]
        logger.info(f"Revoked permission {permission.value} from party {party_id}")
    
    def get_party_permissions(self, party_id: int) -> Set[Permission]:
        """Get all permissions for a party."""
        permissions = set()
        
        # Add permissions from roles
        party_roles = self.party_roles.get(party_id, set())
        for role in party_roles:
            permissions.update(self.role_permissions[role])
        
        # Add custom permissions
        custom_perms = self.custom_permissions.get(party_id, set())
        permissions.update(custom_perms)
        
        return permissions
    
    def has_permission(self, party_id: int, permission: Permission) -> bool:
        """Check if a party has a specific permission."""
        return permission in self.get_party_permissions(party_id)
    
    def get_party_roles(self, party_id: int) -> Set[Role]:
        """Get all roles for a party."""
        return self.party_roles.get(party_id, set())

class PolicyManager:
    """Manages access policies for resources."""
    
    def __init__(self):
        self.policies = {}  # resource_id -> AccessPolicy
        self.policy_templates = self._initialize_policy_templates()
    
    def _initialize_policy_templates(self) -> Dict[str, AccessPolicy]:
        """Initialize default policy templates."""
        templates = {}
        
        # Default dataset policy
        templates['dataset_default'] = AccessPolicy(
            resource_id='',
            resource_type=ResourceType.DATASET,
            owner_party_id=0,
            required_permissions=[Permission.READ_DATA],
            allowed_parties=set(),
            denied_parties=set()
        )
        
        # Default computation policy
        templates['computation_default'] = AccessPolicy(
            resource_id='',
            resource_type=ResourceType.COMPUTATION,
            owner_party_id=0,
            required_permissions=[Permission.EXECUTE_COMPUTATION],
            allowed_parties=set(),
            denied_parties=set()
        )
        
        # Default result policy
        templates['result_default'] = AccessPolicy(
            resource_id='',
            resource_type=ResourceType.RESULT,
            owner_party_id=0,
            required_permissions=[Permission.VIEW_RESULTS],
            allowed_parties=set(),
            denied_parties=set()
        )
        
        return templates
    
    def create_policy(self, resource_id: str, resource_type: ResourceType,
                     owner_party_id: int, required_permissions: List[Permission],
                     allowed_parties: Set[int] = None,
                     denied_parties: Set[int] = None,
                     time_constraints: Dict[str, float] = None,
                     data_constraints: Dict[str, Any] = None) -> AccessPolicy:
        """Create a new access policy."""
        policy = AccessPolicy(
            resource_id=resource_id,
            resource_type=resource_type,
            owner_party_id=owner_party_id,
            required_permissions=required_permissions,
            allowed_parties=allowed_parties or set(),
            denied_parties=denied_parties or set(),
            time_constraints=time_constraints,
            data_constraints=data_constraints
        )
        
        self.policies[resource_id] = policy
        logger.info(f"Created policy for resource {resource_id}")
        return policy
    
    def get_policy(self, resource_id: str) -> Optional[AccessPolicy]:
        """Get policy for a resource."""
        return self.policies.get(resource_id)
    
    def update_policy(self, resource_id: str, **kwargs) -> bool:
        """Update an existing policy."""
        if resource_id not in self.policies:
            return False
        
        policy = self.policies[resource_id]
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        logger.info(f"Updated policy for resource {resource_id}")
        return True
    
    def delete_policy(self, resource_id: str) -> bool:
        """Delete a policy."""
        if resource_id in self.policies:
            del self.policies[resource_id]
            logger.info(f"Deleted policy for resource {resource_id}")
            return True
        return False
    
    def create_from_template(self, template_name: str, resource_id: str,
                           owner_party_id: int, **kwargs) -> AccessPolicy:
        """Create policy from template."""
        if template_name not in self.policy_templates:
            raise AccessControlError(f"Unknown policy template: {template_name}")
        
        template = self.policy_templates[template_name]
        policy = AccessPolicy(
            resource_id=resource_id,
            resource_type=template.resource_type,
            owner_party_id=owner_party_id,
            required_permissions=template.required_permissions.copy(),
            allowed_parties=template.allowed_parties.copy(),
            denied_parties=template.denied_parties.copy(),
            time_constraints=template.time_constraints.copy(),
            data_constraints=template.data_constraints.copy()
        )
        
        # Apply custom overrides
        for key, value in kwargs.items():
            if hasattr(policy, key):
                setattr(policy, key, value)
        
        self.policies[resource_id] = policy
        logger.info(f"Created policy from template {template_name} for resource {resource_id}")
        return policy

class AccessControlManager:
    """Main access control manager."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.role_manager = RoleManager()
        self.policy_manager = PolicyManager()
        self.access_log = []
        self.denied_attempts = {}  # party_id -> count
        self.max_denied_attempts = config.get('max_denied_attempts', 5)
        self.lockout_duration = config.get('lockout_duration_minutes', 30)
        self.locked_parties = {}  # party_id -> lockout_until
    
    def authorize_access(self, request: AccessRequest) -> AccessDecision:
        """Authorize an access request."""
        try:
            # Check if party is locked out
            if self._is_party_locked(request.party_id):
                decision = AccessDecision(
                    granted=False,
                    reason="Party is locked out due to too many failed attempts",
                    granted_permissions=[],
                    denied_permissions=request.requested_permissions
                )
                self._log_access_decision(request, decision)
                return decision
            
            # Get resource policy
            policy = self.policy_manager.get_policy(request.resource_id)
            if not policy:
                decision = AccessDecision(
                    granted=False,
                    reason="No policy found for resource",
                    granted_permissions=[],
                    denied_permissions=request.requested_permissions
                )
                self._log_access_decision(request, decision)
                return decision
            
            # Check party permissions
            party_permissions = self.role_manager.get_party_permissions(request.party_id)
            
            # Check if party has required permissions
            granted_permissions = []
            denied_permissions = []
            
            for permission in request.requested_permissions:
                if permission in party_permissions and permission in policy.required_permissions:
                    granted_permissions.append(permission)
                else:
                    denied_permissions.append(permission)
            
            # Check explicit allow/deny lists
            if request.party_id in policy.denied_parties:
                decision = AccessDecision(
                    granted=False,
                    reason="Party is explicitly denied access",
                    granted_permissions=[],
                    denied_permissions=request.requested_permissions
                )
                self._log_access_decision(request, decision)
                self._record_denied_attempt(request.party_id)
                return decision
            
            # Check if party is explicitly allowed or owner
            if (request.party_id != policy.owner_party_id and 
                policy.allowed_parties and 
                request.party_id not in policy.allowed_parties):
                decision = AccessDecision(
                    granted=False,
                    reason="Party is not in allowed list",
                    granted_permissions=[],
                    denied_permissions=request.requested_permissions
                )
                self._log_access_decision(request, decision)
                self._record_denied_attempt(request.party_id)
                return decision
            
            # Check time constraints
            if not self._check_time_constraints(policy, request):
                decision = AccessDecision(
                    granted=False,
                    reason="Access not allowed at this time",
                    granted_permissions=[],
                    denied_permissions=request.requested_permissions
                )
                self._log_access_decision(request, decision)
                self._record_denied_attempt(request.party_id)
                return decision
            
            # Check data constraints
            if not self._check_data_constraints(policy, request):
                decision = AccessDecision(
                    granted=False,
                    reason="Data constraints not met",
                    granted_permissions=[],
                    denied_permissions=request.requested_permissions
                )
                self._log_access_decision(request, decision)
                self._record_denied_attempt(request.party_id)
                return decision
            
            # Determine final decision
            granted = len(granted_permissions) > 0 and len(denied_permissions) == 0
            
            if granted:
                # Reset denied attempts on successful access
                self.denied_attempts.pop(request.party_id, None)
                reason = "Access granted"
            else:
                self._record_denied_attempt(request.party_id)
                reason = "Insufficient permissions"
            
            decision = AccessDecision(
                granted=granted,
                reason=reason,
                granted_permissions=granted_permissions,
                denied_permissions=denied_permissions
            )
            
            self._log_access_decision(request, decision)
            return decision
            
        except Exception as e:
            logger.error(f"Error in access authorization: {e}")
            decision = AccessDecision(
                granted=False,
                reason=f"Authorization error: {e}",
                granted_permissions=[],
                denied_permissions=request.requested_permissions
            )
            self._log_access_decision(request, decision)
            return decision
    
    def _is_party_locked(self, party_id: int) -> bool:
        """Check if a party is locked out."""
        if party_id in self.locked_parties:
            lockout_until = self.locked_parties[party_id]
            if time.time() < lockout_until:
                return True
            else:
                # Lockout expired, remove from locked parties
                del self.locked_parties[party_id]
        return False
    
    def _record_denied_attempt(self, party_id: int):
        """Record a denied access attempt."""
        if party_id not in self.denied_attempts:
            self.denied_attempts[party_id] = 0
        
        self.denied_attempts[party_id] += 1
        
        if self.denied_attempts[party_id] >= self.max_denied_attempts:
            # Lock out the party
            lockout_until = time.time() + (self.lockout_duration * 60)
            self.locked_parties[party_id] = lockout_until
            logger.warning(f"Party {party_id} locked out until {lockout_until}")
    
    def _check_time_constraints(self, policy: AccessPolicy, request: AccessRequest) -> bool:
        """Check time-based access constraints."""
        if not policy.time_constraints:
            return True
        
        current_time = time.time()
        
        # Check if access is within allowed time window
        if 'start_time' in policy.time_constraints:
            if current_time < policy.time_constraints['start_time']:
                return False
        
        if 'end_time' in policy.time_constraints:
            if current_time > policy.time_constraints['end_time']:
                return False
        
        # Check allowed hours (24-hour format)
        if 'allowed_hours' in policy.time_constraints:
            current_hour = time.localtime(current_time).tm_hour
            if current_hour not in policy.time_constraints['allowed_hours']:
                return False
        
        return True
    
    def _check_data_constraints(self, policy: AccessPolicy, request: AccessRequest) -> bool:
        """Check data-based access constraints."""
        if not policy.data_constraints:
            return True
        
        # Check maximum data size
        if 'max_data_size' in policy.data_constraints:
            request_size = request.context.get('data_size', 0)
            if request_size > policy.data_constraints['max_data_size']:
                return False
        
        # Check allowed data types
        if 'allowed_data_types' in policy.data_constraints:
            request_data_type = request.context.get('data_type')
            if request_data_type not in policy.data_constraints['allowed_data_types']:
                return False
        
        return True
    
    def _log_access_decision(self, request: AccessRequest, decision: AccessDecision):
        """Log access decision for auditing."""
        log_entry = {
            'timestamp': time.time(),
            'party_id': request.party_id,
            'resource_id': request.resource_id,
            'resource_type': request.resource_type.value,
            'requested_permissions': [p.value for p in request.requested_permissions],
            'granted': decision.granted,
            'reason': decision.reason,
            'granted_permissions': [p.value for p in decision.granted_permissions],
            'denied_permissions': [p.value for p in decision.denied_permissions]
        }
        
        self.access_log.append(log_entry)
        logger.info(f"Access decision logged for party {request.party_id}")
    
    def get_access_log(self, party_id: Optional[int] = None, 
                      resource_id: Optional[str] = None,
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get access log with optional filtering."""
        filtered_log = self.access_log
        
        if party_id is not None:
            filtered_log = [entry for entry in filtered_log if entry['party_id'] == party_id]
        
        if resource_id is not None:
            filtered_log = [entry for entry in filtered_log if entry['resource_id'] == resource_id]
        
        if start_time is not None:
            filtered_log = [entry for entry in filtered_log if entry['timestamp'] >= start_time]
        
        if end_time is not None:
            filtered_log = [entry for entry in filtered_log if entry['timestamp'] <= end_time]
        
        return filtered_log
    
    def get_access_statistics(self) -> Dict[str, Any]:
        """Get access control statistics."""
        total_requests = len(self.access_log)
        granted_requests = len([entry for entry in self.access_log if entry['granted']])
        denied_requests = total_requests - granted_requests
        
        return {
            'total_requests': total_requests,
            'granted_requests': granted_requests,
            'denied_requests': denied_requests,
            'success_rate': granted_requests / total_requests if total_requests > 0 else 0,
            'locked_parties': len(self.locked_parties),
            'parties_with_denied_attempts': len(self.denied_attempts)
        }
    
    def unlock_party(self, party_id: int) -> bool:
        """Manually unlock a party."""
        if party_id in self.locked_parties:
            del self.locked_parties[party_id]
            self.denied_attempts.pop(party_id, None)
            logger.info(f"Manually unlocked party {party_id}")
            return True
        return False
    
    def clear_access_log(self):
        """Clear the access log."""
        self.access_log.clear()
        logger.info("Access log cleared")
    
    def export_policies(self) -> Dict[str, Any]:
        """Export all policies for backup."""
        policies = {}
        for resource_id, policy in self.policy_manager.policies.items():
            policies[resource_id] = {
                'resource_type': policy.resource_type.value,
                'owner_party_id': policy.owner_party_id,
                'required_permissions': [p.value for p in policy.required_permissions],
                'allowed_parties': list(policy.allowed_parties),
                'denied_parties': list(policy.denied_parties),
                'time_constraints': policy.time_constraints,
                'data_constraints': policy.data_constraints
            }
        return policies
    
    def import_policies(self, policies_data: Dict[str, Any]):
        """Import policies from backup."""
        for resource_id, policy_data in policies_data.items():
            self.policy_manager.create_policy(
                resource_id=resource_id,
                resource_type=ResourceType(policy_data['resource_type']),
                owner_party_id=policy_data['owner_party_id'],
                required_permissions=[Permission(p) for p in policy_data['required_permissions']],
                allowed_parties=set(policy_data['allowed_parties']),
                denied_parties=set(policy_data['denied_parties']),
                time_constraints=policy_data['time_constraints'],
                data_constraints=policy_data['data_constraints']
            )
        logger.info(f"Imported {len(policies_data)} policies")