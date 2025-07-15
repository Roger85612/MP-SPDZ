"""
Audit Logger Module

Handles comprehensive logging of all security events, access attempts, and system
activities for compliance and monitoring purposes.
"""

import logging
import json
import time
import os
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import hashlib
import gzip
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuditLoggerError(Exception):
    """Custom exception for audit logger errors."""
    pass

class EventType(Enum):
    """Types of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    COMPUTATION = "computation"
    SYSTEM = "system"
    SECURITY = "security"
    ERROR = "error"

class EventSeverity(Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuditEvent:
    """Represents an audit event."""
    event_id: str
    timestamp: float
    event_type: EventType
    severity: EventSeverity
    party_id: Optional[int]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'iso_timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'party_id': self.party_id,
            'resource_id': self.resource_id,
            'action': self.action,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'session_id': self.session_id,
            'success': self.success
        }

class AuditFilter:
    """Filters for audit log queries."""
    
    def __init__(self, event_types: List[EventType] = None,
                 severities: List[EventSeverity] = None,
                 party_ids: List[int] = None,
                 resource_ids: List[str] = None,
                 start_time: Optional[float] = None,
                 end_time: Optional[float] = None,
                 success_only: Optional[bool] = None):
        self.event_types = event_types or []
        self.severities = severities or []
        self.party_ids = party_ids or []
        self.resource_ids = resource_ids or []
        self.start_time = start_time
        self.end_time = end_time
        self.success_only = success_only
    
    def matches(self, event: AuditEvent) -> bool:
        """Check if event matches filter criteria."""
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        if self.severities and event.severity not in self.severities:
            return False
        
        if self.party_ids and event.party_id not in self.party_ids:
            return False
        
        if self.resource_ids and event.resource_id not in self.resource_ids:
            return False
        
        if self.start_time and event.timestamp < self.start_time:
            return False
        
        if self.end_time and event.timestamp > self.end_time:
            return False
        
        if self.success_only is not None and event.success != self.success_only:
            return False
        
        return True

class LogStorage:
    """Handles storage and retrieval of audit logs."""
    
    def __init__(self, storage_dir: str = "audit_logs", 
                 max_file_size: int = 10 * 1024 * 1024,  # 10MB
                 compression: bool = True):
        self.storage_dir = storage_dir
        self.max_file_size = max_file_size
        self.compression = compression
        self.current_file = None
        self.current_file_size = 0
        self.lock = threading.Lock()
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize current log file
        self._initialize_current_file()
    
    def _initialize_current_file(self):
        """Initialize the current log file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_log_{timestamp}.json"
        self.current_file = os.path.join(self.storage_dir, filename)
        self.current_file_size = 0
        
        # Create empty file
        with open(self.current_file, 'w') as f:
            f.write("")
    
    def store_event(self, event: AuditEvent):
        """Store an audit event."""
        with self.lock:
            try:
                # Convert event to JSON
                event_json = json.dumps(event.to_dict()) + '\n'
                
                # Check if we need to rotate the file
                if self.current_file_size + len(event_json) > self.max_file_size:
                    self._rotate_file()
                
                # Write to current file
                with open(self.current_file, 'a') as f:
                    f.write(event_json)
                
                self.current_file_size += len(event_json)
                
            except Exception as e:
                logger.error(f"Error storing audit event: {e}")
                raise AuditLoggerError(f"Failed to store audit event: {e}")
    
    def _rotate_file(self):
        """Rotate the current log file."""
        # Compress the current file if compression is enabled
        if self.compression:
            compressed_file = f"{self.current_file}.gz"
            with open(self.current_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(self.current_file)
            logger.info(f"Compressed and rotated log file: {compressed_file}")
        else:
            # Just rename the file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archived_file = f"{self.current_file}.{timestamp}"
            os.rename(self.current_file, archived_file)
            logger.info(f"Rotated log file: {archived_file}")
        
        # Create new current file
        self._initialize_current_file()
    
    def search_events(self, audit_filter: AuditFilter, limit: int = 1000) -> List[AuditEvent]:
        """Search for events matching the filter."""
        events = []
        
        try:
            # Search in all log files
            log_files = []
            for filename in os.listdir(self.storage_dir):
                if filename.startswith("audit_log_") and (filename.endswith(".json") or filename.endswith(".json.gz")):
                    log_files.append(os.path.join(self.storage_dir, filename))
            
            # Sort files by name (which includes timestamp)
            log_files.sort(reverse=True)  # Newest first
            
            for log_file in log_files:
                if len(events) >= limit:
                    break
                
                # Handle compressed files
                if log_file.endswith('.gz'):
                    file_opener = gzip.open
                    mode = 'rt'
                else:
                    file_opener = open
                    mode = 'r'
                
                with file_opener(log_file, mode) as f:
                    for line in f:
                        if len(events) >= limit:
                            break
                        
                        try:
                            event_data = json.loads(line.strip())
                            event = AuditEvent(
                                event_id=event_data['event_id'],
                                timestamp=event_data['timestamp'],
                                event_type=EventType(event_data['event_type']),
                                severity=EventSeverity(event_data['severity']),
                                party_id=event_data.get('party_id'),
                                resource_id=event_data.get('resource_id'),
                                action=event_data['action'],
                                details=event_data['details'],
                                ip_address=event_data.get('ip_address'),
                                user_agent=event_data.get('user_agent'),
                                session_id=event_data.get('session_id'),
                                success=event_data.get('success', True)
                            )
                            
                            if audit_filter.matches(event):
                                events.append(event)
                                
                        except (json.JSONDecodeError, KeyError, ValueError) as e:
                            logger.warning(f"Error parsing log line: {e}")
                            continue
            
            return events
            
        except Exception as e:
            logger.error(f"Error searching events: {e}")
            raise AuditLoggerError(f"Failed to search events: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about log storage."""
        try:
            total_size = 0
            file_count = 0
            
            for filename in os.listdir(self.storage_dir):
                if filename.startswith("audit_log_"):
                    file_path = os.path.join(self.storage_dir, filename)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            return {
                'storage_dir': self.storage_dir,
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'file_count': file_count,
                'current_file': self.current_file,
                'current_file_size': self.current_file_size,
                'max_file_size': self.max_file_size,
                'compression_enabled': self.compression
            }
            
        except Exception as e:
            logger.error(f"Error getting storage info: {e}")
            return {}

class AuditLogger:
    """Main audit logger class."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.storage = LogStorage(
            storage_dir=config.get('storage_dir', 'audit_logs'),
            max_file_size=config.get('max_file_size', 10 * 1024 * 1024),
            compression=config.get('compression', True)
        )
        self.event_counters = {event_type: 0 for event_type in EventType}
        self.severity_counters = {severity: 0 for severity in EventSeverity}
        self.integrity_check_enabled = config.get('integrity_check', True)
        self.event_signatures = {}  # event_id -> signature
        
        logger.info("Audit logger initialized")
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_event_signature(self, event: AuditEvent) -> str:
        """Calculate integrity signature for an event."""
        if not self.integrity_check_enabled:
            return ""
        
        # Create a deterministic string representation
        sig_data = f"{event.event_id}:{event.timestamp}:{event.event_type.value}:{event.action}"
        if event.party_id:
            sig_data += f":{event.party_id}"
        if event.resource_id:
            sig_data += f":{event.resource_id}"
        
        # Calculate hash
        return hashlib.sha256(sig_data.encode()).hexdigest()
    
    def log_event(self, event_type: EventType, severity: EventSeverity,
                  action: str, details: Dict[str, Any],
                  party_id: Optional[int] = None,
                  resource_id: Optional[str] = None,
                  ip_address: Optional[str] = None,
                  user_agent: Optional[str] = None,
                  session_id: Optional[str] = None,
                  success: bool = True) -> str:
        """Log an audit event."""
        try:
            event_id = self._generate_event_id()
            
            event = AuditEvent(
                event_id=event_id,
                timestamp=time.time(),
                event_type=event_type,
                severity=severity,
                party_id=party_id,
                resource_id=resource_id,
                action=action,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                success=success
            )
            
            # Calculate integrity signature
            signature = self._calculate_event_signature(event)
            if signature:
                self.event_signatures[event_id] = signature
            
            # Store event
            self.storage.store_event(event)
            
            # Update counters
            self.event_counters[event_type] += 1
            self.severity_counters[severity] += 1
            
            logger.debug(f"Audit event logged: {event_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            raise AuditLoggerError(f"Failed to log audit event: {e}")
    
    def log_authentication(self, party_id: int, action: str, success: bool,
                          details: Dict[str, Any], ip_address: str = None) -> str:
        """Log an authentication event."""
        severity = EventSeverity.MEDIUM if success else EventSeverity.HIGH
        return self.log_event(
            event_type=EventType.AUTHENTICATION,
            severity=severity,
            action=action,
            details=details,
            party_id=party_id,
            ip_address=ip_address,
            success=success
        )
    
    def log_authorization(self, party_id: int, resource_id: str, action: str,
                         success: bool, details: Dict[str, Any]) -> str:
        """Log an authorization event."""
        severity = EventSeverity.LOW if success else EventSeverity.MEDIUM
        return self.log_event(
            event_type=EventType.AUTHORIZATION,
            severity=severity,
            action=action,
            details=details,
            party_id=party_id,
            resource_id=resource_id,
            success=success
        )
    
    def log_data_access(self, party_id: int, resource_id: str, action: str,
                       success: bool, details: Dict[str, Any]) -> str:
        """Log a data access event."""
        severity = EventSeverity.LOW if success else EventSeverity.MEDIUM
        return self.log_event(
            event_type=EventType.DATA_ACCESS,
            severity=severity,
            action=action,
            details=details,
            party_id=party_id,
            resource_id=resource_id,
            success=success
        )
    
    def log_computation(self, party_id: int, resource_id: str, action: str,
                       success: bool, details: Dict[str, Any]) -> str:
        """Log a computation event."""
        severity = EventSeverity.MEDIUM if success else EventSeverity.HIGH
        return self.log_event(
            event_type=EventType.COMPUTATION,
            severity=severity,
            action=action,
            details=details,
            party_id=party_id,
            resource_id=resource_id,
            success=success
        )
    
    def log_system(self, action: str, success: bool, details: Dict[str, Any],
                  severity: EventSeverity = EventSeverity.LOW) -> str:
        """Log a system event."""
        return self.log_event(
            event_type=EventType.SYSTEM,
            severity=severity,
            action=action,
            details=details,
            success=success
        )
    
    def log_security(self, action: str, success: bool, details: Dict[str, Any],
                    severity: EventSeverity = EventSeverity.HIGH,
                    party_id: int = None) -> str:
        """Log a security event."""
        return self.log_event(
            event_type=EventType.SECURITY,
            severity=severity,
            action=action,
            details=details,
            party_id=party_id,
            success=success
        )
    
    def log_error(self, action: str, error_details: Dict[str, Any],
                 severity: EventSeverity = EventSeverity.MEDIUM,
                 party_id: int = None) -> str:
        """Log an error event."""
        return self.log_event(
            event_type=EventType.ERROR,
            severity=severity,
            action=action,
            details=error_details,
            party_id=party_id,
            success=False
        )
    
    def search_events(self, audit_filter: AuditFilter, limit: int = 1000) -> List[AuditEvent]:
        """Search for events matching the filter."""
        return self.storage.search_events(audit_filter, limit)
    
    def get_events_by_party(self, party_id: int, limit: int = 100) -> List[AuditEvent]:
        """Get events for a specific party."""
        filter_obj = AuditFilter(party_ids=[party_id])
        return self.search_events(filter_obj, limit)
    
    def get_events_by_resource(self, resource_id: str, limit: int = 100) -> List[AuditEvent]:
        """Get events for a specific resource."""
        filter_obj = AuditFilter(resource_ids=[resource_id])
        return self.search_events(filter_obj, limit)
    
    def get_failed_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get failed events."""
        filter_obj = AuditFilter(success_only=False)
        return self.search_events(filter_obj, limit)
    
    def get_high_severity_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get high severity events."""
        filter_obj = AuditFilter(severities=[EventSeverity.HIGH, EventSeverity.CRITICAL])
        return self.search_events(filter_obj, limit)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics."""
        return {
            'event_counters': {et.value: count for et, count in self.event_counters.items()},
            'severity_counters': {sev.value: count for sev, count in self.severity_counters.items()},
            'total_events': sum(self.event_counters.values()),
            'storage_info': self.storage.get_storage_info(),
            'integrity_check_enabled': self.integrity_check_enabled
        }
    
    def verify_event_integrity(self, event_id: str) -> bool:
        """Verify the integrity of an event."""
        if not self.integrity_check_enabled:
            return True
        
        if event_id not in self.event_signatures:
            return False
        
        # Find the event
        filter_obj = AuditFilter()
        events = self.search_events(filter_obj, limit=10000)
        
        for event in events:
            if event.event_id == event_id:
                calculated_signature = self._calculate_event_signature(event)
                stored_signature = self.event_signatures[event_id]
                return calculated_signature == stored_signature
        
        return False
    
    def export_events(self, audit_filter: AuditFilter, format: str = 'json') -> str:
        """Export events matching the filter."""
        events = self.search_events(audit_filter, limit=10000)
        
        if format == 'json':
            return json.dumps([event.to_dict() for event in events], indent=2)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if events:
                writer = csv.DictWriter(output, fieldnames=events[0].to_dict().keys())
                writer.writeheader()
                for event in events:
                    writer.writerow(event.to_dict())
            return output.getvalue()
        else:
            raise AuditLoggerError(f"Unsupported export format: {format}")
    
    def cleanup_old_logs(self, retention_days: int = 90):
        """Clean up old log files."""
        try:
            cutoff_time = time.time() - (retention_days * 24 * 60 * 60)
            removed_files = 0
            
            for filename in os.listdir(self.storage.storage_dir):
                if filename.startswith("audit_log_"):
                    file_path = os.path.join(self.storage.storage_dir, filename)
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        os.remove(file_path)
                        removed_files += 1
            
            logger.info(f"Cleaned up {removed_files} old log files")
            
        except Exception as e:
            logger.error(f"Error cleaning up old logs: {e}")
            raise AuditLoggerError(f"Failed to cleanup old logs: {e}")