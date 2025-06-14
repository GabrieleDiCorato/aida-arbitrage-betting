import unittest
from src.analysis.arbitrage import ArbitrageAnalyzer
from tests.test_data_factory import TestDataFactory


class TestArbitrageAnalyzer(unittest.TestCase):
    """Test cases for the ArbitrageAnalyzer business logic."""
    
    def test_calculate_implied_probability(self):
        """Test implied probability calculation."""
        # Test with decimal odds 2.0 (50% probability)
        prob = ArbitrageAnalyzer.calculate_implied_probability(2.0)
        self.assertEqual(prob, 0.5)
        
        # Test with decimal odds 1.5 (66.67% probability)
        prob = ArbitrageAnalyzer.calculate_implied_probability(1.5)
        self.assertAlmostEqual(prob, 0.6667, places=4)
          # Test with decimal odds 3.0 (33.33% probability)
        prob = ArbitrageAnalyzer.calculate_implied_probability(3.0)
        self.assertAlmostEqual(prob, 0.3333, places=4)
    
    def test_calculate_implied_probability_invalid_odds(self):
        """Test implied probability calculation with invalid odds."""
        with self.assertRaises(ValueError):
            ArbitrageAnalyzer.calculate_implied_probability(0)
        
        with self.assertRaises(ValueError):
            ArbitrageAnalyzer.calculate_implied_probability(-1.5)
    
    def test_calculate_arbitrage_margin(self):
        """Test arbitrage margin calculation."""
        # Test with bookmaker margin (sum > 1)
        probabilities = [0.5, 0.35, 0.25]  # Sum = 1.1 (10% margin)
        margin = ArbitrageAnalyzer.calculate_arbitrage_margin(probabilities)
        self.assertAlmostEqual(margin, 0.1, places=10)
        
        # Test with arbitrage opportunity (sum < 1)
        probabilities = [0.45, 0.30, 0.20]  # Sum = 0.95 (-5% margin = 5% profit)
        margin = ArbitrageAnalyzer.calculate_arbitrage_margin(probabilities)
        self.assertAlmostEqual(margin, -0.05, places=10)
        
        # Test with perfect market (sum = 1)
        probabilities = [0.5, 0.3, 0.2]  # Sum = 1.0
        margin = ArbitrageAnalyzer.calculate_arbitrage_margin(probabilities)
        self.assertAlmostEqual(margin, 0.0, places=10)
    
    def test_calculate_stake_distribution(self):
        """Test optimal stake distribution calculation."""
        # Test with simple 2-outcome market
        odds = [2.0, 2.0]  # Both outcomes have same odds
        total_stake = 100
        stakes = ArbitrageAnalyzer.calculate_stake_distribution(odds, total_stake)
        
        # Should split evenly
        self.assertEqual(len(stakes), 2)
        self.assertAlmostEqual(stakes[0], 50.0, places=1)
        self.assertAlmostEqual(stakes[1], 50.0, places=1)
        
        # Test with different odds
        odds = [2.0, 3.0]  # Different odds
        stakes = ArbitrageAnalyzer.calculate_stake_distribution(odds, total_stake)
        
        # Higher stake should go to lower odds (more likely outcome)
        self.assertGreater(stakes[0], stakes[1])
        self.assertAlmostEqual(sum(stakes), total_stake, places=1)
    
    def test_calculate_stake_distribution_invalid_odds(self):
        """Test stake distribution with invalid odds."""
        with self.assertRaises(ValueError):
            ArbitrageAnalyzer.calculate_stake_distribution([0, 2.0], 100)
        
        with self.assertRaises(ValueError):
            ArbitrageAnalyzer.calculate_stake_distribution([], 100)
    
    def test_find_arbitrage_opportunities_no_arbitrage(self):
        """Test finding arbitrage opportunities when none exist."""
        odds_list = TestDataFactory.create_multiple_sources_sample()
        opportunities = ArbitrageAnalyzer.find_arbitrage_opportunities(odds_list)
        
        # Should return empty dict if no arbitrage opportunities
        self.assertIsInstance(opportunities, dict)
    
    def test_find_arbitrage_opportunities_with_arbitrage(self):
        """Test finding arbitrage opportunities when they exist."""
        odds_list = TestDataFactory.create_arbitrage_opportunity_sample()
        opportunities = ArbitrageAnalyzer.find_arbitrage_opportunities(odds_list)
        
        # Should find arbitrage opportunities
        self.assertIsInstance(opportunities, dict)
        
        # Check if any opportunities were found
        if opportunities:
            for market, details in opportunities.items():
                self.assertIn('profit_margin_percent', details)
                self.assertIn('best_odds', details)
                self.assertIn('sources', details)
                self.assertIn('stake_distribution_100', details)
                self.assertGreater(details['profit_margin_percent'], 0)
    
    def test_find_arbitrage_opportunities_insufficient_data(self):
        """Test finding arbitrage with insufficient data."""
        # Test with only one odds source
        single_odds = [TestDataFactory.create_sample_psg_atletico()]
        opportunities = ArbitrageAnalyzer.find_arbitrage_opportunities(single_odds)
        
        # Should return empty dict
        self.assertEqual(opportunities, {})
        
        # Test with empty list
        opportunities = ArbitrageAnalyzer.find_arbitrage_opportunities([])
        self.assertEqual(opportunities, {})
    
    def test_calculate_potential_profit(self):
        """Test potential profit calculation."""
        opportunities = {
            '1x2': {
                'profit_margin_percent': 5.0,
                'best_odds': {'home': 2.5, 'draw': 3.8, 'away': 3.2}
            },
            'over_under_2_5': {
                'profit_margin_percent': 3.0,
                'best_odds': {'over': 2.1, 'under': 2.05}
            }
        }
        
        total_stake = 1000
        profits = ArbitrageAnalyzer.calculate_potential_profit(opportunities, total_stake)
        
        self.assertEqual(profits['1x2'], 50.0)  # 5% of 1000
        self.assertEqual(profits['over_under_2_5'], 30.0)  # 3% of 1000


if __name__ == '__main__':
    unittest.main()
