"""
Configuration and constants for the Adaptive Evolutionary Framework.
Centralized configuration ensures consistent behavior across all modules.
"""
import os
from dataclasses import dataclass
from typing import Dict, Any
import logging

@dataclass
class FrameworkConfig:
    """Framework configuration with validation and defaults."""
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "evolution-ecosystem")
    FIREBASE_COLLECTION: str = os.getenv("FIREBASE_COLLECTION", "evolution_modules")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "./firebase-credentials.json")
    
    # RL Configuration
    RL_LEARNING_RATE: float = 0.01
    RL_DISCOUNT_FACTOR: float = 0.95
    RL_EXPLORATION_RATE: float = 0.1
    RL_MAX_MEMORY_SIZE: int = 10000
    
    # Integration Configuration
    MAX_INTEGRATION_ATTEMPTS: int = 3
    INTEGRATION_TIMEOUT_SECONDS: int = 30
    KNOWLEDGE_SHARING_INTERVAL: int = 60  # seconds
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance Monitoring
    HEALTH_CHECK_INTERVAL: int = 300  # seconds
    PERFORMANCE_METRICS_BUFFER: int = 100
    
    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []
        
        if not self.FIREBASE_PROJECT_ID:
            errors.append("FIREBASE_PROJECT_ID must be set")
        if not os.path.exists(self.FIREBASE_CREDENTIALS_PATH):
            errors.append(f"Firebase credentials not found at {self.FIREBASE_CREDENTIALS_PATH}")
        
        if self.RL_LEARNING_RATE <= 0 or self.RL_LEARNING_RATE > 1:
            errors.append(f"RL_LEARNING_RATE must be between 0 and 1, got {self.RL_LEARNING_RATE}")
        
        if errors:
            logging.error(f"Configuration validation failed: {errors}")
            return False
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for logging."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}


def setup_logging(config: FrameworkConfig) -> logging.Logger:
    """Configure centralized logging for the framework."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    logger = logging.getLogger("EvolutionFramework")
    logger.info(f"Logging initialized at level {config.LOG_LEVEL}")
    logger.debug(f"Configuration: {config.to_dict()}")
    return logger