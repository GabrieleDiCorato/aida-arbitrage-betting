from datetime import datetime
from typing import Optional
from ..datamodel.betting_odds import BettingOdds


class BettingOddsFactory:
    """
    Factory utility for creating BettingOdds instances.
    
    This class provides convenient methods for creating betting odds
    from various sources and formats in production scenarios.
    """
    
    @staticmethod
    def create_from_basic_odds(
        source: str,
        home_team: str,
        away_team: str,
        home_win: float,
        draw: float,
        away_win: float,
        match_id: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> BettingOdds:
        """
        Create a BettingOdds instance from basic 1X2 odds.
        
        Args:
            source: Name of the betting source
            home_team: Home team name
            away_team: Away team name
            home_win: Odds for home team win
            draw: Odds for draw
            away_win: Odds for away team win
            match_id: Optional match identifier
            timestamp: Optional timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        if match_id is None:
            match_id = f"{home_team.lower().replace(' ', '_')}_vs_{away_team.lower().replace(' ', '_')}"
        
        return BettingOdds(
            timestamp=timestamp,
            source=source,
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            home_win=home_win,
            draw=draw,
            away_win=away_win
        )
