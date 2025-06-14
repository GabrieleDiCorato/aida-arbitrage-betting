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
from datetime import datetime
import re
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
            
            # Performance optimization - disable unnecessary resources
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")  # Faster loading
            chrome_options.add_argument("--disable-javascript-console")
            chrome_options.add_argument("--disable-css")  # Skip CSS loading
            chrome_options.add_argument("--disable-web-security")  # Skip some security checks
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            
            # Block unnecessary requests - comprehensive blocking
            prefs = {
                # Block images, media, and notifications
                "profile.managed_default_content_settings.images": 2,  # Block images
                "profile.default_content_setting_values.notifications": 2,  # Block notifications
                "profile.managed_default_content_settings.media_stream": 2,  # Block media
                "profile.default_content_settings.popups": 0,  # Block popups
                "profile.managed_default_content_settings.geolocation": 2,  # Block location
                
                # Block ads and analytics
                "profile.managed_default_content_settings.ads": 2,  # Block ads
                "profile.content_settings.exceptions.ads": {},
                "profile.default_content_setting_values.ads": 2,
                
                # Block plugins and flash
                "profile.managed_default_content_settings.plugins": 2,
                "profile.default_content_setting_values.plugins": 2,
                
                # Block automatic downloads
                "profile.default_content_settings.automatic_downloads": 2,
                
                # Privacy settings
                "profile.default_content_setting_values.cookies": 1,  # Allow only first-party cookies
                "profile.block_third_party_cookies": True,
                
                # Language preferences
                'intl.accept_languages': 'it-IT,it,en-US,en'
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Additional blocking arguments
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-ipc-flooding-protection")
            
            # Block specific services
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--disable-default-apps")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-component-update")
            
            # Network optimizations
            chrome_options.add_argument("--aggressive-cache-discard")
            chrome_options.add_argument("--disable-hang-monitor")
            chrome_options.add_argument("--disable-prompt-on-repost")
            
            # Block external connections
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            chrome_options.add_argument("--disable-background-mode")
            
            # Set a realistic window size
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Set realistic user agent
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Language preferences
            chrome_options.add_argument("--lang=it-IT")
            
            # Use webdriver-manager to automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())
              # Create the driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set faster page load timeout
            self.driver.set_page_load_timeout(15)  # Reduced from 30
              # Create WebDriverWait instance with shorter timeout
            self.wait = WebDriverWait(self.driver, 10)  # Reduced from 20
            
            print("Chrome WebDriver setup successful")
            return True
            
        except Exception as e:
            print(f"Failed to setup Chrome WebDriver: {e}")
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
            print(f"Starting Selenium scraping for: {url}")
            
            # Setup driver if not already done
            if not self.driver:
                if not self._setup_driver():
                    return None
            
            # Navigate directly to target page (skip homepage simulation)
            return self._scrape_direct(url)
            
        except Exception as e:
            print(f"Selenium scraping error: {e}")
            return None
        finally:
            # Clean up
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    print("Browser closed")
                except:
                    pass

    def _scrape_direct(self, url: str) -> Optional[BettingOdds]:
        """Scrape directly without browser simulation for faster performance."""
        try:
            # Type guard to ensure driver is available
            if not self.driver:
                print("WebDriver not initialized")
                return None
                
            print("Direct navigation to match page...")
            
            # Navigate directly to the target page
            self.driver.get(url)
            
            # Handle cookie banner if present
            self._handle_cookie_banner()
            
            # Extract odds data (includes waiting for odds elements)
            return self._extract_odds_from_page(url)
            
        except Exception as e:
            print(f"Direct scraping error: {e}")
            return None

    def _extract_odds_from_page(self, url: str) -> Optional[BettingOdds]:
        """Extract betting odds from the current page."""
        if not self.driver:
            return None
            
        try:
            print("Extracting odds from page...")
            
            # Wait for odds elements to appear
            self._wait_for_odds_elements()
            
            # Extract match information
            match_info = self._extract_match_info_selenium(url)
            if not match_info:
                print("Could not extract match information")
                return None
            
            print(f"Match: {match_info['home_team']} vs {match_info['away_team']}")
            
            # Extract odds
            odds_data = self._extract_odds_selenium()
            
            # Count non-null odds
            odds_found = sum(1 for v in odds_data.values() if v is not None)
            print(f"Extracted {odds_found} odds values")
            
            if odds_found == 0:
                print("No odds found")
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
            
            print("Successfully created BettingOdds instance")
            return betting_odds
            
        except Exception as e:
            print(f"Odds extraction error: {e}")
            return None

    def _wait_for_odds_elements(self):
        """Wait for betting odds elements to appear using direct selectors."""
        if not self.driver:
            return
            
        try:
            print("Waiting for betting odds elements...")
            
            # Wait for any of the betting odds buttons to appear
            odds_selectors = [
                # 1X2 odds - using more specific selector
                'button[data-qa$="_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Home win
                'button[data-qa$="_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Draw
                'button[data-qa$="_3"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Away win
                
                # GOAL/NOGOAL odds - using more specific selector
                'button[data-qa*="18_0_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # GOAL
                'button[data-qa*="18_0_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # NOGOAL
                
                # Over/Under 2.5 odds - using more specific selector
                'button[data-qa*="250_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Under 2.5
                'button[data-qa*="250_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Over 2.5
                
                # Over/Under 3.5 odds - using more specific selector
                'button[data-qa*="350_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Under 3.5
                'button[data-qa*="350_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # Over 3.5
                  # Double Chance odds - using more specific selector
                'button[data-qa*="99999_0_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # 1X
                'button[data-qa*="99999_0_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # X2
                'button[data-qa*="99999_0_3"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # 12
                
                # First Half 1X2 odds - using pattern from HTML
                'button[data-qa*="_14_0_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # First half home
                'button[data-qa*="_14_0_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',  # First half draw
                'button[data-qa*="_14_0_3"] span.tw-fr-text-paragraph-s.tw-fr-font-bold'   # First half away
            ]
            
            for selector in odds_selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        print("Found betting odds elements")
                        return
                except TimeoutException:
                    continue
            
            print("No betting odds elements found, proceeding anyway")
            
        except Exception as e:
            print(f"Odds elements wait warning: {e}")

    def _extract_match_info_selenium(self, url: str) -> Optional[Dict[str, str]]:
        """Extract match information using direct selectors."""
        if not self.driver:
            return None
            
        try:
            # Try specific selector for match title from the page structure
            match_title = None
            
            # Primary selector: team names in dropdown toggle button
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, 'button[data-qa="regulator-live-detail-dropdown-toggle"] div')
                match_title = element.text.strip()
                if match_title and (' - ' in match_title or ' vs ' in match_title):
                    print(f"Found match title from dropdown: {match_title}")
                else:
                    match_title = None
            except Exception as e:
                print(f"Could not extract from dropdown selector: {e}")
            
            # Fallback selectors
            if not match_title:
                fallback_selectors = ["h1", "h2", "title", ".match-title", ".event-title"]
                for selector in fallback_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        text = element.text.strip()
                        if text and (' - ' in text or ' vs ' in text or ' v ' in text):
                            match_title = text
                            break
                    except:
                        continue
            
            # Fallback to URL parsing
            if not match_title:
                match_title = self._extract_match_from_url(url)
            
            if not match_title:
                print("Could not find match title")
                return None
            
            print(f"Found match title: {match_title}")
            
            # Parse team names
            teams = self._parse_team_names(match_title)
            if not teams:
                print(f"Could not parse teams from: {match_title}")
                return None
            
            # Generate match ID from URL
            match_id = self._generate_match_id(url, teams)
            
            return {
                'home_team': teams[0],                'away_team': teams[1],
                'match_id': match_id
            }
            
        except Exception as e:
            print(f"Match info extraction error: {e}")
            return None
    
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
    
    def _extract_odds_selenium(self) -> Dict[str, Optional[float]]:
        """Extract betting odds using direct CSS selectors."""
        odds_data: Dict[str, Optional[float]] = {
            'home_win': None,
            'draw': None,
            'away_win': None,
            'over_2_5': None,
            'under_2_5': None,
            'over_3_5': None,
            'under_3_5': None,
            'both_teams_score_yes': None,
            'both_teams_score_no': None,
            'home_or_draw': None,
            'away_or_draw': None,
            'home_or_away': None,
            'first_half_home_win': None,
            'first_half_draw': None,
            'first_half_away_win': None
        }
        
        try:
            # Extract odds using direct CSS selectors
            self._extract_odds_selenium_selectors(odds_data)
            
        except Exception as e:
            print(f"Odds extraction error: {e}")
        
        return odds_data

    def _extract_odds_selenium_selectors(self, odds_data: Dict[str, Optional[float]]):
        """Extract betting odds using direct CSS selectors."""
        if not self.driver:
            return
            
        try:
            print("Extracting odds using direct selectors...")
            
            # Direct selectors for different betting markets
            selectors = {
                # 1X2 odds - using more specific selector
                'home_win': 'button[data-qa$="_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'draw': 'button[data-qa$="_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold', 
                'away_win': 'button[data-qa$="_3"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                
                # GOAL/NOGOAL odds - using more specific selector
                'both_teams_score_yes': 'button[data-qa*="18_0_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'both_teams_score_no': 'button[data-qa*="18_0_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                
                # Over/Under 2.5 odds - using more specific selector
                'under_2_5': 'button[data-qa*="250_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'over_2_5': 'button[data-qa*="250_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                
                # Over/Under 3.5 odds - using more specific selector
                'under_3_5': 'button[data-qa*="350_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'over_3_5': 'button[data-qa*="350_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',                # Double Chance odds - using more specific selector from HTML
                'home_or_draw': 'button[data-qa*="99999_0_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'away_or_draw': 'button[data-qa*="99999_0_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'home_or_away': 'button[data-qa*="99999_0_3"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                
                # First Half 1X2 odds - using pattern from HTML
                'first_half_home_win': 'button[data-qa*="_14_0_1"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'first_half_draw': 'button[data-qa*="_14_0_2"] span.tw-fr-text-paragraph-s.tw-fr-font-bold',
                'first_half_away_win': 'button[data-qa*="_14_0_3"] span.tw-fr-text-paragraph-s.tw-fr-font-bold'
            }
            
            for bet_type, selector in selectors.items():
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    odd_text = element.text.strip()
                    odd_value = float(odd_text)
                    odds_data[bet_type] = odd_value
                    print(f"  {bet_type}: {odd_value}")
                except Exception as e:
                    print(f"  Failed to extract {bet_type}: {e}")
                    
        except Exception as e:
            print(f"  Selenium selectors failed: {e}")
                
    def _handle_cookie_banner(self):
        """Handle cookie banner by clicking 'Accetta tutti' button if present."""
        if not self.driver:
            return False
        
        try:
            print("Checking for cookie banner...")
            # Wait for and click the "Accetta tutti" button
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print("Cookie banner accepted")
            return True
        except TimeoutException:
            print("No cookie banner found")
            return False
        except Exception as e:
            print(f"Cookie banner handling failed: {e}")
            return False

    def close(self):
        """Close the WebDriver and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.wait = None
                print("Browser closed")
            except Exception as e:
                print(f"Error closing browser: {e}")


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
