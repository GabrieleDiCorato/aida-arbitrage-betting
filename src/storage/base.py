"""
Abstract base class for betting odds storage implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from ..datamodel.betting_odds import BettingOdds


class BettingOddsStorageBase(ABC):
    """
    Abstract base class for storing BettingOdds instances.
    
    Provides a common interface for different storage backends
    with session-based organization and clear lifecycle management.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize storage with optional session identifier.
        
        Args:
            session_id: Optional session identifier. If None, will be auto-generated.
        """
        self.session_id = session_id or self._generate_session_id()
        self._is_initialized = False
    
    def _generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the storage backend.
        
        This method should prepare the storage (create files, directories, etc.)
        and should be called before any store operations.
        """
        pass
    
    @abstractmethod
    def store(self, betting_odds: BettingOdds) -> None:
        """
        Store a single BettingOdds instance.
        
        Args:
            betting_odds: The betting odds instance to store.
            
        Raises:
            RuntimeError: If storage has not been initialized.
        """
        pass
    
    @abstractmethod
    def store_batch(self, betting_odds_list: List[BettingOdds]) -> None:
        """
        Store multiple BettingOdds instances in a batch operation.
        
        Args:
            betting_odds_list: List of betting odds instances to store.
            
        Raises:
            RuntimeError: If storage has not been initialized.
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        Close and cleanup the storage backend.
        
        This method should be called when finished with the storage
        to ensure proper cleanup of resources.
        """
        pass
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
    
    def _ensure_initialized(self) -> None:
        """Ensure storage has been initialized."""
        if not self._is_initialized:
            raise RuntimeError("Storage has not been initialized. Call initialize() first.")
