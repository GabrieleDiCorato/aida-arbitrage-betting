"""
Sisal website scraper for live betting odds.

This module provides functionality to scrape live betting odds from the Sisal website
and convert them into BettingOdds instances for analysis.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from ..datamodel.betting_odds import BettingOdds


class SisalScraper:
    """
    Scraper for extracting betting odds from Sisal live betting pages.
    
    This scraper is designed to work with Sisal's live betting event pages
    and extract the available odds into structured BettingOdds instances.
    """
    
    def __init__(self):
        """Initialize the scraper with appropriate headers."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def scrape_betting_odds(self, url: str) -> Optional[BettingOdds]:
        """
        Scrape betting odds from a Sisal live event page.
        
        Args:
            url: The URL of the Sisal live event page
            
        Returns:
            BettingOdds instance with the scraped data, or None if scraping fails
        """
        try:
            # Fetch the page
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract match details
            match_info = self._extract_match_info(soup, url)
            if not match_info:
                return None
            
            # Extract betting odds
            odds_data = self._extract_odds(soup)
            
            # Create BettingOdds instance
            return BettingOdds(
                timestamp=datetime.now(),
                source="Sisal",
                match_id=match_info['match_id'],
                home_team=match_info['home_team'],
                away_team=match_info['away_team'],
                **odds_data
            )
            
        except Exception as e:
            print(f"Error scraping Sisal page {url}: {e}")
            return None
    
    def _extract_match_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, str]]:
        """
        Extract match information from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            url: The original URL for fallback match_id
            
        Returns:
            Dictionary with match information or None if extraction fails
        """
        try:
            # Try to find the match title/teams
            # Look for the match header or title
            match_title_selectors = [
                'h1',
                '.match-title',
                '.event-title',
                '[data-testid*="match"]',
                '.breadcrumb',
                'title'
            ]
            
            match_title = None
            for selector in match_title_selectors:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    text = element.get_text(strip=True)
                    # Look for team names separated by common delimiters
                    if any(delimiter in text for delimiter in [' - ', ' vs ', ' v ', '–', '—']):
                        match_title = text
                        break
            
            # If still no match title, try to extract from URL
            if not match_title:
                # Extract from URL path like /spagna-u21-romania-u21
                path_parts = urlparse(url).path.split('/')
                for part in reversed(path_parts):
                    if '-' in part and len(part.split('-')) >= 2:
                        # Convert URL format to readable team names
                        teams = part.split('-')
                        # Find the split point (usually contains 'vs', 'v', or team names)
                        mid_point = len(teams) // 2
                        home_parts = teams[:mid_point]
                        away_parts = teams[mid_point:]
                        
                        home_team = ' '.join(word.capitalize() for word in home_parts)
                        away_team = ' '.join(word.capitalize() for word in away_parts)
                        
                        match_title = f"{home_team} - {away_team}"
                        break
            
            if not match_title:
                return None
            
            # Parse team names from the title
            teams = self._parse_team_names(match_title)
            if not teams:
                return None
            
            # Generate match ID from URL or teams
            match_id = self._generate_match_id(url, teams)
            
            return {
                'home_team': teams[0],
                'away_team': teams[1],
                'match_id': match_id
            }
            
        except Exception as e:
            print(f"Error extracting match info: {e}")
            return None
    
    def _parse_team_names(self, match_title: str) -> Optional[tuple]:
        """
        Parse team names from match title.
        
        Args:
            match_title: The match title string
            
        Returns:
            Tuple of (home_team, away_team) or None if parsing fails
        """
        # Common delimiters for team separation
        delimiters = [' - ', ' vs ', ' v ', '–', '—', ' VS ', ' V ']
        
        for delimiter in delimiters:
            if delimiter in match_title:
                parts = match_title.split(delimiter, 1)
                if len(parts) == 2:
                    home_team = parts[0].strip()
                    away_team = parts[1].strip()
                    
                    # Clean up team names (remove extra info like scores, time, etc.)
                    home_team = re.sub(r'\d+:\d+.*', '', home_team).strip()
                    away_team = re.sub(r'\d+:\d+.*', '', away_team).strip()
                    
                    if home_team and away_team:
                        return (home_team, away_team)
        
        return None
    
    def _generate_match_id(self, url: str, teams: tuple) -> str:
        """
        Generate a unique match ID.
        
        Args:
            url: The original URL
            teams: Tuple of (home_team, away_team)
            
        Returns:
            Generated match ID
        """
        # Try to extract a meaningful ID from URL first
        path = urlparse(url).path
        path_parts = [part for part in path.split('/') if part]
        
        if len(path_parts) >= 2:
            # Use the last part of the URL path as it usually contains the match identifier
            return path_parts[-1]
          # Fallback: generate from team names
        home_clean = re.sub(r'[^a-zA-Z0-9]', '_', teams[0].lower())
        away_clean = re.sub(r'[^a-zA-Z0-9]', '_', teams[1].lower())
        return f"{home_clean}_vs_{away_clean}"
    
    def _extract_odds(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """
        Extract betting odds from the page.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            Dictionary with extracted odds
        """
        odds_data: Dict[str, Optional[float]] = {
            'home_win': None,
            'draw': None,
            'away_win': None,
            'over_2_5': None,
            'under_2_5': None,
            'both_teams_score_yes': None,
            'both_teams_score_no': None,
            'home_or_draw': None,
            'away_or_draw': None,
            'home_or_away': None
        }
        
        try:
            # Extract 1X2 odds
            self._extract_1x2_odds(soup, odds_data)
            
            # Extract Over/Under odds
            self._extract_over_under_odds(soup, odds_data)
            
            # Extract Goal/NoGoal odds
            self._extract_goal_nogoal_odds(soup, odds_data)
            
            # Extract Double Chance odds
            self._extract_double_chance_odds(soup, odds_data)
            
        except Exception as e:
            print(f"Error extracting odds: {e}")
        
        return odds_data
    
    def _extract_1x2_odds(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract 1X2 (Match Result) odds."""
        # Look for 1X2 section patterns from the webpage content
        patterns = [
            # Based on the webpage content showing "12.75 X3.00 22.60"
            r'(\d+\.?\d*)\s*X(\d+\.?\d*)\s*(\d+\.?\d*)',
            # Alternative patterns
            r'1\s*(\d+\.?\d*)\s*X\s*(\d+\.?\d*)\s*2\s*(\d+\.?\d*)',
        ]
        
        text = soup.get_text()
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    odds_data['home_win'] = float(match.group(1))
                    odds_data['draw'] = float(match.group(2))
                    odds_data['away_win'] = float(match.group(3))
                    return
                except (ValueError, IndexError):
                    continue
        
        # Try alternative approach with CSS selectors
        selectors = [
            '.odds-1x2',
            '[data-testid*="1x2"]',
            '.match-odds',
            '.outcome-odds'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if len(elements) >= 3:
                try:
                    odds_data['home_win'] = float(elements[0].get_text(strip=True))
                    odds_data['draw'] = float(elements[1].get_text(strip=True))
                    odds_data['away_win'] = float(elements[2].get_text(strip=True))
                    return
                except (ValueError, IndexError):
                    continue
    
    def _extract_over_under_odds(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract Over/Under 2.5 goals odds."""
        # Look for "Under/Over 2.5" pattern from webpage content
        text = soup.get_text()
        
        # Pattern: "UNDER2.25 OVER1.57"
        patterns = [
            r'UNDER\s*(\d+\.?\d*)\s*OVER\s*(\d+\.?\d*)',
            r'Under\s*2\.5\s*(\d+\.?\d*)\s*Over\s*2\.5\s*(\d+\.?\d*)',
            r'U\s*2\.5\s*(\d+\.?\d*)\s*O\s*2\.5\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    odds_data['under_2_5'] = float(match.group(1))
                    odds_data['over_2_5'] = float(match.group(2))
                    return
                except (ValueError, IndexError):
                    continue
    
    def _extract_goal_nogoal_odds(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract Goal/NoGoal (Both Teams to Score) odds."""
        text = soup.get_text()
        
        # Pattern: "GOAL1.20 NOGOAL4.00"
        patterns = [
            r'GOAL\s*(\d+\.?\d*)\s*NOGOAL\s*(\d+\.?\d*)',
            r'GG\s*(\d+\.?\d*)\s*NG\s*(\d+\.?\d*)',
            r'Both.*Score.*Yes\s*(\d+\.?\d*)\s*No\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    odds_data['both_teams_score_yes'] = float(match.group(1))
                    odds_data['both_teams_score_no'] = float(match.group(2))
                    return
                except (ValueError, IndexError):
                    continue
    
    def _extract_double_chance_odds(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract Double Chance odds."""
        text = soup.get_text()
        
        # Pattern: "1X1.41 X21.37 121.31"
        patterns = [
            r'1X\s*(\d+\.?\d*)\s*X2\s*(\d+\.?\d*)\s*12\s*(\d+\.?\d*)',
            r'1X\s*(\d+\.?\d*)\s*2X\s*(\d+\.?\d*)\s*12\s*(\d+\.?\d*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    odds_data['home_or_draw'] = float(match.group(1))
                    odds_data['away_or_draw'] = float(match.group(2))
                    odds_data['home_or_away'] = float(match.group(3))
                    return
                except (ValueError, IndexError):
                    continue


def scrape_sisal_odds(url: str) -> Optional[BettingOdds]:
    """
    Convenience function to scrape odds from a Sisal URL.
    
    Args:
        url: The Sisal live event URL
        
    Returns:
        BettingOdds instance or None if scraping fails
    """
    scraper = SisalScraper()
    return scraper.scrape_betting_odds(url)
