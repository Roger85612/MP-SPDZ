"""
Client Interface Module

Handles communication with external clients and data sources for multi-party
computation, including secure data input and result distribution.
"""

import socket
import ssl
import json
import threading
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from abc import ABC, abstractmethod
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClientError(Exception):
    """Custom exception for client interface errors."""
    pass

class ClientStatus(Enum):
    """Client connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DATA_READY = "data_ready"
    ERROR = "error"

@dataclass
class ClientInfo:
    """Information about a connected client."""
    client_id: str
    party_id: str
    ip_address: str
    port: int
    status: ClientStatus
    last_activity: float
    data_schema: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class MessageType(Enum):
    """Types of messages in the protocol."""
    HANDSHAKE = "handshake"
    AUTHENTICATE = "authenticate"
    DATA_SCHEMA = "data_schema"
    DATA_CHUNK = "data_chunk"
    DATA_COMPLETE = "data_complete"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"

@dataclass
class Message:
    """Protocol message structure."""
    msg_type: MessageType
    payload: Dict[str, Any]
    timestamp: float = None
    client_id: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class SecureMessageHandler:
    """Handles secure message encoding/decoding."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key
    
    def encode_message(self, message: Message) -> bytes:
        """Encode message for transmission."""
        try:
            msg_dict = asdict(message)
            msg_dict['msg_type'] = message.msg_type.value
            json_str = json.dumps(msg_dict)
            
            # Add simple encryption if key provided
            if self.encryption_key:
                # Simple XOR encryption for demonstration
                encrypted = self._xor_encrypt(json_str, self.encryption_key)
                return encrypted.encode('utf-8')
            
            return json_str.encode('utf-8')
            
        except Exception as e:
            logger.error(f"Error encoding message: {e}")
            raise ClientError(f"Failed to encode message: {e}")
    
    def decode_message(self, data: bytes) -> Message:
        """Decode received message."""
        try:
            json_str = data.decode('utf-8')
            
            # Decrypt if key provided
            if self.encryption_key:
                json_str = self._xor_decrypt(json_str, self.encryption_key)
            
            msg_dict = json.loads(json_str)
            msg_dict['msg_type'] = MessageType(msg_dict['msg_type'])
            
            return Message(**msg_dict)
            
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            raise ClientError(f"Failed to decode message: {e}")
    
    def _xor_encrypt(self, text: str, key: str) -> str:
        """Simple XOR encryption."""
        key_repeated = (key * (len(text) // len(key) + 1))[:len(text)]
        return ''.join(chr(ord(c) ^ ord(k)) for c, k in zip(text, key_repeated))
    
    def _xor_decrypt(self, encrypted: str, key: str) -> str:
        """Simple XOR decryption."""
        return self._xor_encrypt(encrypted, key)

class ClientConnectionHandler:
    """Handles individual client connections."""
    
    def __init__(self, client_socket: socket.socket, client_info: ClientInfo, 
                 message_handler: SecureMessageHandler, callback_handler: 'CallbackHandler'):
        self.client_socket = client_socket
        self.client_info = client_info
        self.message_handler = message_handler
        self.callback_handler = callback_handler
        self.running = False
        self.data_buffer = []
        
    def start(self):
        """Start handling client connection."""
        self.running = True
        threading.Thread(target=self._handle_client, daemon=True).start()
        logger.info(f"Started handling client {self.client_info.client_id}")
    
    def stop(self):
        """Stop handling client connection."""
        self.running = False
        try:
            self.client_socket.close()
        except:
            pass
        logger.info(f"Stopped handling client {self.client_info.client_id}")
    
    def send_message(self, message: Message):
        """Send message to client."""
        try:
            message.client_id = self.client_info.client_id
            encoded = self.message_handler.encode_message(message)
            
            # Send message length first
            msg_len = len(encoded)
            self.client_socket.send(msg_len.to_bytes(4, byteorder='big'))
            self.client_socket.send(encoded)
            
            logger.debug(f"Sent message to client {self.client_info.client_id}: {message.msg_type}")
            
        except Exception as e:
            logger.error(f"Error sending message to client {self.client_info.client_id}: {e}")
            self.client_info.status = ClientStatus.ERROR
    
    def _handle_client(self):
        """Main client handling loop."""
        try:
            while self.running:
                try:
                    # Receive message length
                    length_bytes = self.client_socket.recv(4)
                    if not length_bytes:
                        break
                    
                    msg_len = int.from_bytes(length_bytes, byteorder='big')
                    
                    # Receive message
                    message_bytes = b''
                    while len(message_bytes) < msg_len:
                        chunk = self.client_socket.recv(msg_len - len(message_bytes))
                        if not chunk:
                            break
                        message_bytes += chunk
                    
                    if len(message_bytes) != msg_len:
                        logger.warning(f"Incomplete message from client {self.client_info.client_id}")
                        continue
                    
                    # Decode and process message
                    message = self.message_handler.decode_message(message_bytes)
                    self._process_message(message)
                    
                    # Update last activity
                    self.client_info.last_activity = time.time()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Error handling client {self.client_info.client_id}: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Client handler error for {self.client_info.client_id}: {e}")
        finally:
            self.client_info.status = ClientStatus.DISCONNECTED
            self.stop()
    
    def _process_message(self, message: Message):
        """Process received message."""
        try:
            if message.msg_type == MessageType.HANDSHAKE:
                self._handle_handshake(message)
            elif message.msg_type == MessageType.AUTHENTICATE:
                self._handle_authentication(message)
            elif message.msg_type == MessageType.DATA_SCHEMA:
                self._handle_data_schema(message)
            elif message.msg_type == MessageType.DATA_CHUNK:
                self._handle_data_chunk(message)
            elif message.msg_type == MessageType.DATA_COMPLETE:
                self._handle_data_complete(message)
            elif message.msg_type == MessageType.HEARTBEAT:
                self._handle_heartbeat(message)
            else:
                logger.warning(f"Unknown message type from client {self.client_info.client_id}: {message.msg_type}")
                
        except Exception as e:
            logger.error(f"Error processing message from client {self.client_info.client_id}: {e}")
            self._send_error_response(f"Error processing message: {e}")
    
    def _handle_handshake(self, message: Message):
        """Handle client handshake."""
        try:
            payload = message.payload
            self.client_info.party_id = payload.get('party_id')
            
            # Send handshake response
            response = Message(
                msg_type=MessageType.HANDSHAKE,
                payload={'status': 'success', 'server_info': 'MPC Joint Analysis Server'}
            )
            self.send_message(response)
            
            self.client_info.status = ClientStatus.CONNECTED
            logger.info(f"Handshake completed for client {self.client_info.client_id}")
            
        except Exception as e:
            logger.error(f"Error in handshake for client {self.client_info.client_id}: {e}")
            self._send_error_response(f"Handshake failed: {e}")
    
    def _handle_authentication(self, message: Message):
        """Handle client authentication."""
        try:
            payload = message.payload
            credentials = payload.get('credentials', {})
            
            # Authenticate client (simplified for demo)
            if self.callback_handler.authenticate_client(self.client_info.party_id, credentials):
                response = Message(
                    msg_type=MessageType.AUTHENTICATE,
                    payload={'status': 'success', 'token': f'token_{self.client_info.client_id}'}
                )
                self.client_info.status = ClientStatus.AUTHENTICATED
                logger.info(f"Client {self.client_info.client_id} authenticated successfully")
            else:
                response = Message(
                    msg_type=MessageType.AUTHENTICATE,
                    payload={'status': 'failed', 'reason': 'Invalid credentials'}
                )
                logger.warning(f"Authentication failed for client {self.client_info.client_id}")
            
            self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error in authentication for client {self.client_info.client_id}: {e}")
            self._send_error_response(f"Authentication failed: {e}")
    
    def _handle_data_schema(self, message: Message):
        """Handle data schema information."""
        try:
            payload = message.payload
            schema = payload.get('schema')
            
            self.client_info.data_schema = schema
            
            # Validate schema
            if self.callback_handler.validate_data_schema(self.client_info.party_id, schema):
                response = Message(
                    msg_type=MessageType.DATA_SCHEMA,
                    payload={'status': 'success', 'schema_accepted': True}
                )
                logger.info(f"Schema accepted for client {self.client_info.client_id}")
            else:
                response = Message(
                    msg_type=MessageType.DATA_SCHEMA,
                    payload={'status': 'failed', 'reason': 'Schema validation failed'}
                )
                logger.warning(f"Schema validation failed for client {self.client_info.client_id}")
            
            self.send_message(response)
            
        except Exception as e:
            logger.error(f"Error handling data schema for client {self.client_info.client_id}: {e}")
            self._send_error_response(f"Schema processing failed: {e}")
    
    def _handle_data_chunk(self, message: Message):
        """Handle data chunk."""
        try:
            payload = message.payload
            chunk_data = payload.get('data')
            chunk_id = payload.get('chunk_id')
            
            # Store data chunk
            self.data_buffer.append({
                'chunk_id': chunk_id,
                'data': chunk_data,
                'timestamp': time.time()
            })
            
            # Send acknowledgment
            response = Message(
                msg_type=MessageType.DATA_CHUNK,
                payload={'status': 'success', 'chunk_id': chunk_id}
            )
            self.send_message(response)
            
            logger.debug(f"Received data chunk {chunk_id} from client {self.client_info.client_id}")
            
        except Exception as e:
            logger.error(f"Error handling data chunk for client {self.client_info.client_id}: {e}")
            self._send_error_response(f"Data chunk processing failed: {e}")
    
    def _handle_data_complete(self, message: Message):
        """Handle data completion signal."""
        try:
            # Reconstruct complete data from chunks
            complete_data = self._reconstruct_data()
            
            # Notify callback handler
            self.callback_handler.on_data_complete(self.client_info.party_id, complete_data)
            
            # Send completion acknowledgment
            response = Message(
                msg_type=MessageType.DATA_COMPLETE,
                payload={'status': 'success', 'data_received': True}
            )
            self.send_message(response)
            
            self.client_info.status = ClientStatus.DATA_READY
            logger.info(f"Data complete for client {self.client_info.client_id}")
            
        except Exception as e:
            logger.error(f"Error handling data completion for client {self.client_info.client_id}: {e}")
            self._send_error_response(f"Data completion failed: {e}")
    
    def _handle_heartbeat(self, message: Message):
        """Handle heartbeat message."""
        response = Message(
            msg_type=MessageType.HEARTBEAT,
            payload={'status': 'alive', 'timestamp': time.time()}
        )
        self.send_message(response)
    
    def _send_error_response(self, error_message: str):
        """Send error response to client."""
        response = Message(
            msg_type=MessageType.ERROR,
            payload={'error': error_message}
        )
        self.send_message(response)
    
    def _reconstruct_data(self) -> Any:
        """Reconstruct complete data from chunks."""
        try:
            # Sort chunks by chunk_id
            sorted_chunks = sorted(self.data_buffer, key=lambda x: x['chunk_id'])
            
            # Concatenate data
            complete_data = []
            for chunk in sorted_chunks:
                complete_data.extend(chunk['data'])
            
            return complete_data
            
        except Exception as e:
            logger.error(f"Error reconstructing data: {e}")
            raise ClientError(f"Failed to reconstruct data: {e}")

class CallbackHandler:
    """Handles callbacks for client events."""
    
    def __init__(self):
        self.auth_callback = None
        self.schema_callback = None
        self.data_callback = None
    
    def set_auth_callback(self, callback: Callable[[str, Dict[str, Any]], bool]):
        """Set authentication callback."""
        self.auth_callback = callback
    
    def set_schema_callback(self, callback: Callable[[str, Dict[str, Any]], bool]):
        """Set schema validation callback."""
        self.schema_callback = callback
    
    def set_data_callback(self, callback: Callable[[str, Any], None]):
        """Set data completion callback."""
        self.data_callback = callback
    
    def authenticate_client(self, party_id: str, credentials: Dict[str, Any]) -> bool:
        """Authenticate client."""
        if self.auth_callback:
            return self.auth_callback(party_id, credentials)
        return True  # Default: allow all
    
    def validate_data_schema(self, party_id: str, schema: Dict[str, Any]) -> bool:
        """Validate data schema."""
        if self.schema_callback:
            return self.schema_callback(party_id, schema)
        return True  # Default: accept all
    
    def on_data_complete(self, party_id: str, data: Any) -> None:
        """Handle data completion."""
        if self.data_callback:
            self.data_callback(party_id, data)

class ClientInterface:
    """Main client interface for multi-party data collection."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize client interface.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.server_socket = None
        self.ssl_context = None
        self.clients = {}
        self.message_handler = SecureMessageHandler(config.get('encryption_key'))
        self.callback_handler = CallbackHandler()
        self.running = False
        
        # Setup SSL context
        self._setup_ssl_context()
        
        # Setup callbacks
        self._setup_callbacks()
    
    def _setup_ssl_context(self):
        """Setup SSL context for secure communication."""
        try:
            if self.config.get('use_ssl', True):
                self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                self.ssl_context.load_cert_chain(
                    self.config.get('cert_file', 'server.pem'),
                    self.config.get('key_file', 'server.key')
                )
                logger.info("SSL context configured")
            
        except Exception as e:
            logger.error(f"Error setting up SSL context: {e}")
            raise ClientError(f"Failed to setup SSL: {e}")
    
    def _setup_callbacks(self):
        """Setup default callbacks."""
        self.callback_handler.set_auth_callback(self._default_auth_callback)
        self.callback_handler.set_schema_callback(self._default_schema_callback)
        self.callback_handler.set_data_callback(self._default_data_callback)
    
    def _default_auth_callback(self, party_id: str, credentials: Dict[str, Any]) -> bool:
        """Default authentication callback."""
        # Simple authentication - check if party_id is in allowed list
        allowed_parties = self.config.get('allowed_parties', [])
        return party_id in allowed_parties if allowed_parties else True
    
    def _default_schema_callback(self, party_id: str, schema: Dict[str, Any]) -> bool:
        """Default schema validation callback."""
        # Basic schema validation
        required_fields = ['features', 'samples', 'data_type']
        return all(field in schema for field in required_fields)
    
    def _default_data_callback(self, party_id: str, data: Any) -> None:
        """Default data completion callback."""
        logger.info(f"Received complete data from party {party_id}")
    
    def start_server(self, host: str = '0.0.0.0', port: int = 14000):
        """Start the client interface server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen(10)
            
            if self.ssl_context:
                self.server_socket = self.ssl_context.wrap_socket(
                    self.server_socket, 
                    server_side=True
                )
            
            self.running = True
            logger.info(f"Client interface server started on {host}:{port}")
            
            # Start accepting connections
            threading.Thread(target=self._accept_connections, daemon=True).start()
            
        except Exception as e:
            logger.error(f"Error starting server: {e}")
            raise ClientError(f"Failed to start server: {e}")
    
    def stop_server(self):
        """Stop the client interface server."""
        self.running = False
        
        # Close all client connections
        for client_handler in self.clients.values():
            client_handler.stop()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        logger.info("Client interface server stopped")
    
    def _accept_connections(self):
        """Accept incoming client connections."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_socket.settimeout(30)  # 30 second timeout
                
                # Create client info
                client_id = f"client_{len(self.clients)}_{int(time.time())}"
                client_info = ClientInfo(
                    client_id=client_id,
                    party_id="",  # Will be set during handshake
                    ip_address=client_address[0],
                    port=client_address[1],
                    status=ClientStatus.CONNECTING,
                    last_activity=time.time()
                )
                
                # Create client handler
                client_handler = ClientConnectionHandler(
                    client_socket, client_info, self.message_handler, self.callback_handler
                )
                
                self.clients[client_id] = client_handler
                client_handler.start()
                
                logger.info(f"Accepted connection from {client_address[0]}:{client_address[1]}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}")
    
    def get_client_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all connected clients."""
        status = {}
        for client_id, client_handler in self.clients.items():
            client_info = client_handler.client_info
            status[client_id] = {
                'party_id': client_info.party_id,
                'ip_address': client_info.ip_address,
                'port': client_info.port,
                'status': client_info.status.value,
                'last_activity': client_info.last_activity,
                'data_schema': client_info.data_schema
            }
        return status
    
    def broadcast_message(self, message: Message):
        """Broadcast message to all connected clients."""
        for client_handler in self.clients.values():
            if client_handler.client_info.status == ClientStatus.AUTHENTICATED:
                client_handler.send_message(message)
    
    def send_results(self, party_id: str, results: Dict[str, Any]):
        """Send analysis results to specific party."""
        for client_handler in self.clients.values():
            if client_handler.client_info.party_id == party_id:
                message = Message(
                    msg_type=MessageType.RESULT,
                    payload=results
                )
                client_handler.send_message(message)
                break
    
    def wait_for_all_parties(self, expected_parties: List[str], timeout: int = 300) -> bool:
        """Wait for all expected parties to connect and send data."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            ready_parties = set()
            for client_handler in self.clients.values():
                if (client_handler.client_info.status == ClientStatus.DATA_READY and 
                    client_handler.client_info.party_id in expected_parties):
                    ready_parties.add(client_handler.client_info.party_id)
            
            if ready_parties == set(expected_parties):
                logger.info(f"All expected parties ready: {expected_parties}")
                return True
            
            time.sleep(1)
        
        logger.warning(f"Timeout waiting for parties. Ready: {ready_parties}, Expected: {expected_parties}")
        return False
    
    def cleanup_inactive_clients(self, timeout: int = 300):
        """Clean up inactive client connections."""
        current_time = time.time()
        inactive_clients = []
        
        for client_id, client_handler in self.clients.items():
            if current_time - client_handler.client_info.last_activity > timeout:
                inactive_clients.append(client_id)
        
        for client_id in inactive_clients:
            logger.info(f"Cleaning up inactive client {client_id}")
            self.clients[client_id].stop()
            del self.clients[client_id]