"""
Selenium-based Sisal website scraper for live betting odds.

This module uses Selenium with Chrome WebDriver to scrape live betting odds
from the Sisal website, bypassing anti-bot detection by using a real browser.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
import random
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from ..datamodel.betting_odds import BettingOdds


class SisalSeleniumScraper:
    """
    Selenium-based scraper for extracting betting odds from Sisal live betting pages.
    
    This scraper uses a real Chrome browser to avoid detection and can handle
    JavaScript-rendered content and dynamic loading.
    """
    
    def __init__(self, headless: bool = True):
        """
        Initialize the Selenium scraper.
        
        Args:
            headless: Whether to run Chrome in headless mode (no visible window)
        """
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with realistic options."""
        try:
            # Chrome options to make it look like a real browser
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless=new")  # Use new headless mode
            
            # Essential options to avoid detection
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Make browser appear more realistic
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading
            chrome_options.add_argument("--disable-javascript-console")
            
            # Set a realistic window size
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Set realistic user agent
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Language preferences
            chrome_options.add_argument("--lang=it-IT")
            chrome_options.add_experimental_option('prefs', {
                'intl.accept_languages': 'it-IT,it,en-US,en'
            })
            
            # Use webdriver-manager to automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            # Create the driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set page load timeout
            self.driver.set_page_load_timeout(30)
            
            # Create WebDriverWait instance
            self.wait = WebDriverWait(self.driver, 20)
            
            print("✅ Chrome WebDriver setup successful")
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Chrome WebDriver: {e}")
            return False
    
    def scrape_betting_odds(self, url: str) -> Optional[BettingOdds]:
        """
        Scrape betting odds from a Sisal live event page using Selenium.
        
        Args:
            url: The URL of the Sisal live event page
            
        Returns:
            BettingOdds instance with the scraped data, or None if scraping fails
        """
        try:
            print(f"🎯 Starting Selenium scraping for: {url}")
            
            # Setup driver if not already done
            if not self.driver:
                if not self._setup_driver():
                    return None
            
            # Navigate to the page with realistic browser behavior
            return self._scrape_with_browser_simulation(url)
            
        except Exception as e:
            print(f"❌ Selenium scraping error: {e}")
            return None
        finally:
            # Clean up
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    print("🧹 Browser closed")
                except:
                    pass
    
    def _scrape_with_browser_simulation(self, url: str) -> Optional[BettingOdds]:
        """Scrape with realistic browser behavior simulation."""
        try:
            print("🌐 Simulating realistic browser behavior...")
            
            # Step 1: Visit homepage first (like a real user)
            print("📄 Visiting Sisal homepage...")
            self.driver.get("https://www.sisal.it")
            
            # Wait for page to load and simulate reading
            self._wait_and_simulate_reading()
            
            # Step 2: Navigate to live betting section
            print("🎲 Navigating to live betting...")
            try:
                # Look for live betting link and click it
                live_betting_selectors = [
                    "a[href*='scommesse-live']",
                    "a[href*='live']",
                    "text:Scommesse Live",
                    "text:Live"
                ]
                
                clicked = False
                for selector in live_betting_selectors:
                    try:
                        if selector.startswith("text:"):
                            # Use XPath for text content
                            text = selector.replace("text:", "")
                            element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        
                        if element and element.is_displayed():
                            self.driver.execute_script("arguments[0].click();", element)
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    # Direct navigation as fallback
                    self.driver.get("https://www.sisal.it/scommesse-live")
                
            except Exception as e:
                print(f"⚠️ Could not click live betting link, using direct navigation: {e}")
                self.driver.get("https://www.sisal.it/scommesse-live")
            
            self._wait_and_simulate_reading()
            
            # Step 3: Navigate to target page
            print("🎯 Navigating to target match page...")
            self.driver.get(url)
            
            # Wait for the page to fully load
            self._wait_for_page_load()
            
            # Step 4: Check if we successfully loaded the betting page
            if not self._verify_betting_page():
                print("❌ Failed to load betting page properly")
                return None
            
            # Step 5: Extract odds data
            return self._extract_odds_from_page(url)
            
        except Exception as e:
            print(f"❌ Browser simulation error: {e}")
            return None
    
    def _wait_and_simulate_reading(self):
        """Simulate human reading behavior with random delays."""
        delay = random.uniform(2, 5)
        print(f"⏱️ Simulating reading time: {delay:.1f}s")
        time.sleep(delay)
    
    def _wait_for_page_load(self):
        """Wait for page to fully load with multiple checks."""
        try:
            # Wait for document ready state
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Check for common loading indicators and wait for them to disappear
            loading_selectors = [
                ".loading", ".spinner", ".loader", "[data-loading]",
                ".skeleton", ".placeholder"
            ]
            
            for selector in loading_selectors:
                try:
                    self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, selector)))
                except TimeoutException:
                    pass  # Element might not exist, which is fine
            
            print("✅ Page fully loaded")
            
        except Exception as e:
            print(f"⚠️ Page load wait warning: {e}")
    
    def _verify_betting_page(self) -> bool:
        """Verify that we're on a proper betting page with odds."""
        try:
            # Check page title
            title = self.driver.title.lower()
            if any(keyword in title for keyword in ['sisal', 'scommesse', 'betting']):
                print(f"✅ Valid betting page title: {self.driver.title}")
            else:
                print(f"⚠️ Unexpected page title: {self.driver.title}")
            
            # Check for betting-related content
            page_text = self.driver.page_source.lower()
            betting_keywords = ['odds', 'quote', 'scommesse', '1x2', 'goal', 'over', 'under']
            found_keywords = [kw for kw in betting_keywords if kw in page_text]
            
            if found_keywords:
                print(f"✅ Found betting keywords: {', '.join(found_keywords[:3])}...")
                return True
            else:
                print("❌ No betting keywords found on page")
                return False
                
        except Exception as e:
            print(f"❌ Page verification error: {e}")
            return False
    
    def _extract_odds_from_page(self, url: str) -> Optional[BettingOdds]:
        """Extract betting odds from the current page."""
        try:
            print("📊 Extracting odds from page...")
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Also try to find odds using Selenium selectors for dynamic content
            self._wait_for_odds_elements()
            
            # Extract match information
            match_info = self._extract_match_info_selenium(soup, url)
            if not match_info:
                print("❌ Could not extract match information")
                return None
            
            print(f"🏆 Match: {match_info['home_team']} vs {match_info['away_team']}")
            
            # Extract odds using both Selenium and BeautifulSoup
            odds_data = self._extract_odds_selenium(soup)
            
            # Count non-null odds
            odds_found = sum(1 for v in odds_data.values() if v is not None)
            print(f"🎲 Extracted {odds_found} odds values")
            
            if odds_found == 0:
                print("❌ No odds found")
                return None
            
            # Create BettingOdds instance
            betting_odds = BettingOdds(
                timestamp=datetime.now(),
                source="Sisal",
                match_id=match_info['match_id'],
                home_team=match_info['home_team'],
                away_team=match_info['away_team'],
                **odds_data
            )
            
            print("✅ Successfully created BettingOdds instance")
            return betting_odds
            
        except Exception as e:
            print(f"❌ Odds extraction error: {e}")
            return None
    
    def _wait_for_odds_elements(self):
        """Wait for odds elements to appear on the page."""
        try:
            # Common selectors for odds elements
            odds_selectors = [
                "[data-testid*='odd']",
                ".odd", ".odds", ".quote",
                "[class*='odd']", "[class*='quote']",
                "button[data-odd]", "span[data-odd]"
            ]
            
            for selector in odds_selectors:
                try:
                    element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if element:
                        print(f"✅ Found odds elements with selector: {selector}")
                        return
                except TimeoutException:
                    continue
            
            print("⚠️ No specific odds elements found, proceeding with page content")
            
        except Exception as e:
            print(f"⚠️ Odds elements wait warning: {e}")
    
    def _extract_match_info_selenium(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, str]]:
        """Extract match information using both Selenium and BeautifulSoup."""
        try:
            # Try Selenium selectors first (for dynamic content)
            match_title = None
            
            # Selenium-based selectors
            selenium_selectors = [
                "h1", "h2", ".match-title", ".event-title",
                "[data-testid*='match']", "[data-testid*='event']"
            ]
            
            for selector in selenium_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if self._looks_like_match_title(text):
                        match_title = text
                        break
                except:
                    continue
            
            # Fallback to BeautifulSoup parsing
            if not match_title:
                match_title = self._extract_match_title_from_soup(soup)
            
            # Final fallback to URL parsing
            if not match_title:
                match_title = self._extract_match_from_url(url)
            
            if not match_title:
                print("❌ Could not find match title")
                return None
            
            print(f"📋 Found match title: {match_title}")
            
            # Parse team names
            teams = self._parse_team_names(match_title)
            if not teams:
                print(f"❌ Could not parse teams from: {match_title}")
                return None
            
            # Generate match ID
            match_id = self._generate_match_id(url, teams)
            
            return {
                'home_team': teams[0],
                'away_team': teams[1],
                'match_id': match_id
            }
            
        except Exception as e:
            print(f"❌ Match info extraction error: {e}")
            return None
    
    def _extract_match_title_from_soup(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract match title from BeautifulSoup."""
        selectors = [
            'title', 'h1', 'h2', '.match-title', '.event-title',
            '[data-testid*="match"]', '[data-testid*="event"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if self._looks_like_match_title(text):
                    return text
        return None
    
    def _looks_like_match_title(self, text: str) -> bool:
        """Check if text looks like a match title."""
        if not text or len(text) < 5:
            return False
        
        # Must contain team separator
        separators = [' - ', ' vs ', ' v ', '–', '—', ' VS ', ' V ']
        has_separator = any(sep in text for sep in separators)
        
        # Should not be too long
        if len(text) > 200:
            return False
        
        # Should be reasonable length for team names
        if len(text.split()) > 15:
            return False
        
        return has_separator
    
    def _extract_match_from_url(self, url: str) -> Optional[str]:
        """Extract match info from URL path."""
        try:
            path_parts = urlparse(url).path.split('/')
            for part in reversed(path_parts):
                if '-' in part and len(part) > 10:
                    teams = part.split('-')
                    if len(teams) >= 2:
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
        delimiters = [' - ', ' vs ', ' v ', '–', '—', ' VS ', ' V ']
        
        for delimiter in delimiters:
            if delimiter in match_title:
                parts = match_title.split(delimiter, 1)
                if len(parts) == 2:
                    home_team = parts[0].strip()
                    away_team = parts[1].strip()
                    
                    # Clean up team names
                    home_team = re.sub(r'\d+:\d+.*', '', home_team).strip()
                    away_team = re.sub(r'\d+:\d+.*', '', away_team).strip()
                    
                    if home_team and away_team:
                        return (home_team, away_team)
        return None
    
    def _generate_match_id(self, url: str, teams: tuple) -> str:
        """Generate a unique match ID."""
        path = urlparse(url).path
        path_parts = [part for part in path.split('/') if part]
        
        if len(path_parts) >= 2:
            return path_parts[-1]
        
        # Fallback: generate from team names
        home_clean = re.sub(r'[^a-zA-Z0-9]', '_', teams[0].lower())
        away_clean = re.sub(r'[^a-zA-Z0-9]', '_', teams[1].lower())
        return f"{home_clean}_vs_{away_clean}"
    
    def _extract_odds_selenium(self, soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Extract betting odds using both Selenium and BeautifulSoup."""
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
            # Try Selenium selectors for dynamic content first
            self._extract_odds_selenium_selectors(odds_data)
            
            # Fallback to text parsing from page source
            if sum(1 for v in odds_data.values() if v is not None) == 0:
                self._extract_odds_from_text(soup, odds_data)
            
        except Exception as e:
            print(f"❌ Odds extraction error: {e}")
        
        return odds_data
    
    def _extract_odds_selenium_selectors(self, odds_data: Dict[str, Optional[float]]):
        """Try to extract odds using Selenium element selectors."""
        try:
            # Common patterns for odds elements
            odds_selectors = [
                "button[data-odd]",
                ".odd-value",
                ".quote",
                "[class*='odd']",
                "[data-testid*='odd']"
            ]
            
            for selector in odds_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if len(elements) >= 3:  # At least 3 odds for 1X2
                        print(f"  🎯 Found odds elements with: {selector}")
                        # Try to extract 1X2 odds from first 3 elements
                        for i, element in enumerate(elements[:3]):
                            try:
                                odd_text = element.text.strip()
                                odd_value = float(odd_text)
                                if i == 0:
                                    odds_data['home_win'] = odd_value
                                elif i == 1:
                                    odds_data['draw'] = odd_value
                                elif i == 2:
                                    odds_data['away_win'] = odd_value
                            except:
                                continue
                        
                        if odds_data['home_win']:  # If we found something, stop
                            break
                except:
                    continue
        except Exception as e:
            print(f"  ⚠️ Selenium selectors failed: {e}")
    
    def _extract_odds_from_text(self, soup: BeautifulSoup, odds_data: Dict[str, Optional[float]]):
        """Extract odds from page text using regex patterns."""
        try:
            # Get all text content
            if self.driver:
                text = self.driver.page_source
            else:
                text = soup.get_text()
            
            # Extract 1X2 odds
            self._extract_1x2_odds_from_text(text, odds_data)
            
            # Extract Over/Under odds
            self._extract_over_under_odds_from_text(text, odds_data)
            
            # Extract Goal/NoGoal odds
            self._extract_goal_nogoal_odds_from_text(text, odds_data)
            
            # Extract Double Chance odds
            self._extract_double_chance_odds_from_text(text, odds_data)
            
        except Exception as e:
            print(f"  ⚠️ Text extraction failed: {e}")
    
    def _extract_1x2_odds_from_text(self, text: str, odds_data: Dict[str, Optional[float]]):
        """Extract 1X2 odds from text."""
        patterns = [
            r'(\d+\.?\d*)\s*X\s*(\d+\.?\d*)\s*(\d+\.?\d*)',
            r'1\s*(\d+\.?\d*)\s*X\s*(\d+\.?\d*)\s*2\s*(\d+\.?\d*)',
            r'ESITO.*?(\d+\.?\d+)\s*X\s*(\d+\.?\d+)\s*(\d+\.?\d+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    odds_data['home_win'] = float(match.group(1))
                    odds_data['draw'] = float(match.group(2))
                    odds_data['away_win'] = float(match.group(3))
                    print(f"    ✅ 1X2: {odds_data['home_win']}/{odds_data['draw']}/{odds_data['away_win']}")
                    return
                except (ValueError, IndexError):
                    continue
    
    def _extract_over_under_odds_from_text(self, text: str, odds_data: Dict[str, Optional[float]]):
        """Extract Over/Under odds from text."""
        patterns = [
            r'UNDER\s*(\d+\.?\d*)\s*OVER\s*(\d+\.?\d*)',
            r'Under\s*2\.5\s*(\d+\.?\d*)\s*Over\s*2\.5\s*(\d+\.?\d*)',
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
    
    def _extract_goal_nogoal_odds_from_text(self, text: str, odds_data: Dict[str, Optional[float]]):
        """Extract Goal/NoGoal odds from text."""
        patterns = [
            r'GOAL\s*(\d+\.?\d*)\s*NOGOAL\s*(\d+\.?\d*)',
            r'GG\s*(\d+\.?\d*)\s*NG\s*(\d+\.?\d*)',
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
    
    def _extract_double_chance_odds_from_text(self, text: str, odds_data: Dict[str, Optional[float]]):
        """Extract Double Chance odds from text."""
        patterns = [
            r'1X\s*(\d+\.?\d*)\s*X2\s*(\d+\.?\d*)\s*12\s*(\d+\.?\d*)',
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


def scrape_sisal_odds_selenium(url: str, headless: bool = True) -> Optional[BettingOdds]:
    """
    Convenience function to scrape odds from a Sisal URL using Selenium.
    
    Args:
        url: The Sisal live event URL
        headless: Whether to run browser in headless mode
        
    Returns:
        BettingOdds instance or None if scraping fails
    """
    scraper = SisalSeleniumScraper(headless=headless)
    return scraper.scrape_betting_odds(url)
