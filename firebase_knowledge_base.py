"""
Firebase-based knowledge storage and state management.
Handles persistence, real-time updates, and cross-module knowledge fusion.
"""
import json
import threading
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    from google.cloud import firestore as google_firestore
    from google.cloud.exceptions import GoogleCloudError
except ImportError as e:
    logging.error(f"Firebase dependencies missing: {e}")
    raise

from framework_config import FrameworkConfig


class FirebaseKnowledgeBase:
    """Firestore-based knowledge storage with real-time capabilities."""
    
    def __init__(self, config: FrameworkConfig):
        """Initialize Firebase connection with error handling."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._lock = threading.RLock()
        self._initialized = False
        self._client = None
        self._listeners = {}
        
        try:
            self._initialize_firebase()
            self._initialized = True
            self.logger.info("Firebase Knowledge Base initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def _initialize_firebase(self) -> None:
        """Initialize Firebase app and Firestore client."""
        if not firebase_admin._apps:
            if not os.path.exists(self.config.FIREBASE_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Firebase credentials file not found at {self.config.FIREBASE_CREDENTIALS_PATH}"
                )
            
            cred = credentials.Certificate(self.config.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'projectId': self.config.FIREBASE_PROJECT_ID
            })
        
        self._client = firestore.client()
        
        # Test connection
        test_doc = self._client.collection('health_checks').document('connection_test')
        test_doc.set({'timestamp': datetime.utcnow().isoformat(), 'status': 'connected'})
        self.logger.debug("Firebase connection test successful")
    
    def store_knowledge(self, module_id: str, knowledge: Dict[str, Any], 
                       metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Store knowledge with metadata and timestamp."""
        if not self._initialized or not self._client:
            self.logger.error("Firebase not initialized")
            return False
        
        try:
            with self._lock:
                doc_ref = self._client.collection(self.config.FIREBASE_COLLECTION).document(module_id)
                
                knowledge_record = {
                    'knowledge': knowledge,
                    'metadata': metadata or {},
                    'timestamp': datetime.utcnow().isoformat(),
                    'version': self._get_next_version(module_id)
                }
                
                doc_ref.set(knowledge_record)
                self.logger.info(f"Knowledge stored for module {module_id}, version {knowledge_record['version']}")
                return True
                
        except GoogleCloudError as e:
            self.logger.error(f"Firestore error storing knowledge: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error storing knowledge: {e}")
            return False
    
    def retrieve_knowledge(self, module_id: str, 
                          version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Retrieve knowledge, optionally by version."""
        if not self._initialized or not self._client:
            self.logger.error("Firebase not initialized")
            return None
        
        try:
            doc_ref = self._client.collection(self.config.FIREBASE_COLLECTION).document(module_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                self.logger.warning(f"No knowledge found for module {module_id}")
                return None
            
            data = doc.to_dict()
            
            # Filter by version if specified
            if version is not None and data.get('version') != version: