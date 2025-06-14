"""
Test utilities for creating sample betting odds data.

This module contains factory methods specifically designed for testing
and demonstrating the betting odds system.
"""

from datetime import datetime
from typing import List
from src.datamodel.betting_odds import BettingOdds


class TestDataFactory:
    """
    Factory for creating test and sample betting odds data.
    
    This class provides methods for creating various types of betting odds
    specifically for testing, examples, and demonstrations.
    """
    
    @staticmethod
    def create_sample_psg_atletico() -> BettingOdds:
        """Create a sample BettingOdds instance for PSG vs Atletico Madrid."""
        return BettingOdds(
            timestamp=datetime.now(),
            source="SampleBookmaker",
            match_id="psg_vs_atletico_2025",
            home_team="Paris Saint-Germain",
            away_team="Atletico Madrid",
            home_win=2.10,
            draw=3.40,
            away_win=3.20,
            over_2_5=1.85,
            under_2_5=1.95,
            both_teams_score_yes=1.70,
            both_teams_score_no=2.15,
            home_or_draw=1.25,
            away_or_draw=1.65,
            home_or_away=1.30
        )
    
    @staticmethod
    def create_multiple_sources_sample() -> List[BettingOdds]:
        """Create multiple BettingOdds instances from different sources for testing arbitrage."""
        timestamp = datetime.now()
        
        return [
            # Bookmaker 1 - Better home odds
            BettingOdds(
                timestamp=timestamp,
                source="Bookmaker_1",
                match_id="psg_vs_atletico_2025",
                home_team="Paris Saint-Germain",
                away_team="Atletico Madrid",
                home_win=2.20,  # Better home odds
                draw=3.30,
                away_win=3.10,
                over_2_5=1.80,
                under_2_5=2.00,
                both_teams_score_yes=1.65,
                both_teams_score_no=2.20
            ),
            
            # Bookmaker 2 - Better draw and away odds
            BettingOdds(
                timestamp=timestamp,
                source="Bookmaker_2",
                match_id="psg_vs_atletico_2025",
                home_team="Paris Saint-Germain",
                away_team="Atletico Madrid",
                home_win=2.05,
                draw=3.50,  # Better draw odds
                away_win=3.40,  # Better away odds
                over_2_5=1.90,  # Better over odds
                under_2_5=1.90,
                both_teams_score_yes=1.75,
                both_teams_score_no=2.10
            ),
            
            # Bookmaker 3 - Different market strengths
            BettingOdds(
                timestamp=timestamp,
                source="Bookmaker_3",
                match_id="psg_vs_atletico_2025",
                home_team="Paris Saint-Germain",
                away_team="Atletico Madrid",
                home_win=2.15,
                draw=3.35,
                away_win=3.25,
                over_2_5=1.85,
                under_2_5=2.05,  # Better under odds
                both_teams_score_yes=1.80,  # Better BTTS yes odds
                both_teams_score_no=2.00
            )
        ]
    
    @staticmethod
    def create_arbitrage_opportunity_sample() -> List[BettingOdds]:
        """Create BettingOdds instances that contain a clear arbitrage opportunity."""
        timestamp = datetime.now()
        
        return [
            # Bookmaker A - Excellent home odds
            BettingOdds(
                timestamp=timestamp,
                source="Bookmaker_A",
                match_id="arbitrage_example",
                home_team="Team A",
                away_team="Team B",
                home_win=2.50,  # High home odds
                draw=3.20,
                away_win=2.80,
                over_2_5=2.10,  # High over odds
                under_2_5=1.80
            ),
            
            # Bookmaker B - Excellent draw and away odds
            BettingOdds(
                timestamp=timestamp,
                source="Bookmaker_B",
                match_id="arbitrage_example",
                home_team="Team A",
                away_team="Team B",
                home_win=2.10,
                draw=3.80,  # High draw odds
                away_win=3.20,  # High away odds
                over_2_5=1.85,
                under_2_5=2.05  # High under odds
            )
        ]


def create_sample_odds() -> BettingOdds:
    """
    Convenience function for creating sample odds.
    Kept for backward compatibility.
    """
    return TestDataFactory.create_sample_psg_atletico()
