import unittest
from datetime import datetime
from src.utils.factory import BettingOddsFactory
from .test_data_factory import TestDataFactory, create_sample_odds


class TestBettingOddsFactory(unittest.TestCase):
    """Test cases for the BettingOddsFactory utility."""
    
    def test_create_sample_psg_atletico(self):
        """Test creating sample PSG vs Atletico odds."""
        odds = TestDataFactory.create_sample_psg_atletico()
        
        self.assertEqual(odds.source, "SampleBookmaker")
        self.assertEqual(odds.match_id, "psg_vs_atletico_2025")
        self.assertEqual(odds.home_team, "Paris Saint-Germain")
        self.assertEqual(odds.away_team, "Atletico Madrid")
        self.assertEqual(odds.home_win, 2.10)
        self.assertEqual(odds.draw, 3.40)
        self.assertEqual(odds.away_win, 3.20)
        self.assertIsInstance(odds.timestamp, datetime)
    
    def test_create_from_basic_odds(self):
        """Test creating odds from basic parameters."""
        odds = BettingOddsFactory.create_from_basic_odds(
            source="TestBookmaker",
            home_team="Real Madrid",
            away_team="Barcelona",
            home_win=1.90,
            draw=3.50,
            away_win=4.20
        )
        
        self.assertEqual(odds.source, "TestBookmaker")
        self.assertEqual(odds.home_team, "Real Madrid")
        self.assertEqual(odds.away_team, "Barcelona")
        self.assertEqual(odds.home_win, 1.90)
        self.assertEqual(odds.draw, 3.50)
        self.assertEqual(odds.away_win, 4.20)
        self.assertIsInstance(odds.timestamp, datetime)
        self.assertEqual(odds.match_id, "real_madrid_vs_barcelona")
    
    def test_create_from_basic_odds_with_custom_params(self):
        """Test creating odds with custom match_id and timestamp."""
        custom_timestamp = datetime(2025, 6, 15, 20, 0, 0)
        custom_match_id = "custom_match_123"
        
        odds = BettingOddsFactory.create_from_basic_odds(
            source="TestBookmaker",
            home_team="Team A",
            away_team="Team B",
            home_win=2.00,
            draw=3.00,
            away_win=3.50,
            match_id=custom_match_id,
            timestamp=custom_timestamp
        )
        
        self.assertEqual(odds.match_id, custom_match_id)
        self.assertEqual(odds.timestamp, custom_timestamp)
      def test_create_multiple_sources_sample(self):
        """Test creating multiple betting odds from different sources."""
        odds_list = TestDataFactory.create_multiple_sources_sample()
        
        self.assertEqual(len(odds_list), 3)
        
        # Check that all have the same match details but different sources
        sources = [odds.source for odds in odds_list]
        self.assertEqual(set(sources), {"Bookmaker_1", "Bookmaker_2", "Bookmaker_3"})
        
        # All should be for the same match
        for odds in odds_list:
            self.assertEqual(odds.match_id, "psg_vs_atletico_2025")
            self.assertEqual(odds.home_team, "Paris Saint-Germain")
            self.assertEqual(odds.away_team, "Atletico Madrid")
        
        # Should have different odds values
        home_odds = [odds.home_win for odds in odds_list]
        self.assertEqual(len(set(home_odds)), 3)  # All different
    
    def test_create_arbitrage_opportunity_sample(self):
        """Test creating betting odds with arbitrage opportunities."""
        odds_list = BettingOddsFactory.create_arbitrage_opportunity_sample()
        
        self.assertEqual(len(odds_list), 2)
        
        # Check sources
        sources = [odds.source for odds in odds_list]
        self.assertEqual(set(sources), {"Bookmaker_A", "Bookmaker_B"})
        
        # All should be for the same match
        for odds in odds_list:
            self.assertEqual(odds.match_id, "arbitrage_example")
            self.assertEqual(odds.home_team, "Team A")
            self.assertEqual(odds.away_team, "Team B")
        
        # Should have some odds that create arbitrage opportunities
        # (This is a basic check - detailed arbitrage logic is tested in ArbitrageAnalyzer tests)
        self.assertIsNotNone(odds_list[0].home_win)
        self.assertIsNotNone(odds_list[0].draw)
        self.assertIsNotNone(odds_list[0].away_win)
        self.assertIsNotNone(odds_list[1].home_win)
        self.assertIsNotNone(odds_list[1].draw)
        self.assertIsNotNone(odds_list[1].away_win)
    
    def test_create_sample_odds_backward_compatibility(self):
        """Test backward compatibility function."""
        odds = create_sample_odds()
        
        # Should be the same as create_sample_psg_atletico
        expected_odds = BettingOddsFactory.create_sample_psg_atletico()
        
        self.assertEqual(odds.source, expected_odds.source)
        self.assertEqual(odds.match_id, expected_odds.match_id)
        self.assertEqual(odds.home_team, expected_odds.home_team)
        self.assertEqual(odds.away_team, expected_odds.away_team)
        self.assertEqual(odds.home_win, expected_odds.home_win)
        self.assertEqual(odds.draw, expected_odds.draw)
        self.assertEqual(odds.away_win, expected_odds.away_win)
    
    def test_timestamp_consistency(self):
        """Test that timestamps are consistent within a batch."""
        odds_list = BettingOddsFactory.create_multiple_sources_sample()
        
        # All odds in the same batch should have the same timestamp
        timestamps = [odds.timestamp for odds in odds_list]
        self.assertEqual(len(set(timestamps)), 1)  # All same timestamp


if __name__ == '__main__':
    unittest.main()
