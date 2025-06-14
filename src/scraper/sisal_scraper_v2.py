"""
Advanced Sisal website scraper for live betting odds.

This module provides enhanced functionality to scrape live betting odds from the Sisal website
with multiple anti-detection strategies and robust error handling.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import random
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from ..datamodel.betting_odds import BettingOdds


class SisalScraper:
    """
    Advanced scraper for extracting betting odds from Sisal live betting pages.
    
    This scraper implements multiple anti-detection techniques and fallback methods
    to successfully extract odds from Sisal's live betting platform.
    """
    
    def __init__(self):
        """Initialize the scraper with advanced anti-detection measures."""
        self.session = requests.Session()
        self._setup_session()
        self.max_retries = 3
        self.base_delay = 2
        
    def _setup_session(self):
        """Setup session with realistic browser characteristics."""
        # Realistic headers that mimic a real Chrome browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        })
        
        # Set cookies that might be expected
        self.session.cookies.update({
            'cookieconsent_status': 'dismiss',
            'language': 'it',
            'currency': 'EUR'
        })
        
    def _get_random_delay(self) -> float:
        """Get a random delay to simulate human behavior."""
        return random.uniform(self.base_delay, self.base_delay * 2.5)
    
    def scrape_betting_odds(self, url: str) -> Optional[BettingOdds]:
        """
        Scrape betting odds using multiple strategies and anti-detection measures.
        
        Args:
            url: The URL of the Sisal live event page
            
        Returns:
            BettingOdds instance with the scraped data, or None if scraping fails
        """
        print(f"🎯 Starting advanced scraping for: {url}")
        
        # Try multiple strategies in order of preference
        strategies = [
            self._scrape_with_session_establishment,
            self._scrape_with_mobile_headers,
            self._scrape_with_minimal_headers,
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                print(f"📋 Trying strategy {i}/{len(strategies)}: {strategy.__name__}")
                result = strategy(url)
                if result:
                    print(f"✅ Success with strategy {i}")
                    return result
                else:
                    print(f"❌ Strategy {i} returned no result")
            except Exception as e:
                print(f"❌ Strategy {i} error: {e}")
            
            # Wait between strategies
            if i < len(strategies):
                delay = self._get_random_delay()
                print(f"⏱️ Waiting {delay:.1f}s before next strategy...")
                time.sleep(delay)
        
        print("🚫 All strategies failed")
        return None
    
    def _scrape_with_session_establishment(self, url: str) -> Optional[BettingOdds]:
        """Primary strategy: Full session establishment like a real browser."""
        print("  🌐 Establishing full browser session...")
        
        try:
            # Step 1: Visit homepage
            print("  📄 Visiting homepage...")
            home_resp = self.session.get('https://www.sisal.it', timeout=20)
            if home_resp.status_code != 200:
                print(f"  ❌ Homepage failed: {home_resp.status_code}")
                return None
            
            time.sleep(self._get_random_delay())
            
            # Step 2: Visit live betting section
            print("  🎲 Visiting live betting section...")
            self.session.headers.update({
                'Referer': 'https://www.sisal.it',
                'Sec-Fetch-Site': 'same-origin'
            })
            
            live_resp = self.session.get('https://www.sisal.it/scommesse-live', timeout=20)
            if live_resp.status_code != 200:
                print(f"  ❌ Live section failed: {live_resp.status_code}")
                return None
            
            time.sleep(self._get_random_delay())
            
            # Step 3: Finally visit target page
            print("  🎯 Visiting target page...")
            self.session.headers.update({
                'Referer': 'https://www.sisal.it/scommesse-live'
            })
            
            response = self.session.get(url, timeout=30)
            return self._process_response(response, url)
            
        except Exception as e:
            print(f"  ❌ Session establishment failed: {e}")
            return None
    
    def _scrape_with_mobile_headers(self, url: str) -> Optional[BettingOdds]:
        """Alternative strategy: Use mobile headers (often less protected)."""
        print("  📱 Trying mobile headers...")
        
        try:
            mobile_session = requests.Session()
            mobile_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            })
            
            response = mobile_session.get(url, timeout=25)
            return self._process_response(response, url)
            
        except Exception as e:
            print(f"  ❌ Mobile headers failed: {e}")
            return None
    
    def _scrape_with_minimal_headers(self, url: str) -> Optional[BettingOdds]:
        """Minimal headers strategy: Sometimes less is more."""
        print("  🎯 Trying minimal headers...")
        
        try:
            minimal_session = requests.Session()
            minimal_session.headers.clear()
            minimal_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            })
            
            response = minimal_session.get(url, timeout=25)
            return self._process_response(response, url)
            
        except Exception as e:
            print(f"  ❌ Minimal headers failed: {e}")
            return None
    
    def _process_response(self, response: requests.Response, url: str) -> Optional[BettingOdds]:
        """Process the response and extract betting odds."""
        try:
            if response.status_code != 200:
                print(f"  ❌ HTTP {response.status_code}: {response.reason}")
                return None
            
            # Check for blocking indicators
            if self._is_blocked(response):
                print("  🚫 Response indicates blocking")
                return None
            
            # Check content length
            content_length = len(response.content)
            print(f"  📄 Content length: {content_length} bytes")
            
            if content_length < 1000:
                print("  ⚠️ Suspiciously small content, but continuing...")
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: Print some of the content to see what we got
            title = soup.find('title')
            if title:
                print(f"  📋 Page title: {title.get_text()[:100]}")
            
            # Look for betting-related content
            text_content = soup.get_text()
            betting_keywords = ['odds', 'quote', 'scommesse', 'calcio', '1x2', 'goal']
            found_keywords = [kw for kw in betting_keywords if kw in text_content.lower()]
            
            if found_keywords:
                print(f"  ✅ Found betting keywords: {', '.join(found_keywords)}")
            else:
                print("  ⚠️ No obvious betting content found")
                # Let's see what content we actually got
                sample_text = ' '.join(text_content.split()[:20])
                print(f"  📝 Sample content: {sample_text}")
            
            # Extract match details
            match_info = self._extract_match_info(soup, url)
            if not match_info:
                print("  ❌ Could not extract match info")
                return None
            
            print(f"  🏆 Match: {match_info['home_team']} vs {match_info['away_team']}")
            
            # Extract betting odds
            odds_data = self._extract_odds(soup)
            odds_found = sum(1 for v in odds_data.values() if v is not None)
            print(f"  🎲 Extracted {odds_found} odds values")
            
            if odds_found == 0:
                print("  ❌ No odds found in content")
                return None
            
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
            print(f"  ❌ Processing error: {e}")
            return None
    
    def _is_blocked(self, response: requests.Response) -> bool:
        """Enhanced blocking detection."""
        # HTTP status codes that indicate blocking
        if response.status_code in [403, 429, 503, 520, 521, 522, 523, 524]:
            return True
        
        # Check response headers for blocking indicators
        headers = str(response.headers).lower()
        if any(indicator in headers for indicator in [
            'cloudflare', 'ddos-protection', 'security-check', 'rate-limit'
        ]):
            return True
        
        # Check content for blocking indicators
        content = response.text.lower()
        blocking_indicators = [
            'access denied', 'blocked', 'forbidden', 'captcha',
            'security check', 'please verify', 'unusual activity',
            'bot detected', 'automated', 'rate limit', 'too many requests',
            'cloudflare', 'ray id', 'error 1020', 'error 1015',
            'checking your browser', 'please wait', 'human verification'
        ]
        
        for indicator in blocking_indicators:
            if indicator in content:
                return True
        
        # Check for JavaScript challenges (but be careful not to trigger on normal JS)
        js_challenge_patterns = [
            'please enable javascript',
            'javascript is required',
            'turn on javascript'
        ]
        
        for pattern in js_challenge_patterns:
            if pattern in content:
                return True
        
        return False
    
    def _extract_match_info(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, str]]:
        """Enhanced match info extraction with multiple fallback strategies."""
        try:
            # Strategy 1: Look for title or header elements
            title_selectors = [
                'title', 'h1', 'h2', '.match-title', '.event-title',
                '[data-testid*="match"]', '[data-testid*="event"]',
                '.match-header', '.event-header', '.game-title'
            ]
            
            match_title = None
            for selector in title_selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if self._looks_like_match_title(text):
                        match_title = text
                        break
                if match_title:
                    break
            
            # Strategy 2: Look in breadcrumbs or navigation
            if not match_title:
                breadcrumb_selectors = ['.breadcrumb', '.nav', 'nav', '[role="navigation"]']
                for selector in breadcrumb_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True)
                        if self._looks_like_match_title(text):
                            match_title = text
                            break
                    if match_title:
                        break
            
            # Strategy 3: Extract from URL
            if not match_title:
                match_title = self._extract_match_from_url(url)
              # Strategy 4: Look for team names in meta tags
            if not match_title:
                meta_elements = soup.select('meta[name="description"], meta[property="og:title"]')
                for element in meta_elements:
                    content = element.get('content')
                    if content and isinstance(content, str) and self._looks_like_match_title(content):
                        match_title = content
                        break
            
            if not match_title:
                print("  ❌ Could not find match title anywhere")
                return None
            
            print(f"  📋 Found match title: {match_title}")
            
            # Parse team names
            teams = self._parse_team_names(str(match_title))
            if not teams:
                print(f"  ❌ Could not parse teams from: {match_title}")
                return None
            
            # Generate match ID
            match_id = self._generate_match_id(url, teams)
            
            return {
                'home_team': teams[0],
                'away_team': teams[1],
                'match_id': match_id
            }
            
        except Exception as e:
            print(f"  ❌ Match info extraction error: {e}")
            return None
    
    def _looks_like_match_title(self, text: str) -> bool:
        """Check if text looks like a match title."""
        if not text or len(text) < 5:
            return False
        
        # Must contain team separator
        separators = [' - ', ' vs ', ' v ', '–', '—', ' VS ', ' V ']
        has_separator = any(sep in text for sep in separators)
        
        # Should not be too long (probably not a match title)
        if len(text) > 200:
            return False
        
        # Should be reasonable length for team names
        if len(text.split()) > 12:
            return False
        
        return has_separator
    
    def _extract_match_from_url(self, url: str) -> Optional[str]:
        """Extract match info from URL path."""
        try:
            path_parts = urlparse(url).path.split('/')
            # Look for the match identifier (usually the last meaningful part)
            for part in reversed(path_parts):
                if '-' in part and len(part) > 10:
                    # Convert URL format to readable team names
                    teams = part.split('-')
                    if len(teams) >= 2:
                        # Try to find a reasonable split point
                        mid = len(teams) // 2
                        home_parts = teams[:mid]
                        away_parts = teams[mid:]
                        
                        home_team = ' '.join(word.capitalize() for word in home_parts)
                        away_team = ' '.join(word.capitalize() for word in away_parts)
                        
                        return f"{home_team} - {away_team}"
        except Exception:
            pass
        return None
    
    def _parse_team_names(self, match_title: str) -> Optional[tuple]:
        """Parse team names from match title."""
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
        """Generate a unique match ID."""
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
        """Extract betting odds from the page."""
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
            print(f"  ❌ Error extracting odds: {e}")
        
        return odds_data
    
    def _extract_1x2_odds(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract 1X2 (Match Result) odds."""
        text = soup.get_text()
        
        # Look for 1X2 section patterns from the webpage content
        patterns = [
            # Based on the webpage content showing "12.75 X3.00 22.60"
            r'(\d+\.?\d*)\s*X\s*(\d+\.?\d*)\s*(\d+\.?\d*)',
            # Alternative patterns
            r'1\s*(\d+\.?\d*)\s*X\s*(\d+\.?\d*)\s*2\s*(\d+\.?\d*)',
            # More flexible pattern
            r'ESITO.*?(\d+\.?\d+)\s*X\s*(\d+\.?\d+)\s*(\d+\.?\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    odds_data['home_win'] = float(match.group(1))
                    odds_data['draw'] = float(match.group(2))
                    odds_data['away_win'] = float(match.group(3))
                    print(f"    ✅ 1X2 odds: {odds_data['home_win']}/{odds_data['draw']}/{odds_data['away_win']}")
                    return
                except (ValueError, IndexError):
                    continue
    
    def _extract_over_under_odds(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract Over/Under 2.5 goals odds."""
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
                    print(f"    ✅ O/U 2.5: {odds_data['over_2_5']}/{odds_data['under_2_5']}")
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
                    print(f"    ✅ BTTS: {odds_data['both_teams_score_yes']}/{odds_data['both_teams_score_no']}")
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
                    print(f"    ✅ Double Chance: {odds_data['home_or_draw']}/{odds_data['away_or_draw']}/{odds_data['home_or_away']}")
                    return
                except (ValueError, IndexError):
                    continue


def scrape_sisal_odds(url: str) -> Optional[BettingOdds]:
    """
    Convenience function to scrape odds from a Sisal URL with advanced techniques.
    
    Args:
        url: The Sisal live event URL
        
    Returns:
        BettingOdds instance or None if scraping fails
    """
    scraper = SisalScraper()
    return scraper.scrape_betting_odds(url)
