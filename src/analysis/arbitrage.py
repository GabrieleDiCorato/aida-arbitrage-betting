from typing import Dict, List, Any
from ..datamodel.betting_odds import BettingOdds


class ArbitrageAnalyzer:
    """
    Business logic for analyzing betting odds and finding arbitrage opportunities.
    
    This class contains the core arbitrage detection and calculation logic,
    separated from the data model.
    """
    
    @staticmethod
    def calculate_implied_probability(odds: float) -> float:
        """Calculate implied probability from decimal odds."""
        if odds <= 0:
            raise ValueError(f"Odds must be positive, got: {odds}")
        return 1.0 / odds
    
    @staticmethod
    def calculate_arbitrage_margin(probabilities: List[float]) -> float:
        """
        Calculate arbitrage margin from a list of implied probabilities.
        
        Returns:
            Negative value indicates arbitrage opportunity (profit margin)
            Positive value indicates bookmaker margin
        """
        return sum(probabilities) - 1.0
    
    @staticmethod
    def calculate_stake_distribution(odds: List[float], total_stake: float) -> List[float]:
        """
        Calculate optimal stake distribution for arbitrage betting.
        
        Args:
            odds: List of decimal odds for each outcome
            total_stake: Total amount to be staked
            
        Returns:
            List of stakes for each outcome to guarantee equal profit
        """
        if not odds or any(odd <= 0 for odd in odds):
            raise ValueError("All odds must be positive")
        
        total_inverse_odds = sum(1/odd for odd in odds)
        
        return [total_stake / (total_inverse_odds * odd) for odd in odds]
    
    @classmethod
    def find_arbitrage_opportunities(cls, odds_list: List[BettingOdds]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze multiple betting odds to find arbitrage opportunities.
        
        Args:
            odds_list: List of BettingOdds instances from different sources
            
        Returns:
            Dictionary of arbitrage opportunities with detailed information
        """
        if len(odds_list) < 2:
            return {}
        
        opportunities = {}
        
        # Check 1X2 market
        _1x2_opportunities = cls._analyze_1x2_market(odds_list)
        if _1x2_opportunities:
            opportunities.update(_1x2_opportunities)
        
        # Check Over/Under markets
        ou_opportunities = cls._analyze_over_under_markets(odds_list)
        if ou_opportunities:
            opportunities.update(ou_opportunities)
        
        # Check Both Teams to Score
        btts_opportunities = cls._analyze_btts_market(odds_list)
        if btts_opportunities:
            opportunities.update(btts_opportunities)
        
        return opportunities
    
    @staticmethod
    def calculate_potential_profit(opportunities: Dict[str, Dict[str, Any]], 
                                 total_stake: float) -> Dict[str, float]:
        """
        Calculate potential profit for each arbitrage opportunity.
        
        Args:
            opportunities: Dictionary of arbitrage opportunities
            total_stake: Total amount to stake
            
        Returns:
            Dictionary mapping opportunity names to potential profits
        """
        profits = {}
        
        for market, details in opportunities.items():
            profit_margin = details['profit_margin_percent'] / 100
            potential_profit = total_stake * profit_margin
            profits[market] = round(potential_profit, 2)
        
        return profits
    
    @classmethod
    def _analyze_1x2_market(cls, odds_list: List[BettingOdds]) -> Dict[str, Dict[str, Any]]:
        """Analyze 1X2 market for arbitrage opportunities."""
        # Filter odds with complete 1X2 data
        valid_odds = [
            odds for odds in odds_list
            if all([odds.home_win, odds.draw, odds.away_win])
        ]
        
        if len(valid_odds) < 2:
            return {}
        
        # Find best odds for each outcome
        best_home_odds = max(odds.home_win for odds in valid_odds if odds.home_win is not None)
        best_draw_odds = max(odds.draw for odds in valid_odds if odds.draw is not None)
        best_away_odds = max(odds.away_win for odds in valid_odds if odds.away_win is not None)
        
        # Find sources for best odds
        home_source = next(odds.source for odds in valid_odds if odds.home_win == best_home_odds)
        draw_source = next(odds.source for odds in valid_odds if odds.draw == best_draw_odds)
        away_source = next(odds.source for odds in valid_odds if odds.away_win == best_away_odds)
        
        # Calculate arbitrage
        probabilities = [
            cls.calculate_implied_probability(best_home_odds),
            cls.calculate_implied_probability(best_draw_odds),
            cls.calculate_implied_probability(best_away_odds)
        ]
        
        margin = cls.calculate_arbitrage_margin(probabilities)
        
        if margin < 0:  # Arbitrage opportunity
            return {
                '1x2': {
                    'profit_margin_percent': round(abs(margin) * 100, 2),
                    'total_implied_probability': round(sum(probabilities), 4),
                    'best_odds': {
                        'home': best_home_odds,
                        'draw': best_draw_odds,
                        'away': best_away_odds
                    },
                    'sources': {
                        'home': home_source,
                        'draw': draw_source,
                        'away': away_source
                    },
                    'stake_distribution_100': cls.calculate_stake_distribution(
                        [best_home_odds, best_draw_odds, best_away_odds], 100
                    )
                }
            }
        
        return {}
    
    @classmethod
    def _analyze_over_under_markets(cls, odds_list: List[BettingOdds]) -> Dict[str, Dict[str, Any]]:
        """Analyze Over/Under markets for arbitrage opportunities."""
        opportunities = {}
          # Check different Over/Under lines
        ou_markets = [
            ('over_under_2_5', 'over_2_5', 'under_2_5'),
            ('over_under_3_5', 'over_3_5', 'under_3_5')
        ]
        
        for market_name, over_attr, under_attr in ou_markets:
            valid_odds = [
                odds for odds in odds_list
                if getattr(odds, over_attr) and getattr(odds, under_attr)
            ]
            
            if len(valid_odds) < 2:
                continue
            
            best_over = max(getattr(odds, over_attr) for odds in valid_odds 
                           if getattr(odds, over_attr) is not None)
            best_under = max(getattr(odds, under_attr) for odds in valid_odds 
                            if getattr(odds, under_attr) is not None)
            
            over_source = next(odds.source for odds in valid_odds 
                              if getattr(odds, over_attr) == best_over)
            under_source = next(odds.source for odds in valid_odds 
                               if getattr(odds, under_attr) == best_under)
            
            probabilities = [
                cls.calculate_implied_probability(best_over),
                cls.calculate_implied_probability(best_under)
            ]
            
            margin = cls.calculate_arbitrage_margin(probabilities)
            
            if margin < 0:  # Arbitrage opportunity
                opportunities[market_name] = {
                    'profit_margin_percent': round(abs(margin) * 100, 2),
                    'total_implied_probability': round(sum(probabilities), 4),
                    'best_odds': {
                        'over': best_over,
                        'under': best_under
                    },
                    'sources': {
                        'over': over_source,
                        'under': under_source
                    },
                    'stake_distribution_100': cls.calculate_stake_distribution(
                        [best_over, best_under], 100
                    )
                }
        
        return opportunities
    
    @classmethod
    def _analyze_btts_market(cls, odds_list: List[BettingOdds]) -> Dict[str, Dict[str, Any]]:
        """Analyze Both Teams to Score market for arbitrage opportunities."""
        valid_odds = [
            odds for odds in odds_list
            if odds.both_teams_score_yes and odds.both_teams_score_no
        ]
        
        if len(valid_odds) < 2:
            return {}
        
        best_yes = max(odds.both_teams_score_yes for odds in valid_odds 
                      if odds.both_teams_score_yes is not None)
        best_no = max(odds.both_teams_score_no for odds in valid_odds 
                     if odds.both_teams_score_no is not None)
        
        yes_source = next(odds.source for odds in valid_odds 
                         if odds.both_teams_score_yes == best_yes)
        no_source = next(odds.source for odds in valid_odds 
                        if odds.both_teams_score_no == best_no)
        
        probabilities = [
            cls.calculate_implied_probability(best_yes),
            cls.calculate_implied_probability(best_no)
        ]
        
        margin = cls.calculate_arbitrage_margin(probabilities)
        
        if margin < 0:  # Arbitrage opportunity
            return {
                'both_teams_score': {
                    'profit_margin_percent': round(abs(margin) * 100, 2),
                    'total_implied_probability': round(sum(probabilities), 4),
                    'best_odds': {
                        'yes': best_yes,
                        'no': best_no
                    },
                    'sources': {
                        'yes': yes_source,
                        'no': no_source
                    },
                    'stake_distribution_100': cls.calculate_stake_distribution(
                        [best_yes, best_no], 100
                    )
                }
            }
        
        return {}
