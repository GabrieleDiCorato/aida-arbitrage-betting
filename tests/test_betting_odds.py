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
      # Note: to_dict() and from_dict() methods are not implemented in the current BettingOdds class
    # These tests would be relevant if serialization methods were added in the future
    
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


class TestBettingOddsImmutability(unittest.TestCase):
    """Test cases to verify the immutability of the BettingOdds dataclass."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timestamp = datetime.now()
        self.betting_odds = BettingOdds(
            timestamp=self.timestamp,
            source='TestBookmaker',
            match_id='test_match_immutable',
            home_team='Team A',
            away_team='Team B',
            home_win=2.10,
            draw=3.40,
            away_win=3.20,
            home_or_draw=1.25,
            away_or_draw=1.65,
            home_or_away=1.30,
            over_2_5=1.85,
            under_2_5=1.95,
            both_teams_score_yes=1.70,
            both_teams_score_no=2.15
        )
    
    def test_cannot_modify_core_fields(self):
        """Test that core metadata fields cannot be modified."""
        with self.assertRaises(AttributeError):
            self.betting_odds.source = 'ModifiedBookmaker'
        
        with self.assertRaises(AttributeError):
            self.betting_odds.match_id = 'modified_match'
        
        with self.assertRaises(AttributeError):
            self.betting_odds.home_team = 'Modified Team A'
        
        with self.assertRaises(AttributeError):
            self.betting_odds.away_team = 'Modified Team B'
        
        with self.assertRaises(AttributeError):
            self.betting_odds.timestamp = datetime.now()
    
    def test_cannot_modify_1x2_odds(self):
        """Test that 1X2 odds fields cannot be modified."""
        with self.assertRaises(AttributeError):
            self.betting_odds.home_win = 2.50
        
        with self.assertRaises(AttributeError):
            self.betting_odds.draw = 3.00
        
        with self.assertRaises(AttributeError):
            self.betting_odds.away_win = 4.00
    
    def test_cannot_modify_double_chance_odds(self):
        """Test that double chance odds fields cannot be modified."""
        with self.assertRaises(AttributeError):
            self.betting_odds.home_or_draw = 1.50
        
        with self.assertRaises(AttributeError):
            self.betting_odds.away_or_draw = 2.00
        
        with self.assertRaises(AttributeError):
            self.betting_odds.home_or_away = 1.80
    
    def test_cannot_modify_over_under_odds(self):
        """Test that over/under odds fields cannot be modified."""
        with self.assertRaises(AttributeError):
            self.betting_odds.over_1_5 = 1.30
        
        with self.assertRaises(AttributeError):
            self.betting_odds.under_1_5 = 3.50
        
        with self.assertRaises(AttributeError):
            self.betting_odds.over_2_5 = 2.00
        
        with self.assertRaises(AttributeError):
            self.betting_odds.under_2_5 = 2.10
        
        with self.assertRaises(AttributeError):
            self.betting_odds.over_3_5 = 3.00
        
        with self.assertRaises(AttributeError):
            self.betting_odds.under_3_5 = 1.40
    
    def test_cannot_modify_both_teams_score_odds(self):
        """Test that both teams score odds fields cannot be modified."""
        with self.assertRaises(AttributeError):
            self.betting_odds.both_teams_score_yes = 2.00
        
        with self.assertRaises(AttributeError):
            self.betting_odds.both_teams_score_no = 1.80
    
    def test_cannot_add_new_attributes(self):
        """Test that new attributes cannot be added to the instance."""
        with self.assertRaises(AttributeError):
            self.betting_odds.new_field = 'some_value'
        
        with self.assertRaises(AttributeError):
            self.betting_odds.handicap = 1.50
    
    def test_cannot_delete_attributes(self):
        """Test that existing attributes cannot be deleted."""
        with self.assertRaises(AttributeError):
            del self.betting_odds.source
        
        with self.assertRaises(AttributeError):
            del self.betting_odds.home_win
        
        with self.assertRaises(AttributeError):
            del self.betting_odds.over_2_5
    
    def test_hashable_due_to_immutability(self):
        """Test that BettingOdds instances are hashable due to immutability."""
        # Should be able to compute hash without error
        hash_value = hash(self.betting_odds)
        self.assertIsInstance(hash_value, int)
        
        # Should be able to use as dictionary key
        test_dict = {self.betting_odds: 'test_value'}
        self.assertEqual(test_dict[self.betting_odds], 'test_value')
        
        # Should be able to add to set
        test_set = {self.betting_odds}
        self.assertEqual(len(test_set), 1)
        self.assertIn(self.betting_odds, test_set)
    
    def test_equality_consistency_with_immutability(self):
        """Test that equal instances have same hash (consistency with immutability)."""
        # Create identical instance
        identical_odds = BettingOdds(
            timestamp=self.timestamp,
            source='TestBookmaker',
            match_id='test_match_immutable',
            home_team='Team A',
            away_team='Team B',
            home_win=2.10,
            draw=3.40,
            away_win=3.20,
            home_or_draw=1.25,
            away_or_draw=1.65,
            home_or_away=1.30,
            over_2_5=1.85,
            under_2_5=1.95,
            both_teams_score_yes=1.70,
            both_teams_score_no=2.15
        )
        
        # Equal instances should have same hash
        self.assertEqual(self.betting_odds, identical_odds)
        self.assertEqual(hash(self.betting_odds), hash(identical_odds))
    
    def test_immutability_with_none_values(self):
        """Test immutability with None values for optional fields."""
        minimal_odds = BettingOdds(
            timestamp=self.timestamp,
            source='TestBookmaker',
            match_id='minimal_match',
            home_team='Team A',
            away_team='Team B'
        )
        
        # Should not be able to modify None fields
        with self.assertRaises(AttributeError):
            minimal_odds.home_win = 2.50
        
        with self.assertRaises(AttributeError):
            minimal_odds.over_2_5 = 1.85
        
        with self.assertRaises(AttributeError):
            minimal_odds.both_teams_score_yes = 1.70
    
    def test_original_values_preserved(self):
        """Test that original values are preserved after failed modification attempts."""
        original_source = self.betting_odds.source
        original_home_win = self.betting_odds.home_win
        original_over_2_5 = self.betting_odds.over_2_5
        
        # Attempt modifications (should fail)
        with self.assertRaises(AttributeError):
            self.betting_odds.source = 'ModifiedBookmaker'
        
        with self.assertRaises(AttributeError):
            self.betting_odds.home_win = 999.99
        
        with self.assertRaises(AttributeError):
            self.betting_odds.over_2_5 = 999.99
        
        # Verify original values are unchanged
        self.assertEqual(self.betting_odds.source, original_source)
        self.assertEqual(self.betting_odds.home_win, original_home_win)
        self.assertEqual(self.betting_odds.over_2_5, original_over_2_5)


if __name__ == '__main__':
    unittest.main()
