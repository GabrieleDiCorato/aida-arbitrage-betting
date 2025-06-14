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
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None
    over_3_5: Optional[float] = None
    under_3_5: Optional[float] = None

    # Both Teams to Score
    both_teams_score_yes: Optional[float] = None
    both_teams_score_no: Optional[float] = None

    # First Half Markets
    first_half_home_win: Optional[float] = None
    first_half_draw: Optional[float] = None
    first_half_away_win: Optional[float] = None
    
    # Second Half Markets
    second_half_home_win: Optional[float] = None
    second_half_draw: Optional[float] = None
    second_half_away_win: Optional[float] = None
    
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
            raise ValueError("Team names cannot be empty")        # Validate odds are positive if provided
        odds_fields = [
            self.home_win, self.draw, self.away_win, self.home_or_draw,
            self.away_or_draw, self.home_or_away, self.over_2_5, self.under_2_5,
            self.over_3_5, self.under_3_5,
            self.both_teams_score_yes, self.both_teams_score_no,
            self.first_half_home_win, self.first_half_draw, self.first_half_away_win,
            self.second_half_home_win, self.second_half_draw, self.second_half_away_win
        ]
        
        for odds in odds_fields:
            if odds is not None and odds <= 0:
                raise ValueError(f"Odds must be positive, got: {odds}")
      
    def to_dict(self) -> Dict[str, Any]:
        """Convert the betting odds to a dictionary for storage."""
        return {
            'timestamp': self.timestamp,
            'source': self.source,
            'match_id': self.match_id,
            'home_team': self.home_team,
            'away_team': self.away_team,
            'odds': {
                # 1X2 Market
                '1x2': {
                    'home_win': self.home_win,
                    'draw': self.draw,
                    'away_win': self.away_win
                },
                # Double Chance
                'double_chance': {
                    'home_or_draw': self.home_or_draw,
                    'away_or_draw': self.away_or_draw,
                    'home_or_away': self.home_or_away
                },                # Total Goals
                'total_goals': {
                    'over_2_5': self.over_2_5,
                    'under_2_5': self.under_2_5,
                    'over_3_5': self.over_3_5,
                    'under_3_5': self.under_3_5
                },
                # Both Teams to Score
                'both_teams_score': {
                    'yes': self.both_teams_score_yes,
                    'no': self.both_teams_score_no                },
                # First Half
                'first_half': {
                    'home_win': self.first_half_home_win,
                    'draw': self.first_half_draw,                    
                    'away_win': self.first_half_away_win
                },
                # Second Half
                'second_half': {
                    'home_win': self.second_half_home_win,
                    'draw': self.second_half_draw,                    
                    'away_win': self.second_half_away_win
                }
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BettingOdds':
        """Create a BettingOdds instance from a dictionary."""
        odds = data.get('odds', {})
        
        return cls(
            timestamp=data['timestamp'],
            source=data['source'],
            match_id=data['match_id'],
            home_team=data['home_team'],
            away_team=data['away_team'],
            
            # 1X2
            home_win=odds.get('1x2', {}).get('home_win'),
            draw=odds.get('1x2', {}).get('draw'),
            away_win=odds.get('1x2', {}).get('away_win'),
            
            # Double Chance
            home_or_draw=odds.get('double_chance', {}).get('home_or_draw'),
            away_or_draw=odds.get('double_chance', {}).get('away_or_draw'),
            home_or_away=odds.get('double_chance', {}).get('home_or_away'),
              # Total Goals
            over_2_5=odds.get('total_goals', {}).get('over_2_5'),
            under_2_5=odds.get('total_goals', {}).get('under_2_5'),
            over_3_5=odds.get('total_goals', {}).get('over_3_5'),
            under_3_5=odds.get('total_goals', {}).get('under_3_5'),
              # Both Teams to Score
            both_teams_score_yes=odds.get('both_teams_score', {}).get('yes'),
            both_teams_score_no=odds.get('both_teams_score', {}).get('no'),
              # First Half
            first_half_home_win=odds.get('first_half', {}).get('home_win'),
            first_half_draw=odds.get('first_half', {}).get('draw'),
            first_half_away_win=odds.get('first_half', {}).get('away_win'),
              # Second Half
            second_half_home_win=odds.get('second_half', {}).get('home_win'),
            second_half_draw=odds.get('second_half', {}).get('draw'),
            second_half_away_win=odds.get('second_half', {}).get('away_win')
        )
