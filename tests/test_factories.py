import unittest
from datetime import datetime
from src.utils.factory import BettingOddsFactory
from tests.test_data_factory import TestDataFactory, create_sample_odds


class TestBettingOddsFactory(unittest.TestCase):
    """Test cases for the production BettingOddsFactory utility."""
    
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
        custom_timestamp = datetime(2025, 1, 15, 20, 30)
        
        odds = BettingOddsFactory.create_from_basic_odds(
            source="CustomBookmaker",
            home_team="Liverpool",
            away_team="Manchester City",
            home_win=2.25,
            draw=3.10,
            away_win=3.00,
            match_id="custom_match_id",
            timestamp=custom_timestamp
        )
        
        self.assertEqual(odds.source, "CustomBookmaker")
        self.assertEqual(odds.match_id, "custom_match_id")
        self.assertEqual(odds.timestamp, custom_timestamp)


class TestDataFactoryTests(unittest.TestCase):
    """Test cases for the TestDataFactory utility."""
    
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
    
    def test_create_multiple_sources_sample(self):
        """Test creating multiple betting odds from different sources."""
        odds_list = TestDataFactory.create_multiple_sources_sample()
        
        self.assertEqual(len(odds_list), 3)
        
        # Check that all have the same match details but different sources
        sources = [odds.source for odds in odds_list]
        self.assertEqual(set(sources), {"Bookmaker_1", "Bookmaker_2", "Bookmaker_3"})
        
        # Check they all have the same match details
        for odds in odds_list:
            self.assertEqual(odds.match_id, "psg_vs_atletico_2025")
            self.assertEqual(odds.home_team, "Paris Saint-Germain")
            self.assertEqual(odds.away_team, "Atletico Madrid")
        
        # Check timestamps are consistent
        timestamps = [odds.timestamp for odds in odds_list]
        self.assertEqual(len(set(timestamps)), 1)  # All should be the same
    
    def test_create_arbitrage_opportunity_sample(self):
        """Test creating betting odds with arbitrage opportunities."""
        odds_list = TestDataFactory.create_arbitrage_opportunity_sample()
        
        self.assertEqual(len(odds_list), 2)
        
        # Check sources
        sources = [odds.source for odds in odds_list]
        self.assertEqual(set(sources), {"Bookmaker_A", "Bookmaker_B"})
        
        # Check match details
        for odds in odds_list:
            self.assertEqual(odds.match_id, "arbitrage_example")
            self.assertEqual(odds.home_team, "Team A")
            self.assertEqual(odds.away_team, "Team B")        # Verify the odds are set up for potential arbitrage
        odds_a = next(odds for odds in odds_list if odds.source == "Bookmaker_A")
        odds_b = next(odds for odds in odds_list if odds.source == "Bookmaker_B")
        
        # Bookmaker A should have better home odds
        self.assertIsNotNone(odds_a.home_win)
        self.assertIsNotNone(odds_b.home_win)
        if odds_a.home_win is not None and odds_b.home_win is not None:
            self.assertGreater(odds_a.home_win, odds_b.home_win)
        
        # Bookmaker B should have better draw and away odds
        self.assertIsNotNone(odds_a.draw)
        self.assertIsNotNone(odds_b.draw)
        if odds_a.draw is not None and odds_b.draw is not None:
            self.assertGreater(odds_b.draw, odds_a.draw)
        
        self.assertIsNotNone(odds_a.away_win)
        self.assertIsNotNone(odds_b.away_win)
        if odds_a.away_win is not None and odds_b.away_win is not None:
            self.assertGreater(odds_b.away_win, odds_a.away_win)
    
    def test_create_sample_odds_backward_compatibility(self):
        """Test backward compatibility function."""
        sample_odds = create_sample_odds()
        expected_odds = TestDataFactory.create_sample_psg_atletico()
        
        self.assertEqual(sample_odds.source, expected_odds.source)
        self.assertEqual(sample_odds.match_id, expected_odds.match_id)
        self.assertEqual(sample_odds.home_team, expected_odds.home_team)
        self.assertEqual(sample_odds.away_team, expected_odds.away_team)
    
    def test_timestamp_consistency(self):
        """Test that timestamps are consistent within a batch."""
        odds_list = TestDataFactory.create_multiple_sources_sample()
        
        # All timestamps should be the same since they're created in one batch
        timestamps = [odds.timestamp for odds in odds_list]
        self.assertEqual(len(set(timestamps)), 1)


if __name__ == '__main__':
    unittest.main()
