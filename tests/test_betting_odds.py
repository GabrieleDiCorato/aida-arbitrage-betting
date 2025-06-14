import unittest
from datetime import datetime
from src.datamodel.betting_odds import BettingOdds


class TestBettingOdds(unittest.TestCase):
    """Test cases for the BettingOdds data model."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
        self.valid_odds_data = {
            'timestamp': self.timestamp,
            'source': 'TestBookmaker',
            'match_id': 'test_match',
            'home_team': 'Team A',
            'away_team': 'Team B',
            'home_win': 2.10,
            'draw': 3.40,
            'away_win': 3.20
        }
    
    def test_valid_odds_creation(self):
        """Test creating a valid BettingOdds instance."""
        odds = BettingOdds(**self.valid_odds_data)
        
        self.assertEqual(odds.timestamp, self.timestamp)
        self.assertEqual(odds.source, 'TestBookmaker')
        self.assertEqual(odds.match_id, 'test_match')
        self.assertEqual(odds.home_team, 'Team A')
        self.assertEqual(odds.away_team, 'Team B')
        self.assertEqual(odds.home_win, 2.10)
        self.assertEqual(odds.draw, 3.40)
        self.assertEqual(odds.away_win, 3.20)
    
    def test_empty_source_validation(self):
        """Test validation fails for empty source."""
        invalid_data = self.valid_odds_data.copy()
        invalid_data['source'] = ''
        
        with self.assertRaises(ValueError) as context:
            BettingOdds(**invalid_data)
        
        self.assertIn('Source cannot be empty', str(context.exception))
    
    def test_empty_match_id_validation(self):
        """Test validation fails for empty match_id."""
        invalid_data = self.valid_odds_data.copy()
        invalid_data['match_id'] = ''
        
        with self.assertRaises(ValueError) as context:
            BettingOdds(**invalid_data)
        
        self.assertIn('Match ID cannot be empty', str(context.exception))
    
    def test_empty_team_names_validation(self):
        """Test validation fails for empty team names."""
        invalid_data = self.valid_odds_data.copy()
        invalid_data['home_team'] = ''
        
        with self.assertRaises(ValueError) as context:
            BettingOdds(**invalid_data)
        
        self.assertIn('Team names cannot be empty', str(context.exception))
    
    def test_negative_odds_validation(self):
        """Test validation fails for negative odds."""
        invalid_data = self.valid_odds_data.copy()
        invalid_data['home_win'] = -1.5
        
        with self.assertRaises(ValueError) as context:
            BettingOdds(**invalid_data)
        
        self.assertIn('Odds must be positive', str(context.exception))
    
    def test_to_dict_conversion(self):
        """Test converting BettingOdds to dictionary."""
        odds = BettingOdds(**self.valid_odds_data)
        odds_dict = odds.to_dict()
        
        self.assertEqual(odds_dict['timestamp'], self.timestamp)
        self.assertEqual(odds_dict['source'], 'TestBookmaker')
        self.assertEqual(odds_dict['match_id'], 'test_match')
        self.assertEqual(odds_dict['home_team'], 'Team A')
        self.assertEqual(odds_dict['away_team'], 'Team B')
          # Check odds structure
        self.assertEqual(odds_dict['odds']['1x2']['home_win'], 2.10)
        self.assertEqual(odds_dict['odds']['1x2']['draw'], 3.40)
        self.assertEqual(odds_dict['odds']['1x2']['away_win'], 3.20)
    
    def test_from_dict_conversion(self):
        """Test creating BettingOdds from dictionary."""
        odds = BettingOdds(**self.valid_odds_data)
        odds_dict = odds.to_dict()
        
        # Convert back from dictionary
        recreated_odds = BettingOdds.from_dict(odds_dict)
        
        self.assertEqual(recreated_odds.timestamp, self.timestamp)
        self.assertEqual(recreated_odds.source, 'TestBookmaker')
        self.assertEqual(recreated_odds.match_id, 'test_match')
        self.assertEqual(recreated_odds.home_team, 'Team A')
        self.assertEqual(recreated_odds.away_team, 'Team B')
        self.assertEqual(recreated_odds.home_win, 2.10)
        self.assertEqual(recreated_odds.draw, 3.40)
        self.assertEqual(recreated_odds.away_win, 3.20)
    
    def test_optional_fields_default_values(self):
        """Test that optional fields have correct default values."""
        odds = BettingOdds(**self.valid_odds_data)
        
        # Check that optional odds are None by default
        self.assertIsNone(odds.over_2_5)
        self.assertIsNone(odds.under_2_5)
        self.assertIsNone(odds.both_teams_score_yes)
        self.assertIsNone(odds.both_teams_score_no)
    
    def test_complete_odds_data(self):
        """Test creating BettingOdds with complete data."""
        complete_data = self.valid_odds_data.copy()
        complete_data.update({
            'over_2_5': 1.85,
            'under_2_5': 1.95,
            'both_teams_score_yes': 1.70,
            'both_teams_score_no': 2.15
        })
        
        odds = BettingOdds(**complete_data)
        
        self.assertEqual(odds.over_2_5, 1.85)
        self.assertEqual(odds.under_2_5, 1.95)
        self.assertEqual(odds.both_teams_score_yes, 1.70)
        self.assertEqual(odds.both_teams_score_no, 2.15)


if __name__ == '__main__':
    unittest.main()
