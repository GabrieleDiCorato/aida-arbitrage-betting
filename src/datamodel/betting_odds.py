from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

@dataclass
class BettingOdds:
    """
    Data model for timestamped betting odds from a specific source.
    
    This class represents the core data structure for betting odds,
    focusing on data modeling and serialization only.
    """
    
    # Core metadata
    timestamp: datetime
    source: str
    match_id: str
    home_team: str
    away_team: str
    
    # Match Winner (1X2) - Most common market
    home_win: Optional[float] = None  # 1
    draw: Optional[float] = None      # X
    away_win: Optional[float] = None  # 2
    
    # Double Chance
    home_or_draw: Optional[float] = None    # 1X
    away_or_draw: Optional[float] = None    # X2
    home_or_away: Optional[float] = None    # 12
    
    # Total Goals (Over/Under)
    over_1_5: Optional[float] = None
    under_1_5: Optional[float] = None
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None
    over_3_5: Optional[float] = None
    under_3_5: Optional[float] = None

    # Both Teams to Score
    both_teams_score_yes: Optional[float] = None
    both_teams_score_no: Optional[float] = None
    
    def __post_init__(self):
        """Validate the betting odds data after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """Private method to validate betting odds data."""
        if not self.source:
            raise ValueError("Source cannot be empty")
        if not self.match_id:
            raise ValueError("Match ID cannot be empty")
        if not self.home_team or not self.away_team:
            raise ValueError("Team names cannot be empty")
            
        # Validate odds are positive if provided
        odds_fields = [
            self.home_win, self.draw, self.away_win, self.home_or_draw,
            self.away_or_draw, self.home_or_away, self.over_2_5, self.under_2_5,
            self.over_3_5, self.under_3_5,
            self.both_teams_score_yes, self.both_teams_score_no
        ]
        
        for odds in odds_fields:
            if odds is not None and odds <= 0:
                raise ValueError(f"Odds must be positive, got: {odds}")