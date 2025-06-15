"""
Storage package for persisting betting odds data.

This package provides file-based storage implementations for BettingOdds instances
with support for multiple formats and clear separation of concerns.
"""

from .base import BettingOddsStorageBase
from .csv_storage import CSVBettingOddsStorage

__all__ = ['BettingOddsStorageBase', 'CSVBettingOddsStorage']
