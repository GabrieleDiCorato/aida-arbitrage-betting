"""
CSV-based storage implementation for betting odds data.
"""

import csv
from pathlib import Path
from typing import List, Optional
from .base import BettingOddsStorageBase
from ..datamodel.betting_odds import BettingOdds

class CSVBettingOddsStorage(BettingOddsStorageBase):
    """
    CSV file-based storage for BettingOdds instances.
    
    Stores betting odds data in CSV format with automatic header generation
    and session-based file organization.
    """
    
    def __init__(self, 
                 session_id: Optional[str] = None, 
                 output_dir: str = "data",
                 filename_prefix: str = "sisal_odds"):
        """
        Initialize CSV storage.
        
        Args:
            session_id: Optional session identifier. If None, will be auto-generated.
            output_dir: Directory where CSV files will be stored.
            filename_prefix: Prefix for the CSV filename.
        """
        super().__init__(session_id)
        self.output_dir = Path(output_dir)
        self.filename_prefix = filename_prefix
        self.csv_file_path: Optional[Path] = None
        
        self._fieldnames = [
            'timestamp', 'source', 'match_id', 'home_team', 'away_team',
            'home_win', 'draw', 'away_win',
            'home_or_draw', 'away_or_draw', 'home_or_away',
            'over_1_5', 'under_1_5', 'over_2_5', 'under_2_5', 'over_3_5', 'under_3_5',
            'both_teams_score_yes', 'both_teams_score_no'
        ]
    
    def initialize(self) -> None:
        """Initialize the CSV storage by creating directory and file."""
        if self._is_initialized:
            return
            
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate CSV file path
        csv_filename = f"{self.filename_prefix}_{self.session_id}.csv"
        self.csv_file_path = self.output_dir / csv_filename
        
        # Write header if file doesn't exist
        if not self.csv_file_path.exists():
            self._write_header()
        
        self._is_initialized = True
        print(f"✓ CSV storage initialized: {self.csv_file_path}")
    
    def store(self, betting_odds: BettingOdds) -> None:
        """
        Store a single BettingOdds instance to CSV.
        
        Args:
            betting_odds: The betting odds instance to store.
        """
        self._ensure_initialized()
        
        if not self.csv_file_path:
            raise RuntimeError("CSV file path not initialized")
        
        csv_row = self._betting_odds_to_row(betting_odds)
        
        try:
            with open(str(self.csv_file_path), 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self._fieldnames)
                writer.writerow(csv_row)
            
            print(f"✓ Stored odds for {betting_odds.home_team} vs {betting_odds.away_team}")
            
        except Exception as e:
            print(f"✗ CSV storage error: {e}")
            raise
    
    def store_batch(self, betting_odds_list: List[BettingOdds]) -> None:
        """
        Store multiple BettingOdds instances in a batch operation.
        
        Args:
            betting_odds_list: List of betting odds instances to store.
        """
        self._ensure_initialized()
        
        if not betting_odds_list:
            return
            
        if not self.csv_file_path:
            raise RuntimeError("CSV file path not initialized")
        
        try:
            with open(str(self.csv_file_path), 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self._fieldnames)
                
                for betting_odds in betting_odds_list:
                    csv_row = self._betting_odds_to_row(betting_odds)
                    writer.writerow(csv_row)
            
            print(f"✓ Stored batch of {len(betting_odds_list)} betting odds records")
            
        except Exception as e:
            print(f"✗ CSV batch storage error: {e}")
            raise
    
    def close(self) -> None:
        """Close the CSV storage and cleanup resources."""
        if self._is_initialized:
            print(f"✓ CSV storage session closed: {self.csv_file_path}")
            self._is_initialized = False
    
    def get_file_path(self) -> Optional[Path]:
        """Get the path to the CSV file."""
        return self.csv_file_path
    
    def _write_header(self) -> None:
        """Write CSV header to file."""
        if not self.csv_file_path:
            raise RuntimeError("CSV file path not initialized")
            
        try:
            with open(str(self.csv_file_path), 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self._fieldnames)
                writer.writeheader()
        except Exception as e:
            print(f"✗ Error writing CSV header: {e}")
            raise
    
    def _betting_odds_to_row(self, betting_odds: BettingOdds) -> dict:
        """
        Convert a BettingOdds instance to a CSV row dictionary.
        
        Args:
            betting_odds: The betting odds instance to convert.
            
        Returns:
            Dictionary mapping fieldnames to values.
        """
        return {
            'timestamp': betting_odds.timestamp.isoformat(),
            'source': betting_odds.source,
            'match_id': betting_odds.match_id,
            'home_team': betting_odds.home_team,
            'away_team': betting_odds.away_team,
            'home_win': betting_odds.home_win,
            'draw': betting_odds.draw,
            'away_win': betting_odds.away_win,
            'home_or_draw': betting_odds.home_or_draw,
            'away_or_draw': betting_odds.away_or_draw,            'home_or_away': betting_odds.home_or_away,
            'over_1_5': betting_odds.over_1_5,
            'under_1_5': betting_odds.under_1_5,
            'over_2_5': betting_odds.over_2_5,
            'under_2_5': betting_odds.under_2_5,
            'over_3_5': betting_odds.over_3_5,
            'under_3_5': betting_odds.under_3_5,
            'both_teams_score_yes': betting_odds.both_teams_score_yes,
            'both_teams_score_no': betting_odds.both_teams_score_no
        }
