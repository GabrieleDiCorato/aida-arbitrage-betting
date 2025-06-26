"""
Simplified Selenium-based Sisal website scraper for live betting odds.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import time
import signal
from ...datamodel.betting_odds import BettingOdds
from ...storage import CSVBettingOddsStorage, BettingOddsStorageBase


class SisalScraper:
    """Simplified Sisal scraper focused on speed and reliability."""
    
    def __init__(self, headless: bool = True, storage: Optional[BettingOddsStorageBase] = None):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.storage = storage or CSVBettingOddsStorage()
        self._is_running = False
        self._session_start_time: Optional[datetime] = None
        
    def _setup_driver(self):
        """Setup Chrome WebDriver with minimal options for speed."""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument("--headless=new")
            
            # Essential options only
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Speed optimizations
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript-console")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            
            # Realistic user agent
            chrome_options.add_argument(
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Set timeouts
            self.driver.set_page_load_timeout(15)
            self.wait = WebDriverWait(self.driver, 10)
            
            print("Chrome WebDriver setup successful")
            return True
            
        except Exception as e:
            print(f"Failed to setup Chrome WebDriver: {e}")
            return False

    def _wait_for_page_load(self):
        """Wait for the main betting content to load."""
        try:
            if not self.wait:
                return
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '1X2 ESITO FINALE')]"))
            )
            print("Page content loaded")
        except TimeoutException:
            print("Page content may not be fully loaded")

    def _extract_team_names(self) -> Optional[tuple]:
        """Extract team names using the dropdown button selector."""
        try:
            if not self.driver:
                return None
            element = self.driver.find_element(
                By.CSS_SELECTOR, 
                'button[data-qa="regulator-live-detail-dropdown-toggle"] div'
            )
            match_text = element.text.strip()
            
            if " - " in match_text:
                teams = match_text.split(" - ", 1)
                home_team = teams[0].strip()
                away_team = teams[1].strip()
                print(f"Teams: {home_team} vs {away_team}")
                return (home_team, away_team)
                
        except NoSuchElementException:
            print("Team names element not found")
        except Exception as e:
            print(f"Error extracting team names: {e}")
        
        return None

    def _extract_odds(self) -> Dict[str, Optional[float]]:
        """Extract betting odds using optimized selectors."""
        odds_data = {}
        
        if not self.driver:
            return odds_data
        
        # Extract each market using data-qa patterns
        odds_data.update(self._extract_1x2_main())
        odds_data.update(self._extract_double_chance())
        odds_data.update(self._extract_over_under())
        odds_data.update(self._extract_both_teams_score())
        
        return odds_data

    def _extract_1x2_main(self) -> Dict[str, Optional[float]]:
        """Extract main 1X2 market odds."""
        return self._extract_market_by_pattern({
            'home_win': '_3_0_1',
            'draw': '_3_0_2', 
            'away_win': '_3_0_3'
        }, "1X2 Main")

    def _extract_double_chance(self) -> Dict[str, Optional[float]]:
        """Extract double chance market odds."""
        return self._extract_market_by_pattern({
            'home_or_draw': '_99999_0_1',
            'away_or_draw': '_99999_0_2',
            'home_or_away': '_99999_0_3'
        }, "Double Chance")

    def _extract_over_under(self) -> Dict[str, Optional[float]]:
        """Extract over/under goals market odds."""
        # Try different patterns for O/U 1.5, 2.5 and 3.5
        odds_data = {}

         # O/U 1.5 patterns (based on HTML analysis)
        ou_15_patterns = {
            'under_1_5': ['_7989_150_1', '_150_1'],  
            'over_1_5': ['_7989_150_2', '_150_2']
        }
        
        # O/U 2.5 patterns (based on HTML analysis)
        ou_25_patterns = {
            'under_2_5': ['_7989_250_1', '_250_1'],  
            'over_2_5': ['_7989_250_2', '_250_2']
        }
        
        # O/U 3.5 patterns (estimated)
        ou_35_patterns = {
            'under_3_5': ['_7989_350_1', '_350_1'],
            'over_3_5': ['_7989_350_2', '_350_2']
        }

        # Extract O/U 1.5
        for bet_type, patterns in ou_15_patterns.items():
            odds_data[bet_type] = self._try_extract_with_patterns(patterns)
        
        # Extract O/U 2.5
        for bet_type, patterns in ou_25_patterns.items():
            odds_data[bet_type] = self._try_extract_with_patterns(patterns)
            
        # Extract O/U 3.5
        for bet_type, patterns in ou_35_patterns.items():
            odds_data[bet_type] = self._try_extract_with_patterns(patterns)
            
        if any(odds_data.values()):
            print("Over/Under odds extracted")
            
        return odds_data

    def _extract_both_teams_score(self) -> Dict[str, Optional[float]]:
        """Extract both teams to score (GOAL/NOGOAL) market odds."""
        # Based on HTML analysis: "Goal/NoGoal" section
        return self._extract_market_by_pattern({
            'both_teams_score_yes': '_18_0_1',  # "GOAL" button
            'both_teams_score_no': '_18_0_2'    # "NOGOAL" button
        }, "Goal/NoGoal")

    def _extract_market_by_pattern(self, patterns: Dict[str, str], market_name: str) -> Dict[str, Optional[float]]:
        """Extract odds for a market using data-qa patterns."""
        odds_data = {}
        found_any = False
        
        for bet_type, pattern in patterns.items():
            odds_data[bet_type] = self._try_extract_with_patterns([pattern])
            if odds_data[bet_type] is not None:
                found_any = True
                
        if found_any:
            print(f"{market_name} odds extracted")
            
        return odds_data

    def _try_extract_with_patterns(self, patterns: list) -> Optional[float]:
        """Try to extract odds using multiple data-qa patterns."""
        if not self.driver:
            return None
            
        for pattern in patterns:
            try:
                # Look for button with data-qa containing the pattern
                selector = f'button[data-qa*="{pattern}"] span'
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    try:
                        odds_text = element.text.strip()
                        if odds_text and odds_text.replace('.', '').replace(',', '').isdigit():
                            odds_value = float(odds_text.replace(',', '.'))
                            if odds_value > 1.0:  # Sanity check
                                return odds_value
                    except (ValueError, AttributeError):
                        continue
                        
            except Exception:
                continue
                
        return None

    def _generate_match_id(self, url: str) -> str:
        """Generate match ID from URL."""
        path = urlparse(url).path
        path_parts = [part for part in path.split('/') if part]
        return path_parts[-1] if path_parts else f"match_{int(datetime.now().timestamp())}"

    def _handle_cookie_banner(self):
        """Handle cookie banner."""
        try:
            if not self.driver:
                return
            cookie_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            print("Cookie banner accepted")
        except TimeoutException:
            print("No cookie banner found")
        except Exception as e:
            print(f"Cookie banner handling failed: {e}")

    def _print_debug_info(self, betting_odds: BettingOdds):
        """Print extracted betting odds for debugging."""
        print(f"\n=== EXTRACTED BETTING ODDS ===")
        print(f"Match: {betting_odds.home_team} vs {betting_odds.away_team}")
        print(f"Match ID: {betting_odds.match_id}")
        print(f"Source: {betting_odds.source}")
        print(f"Timestamp: {betting_odds.timestamp}")
        
        if any([betting_odds.home_win, betting_odds.draw, betting_odds.away_win]):
            print(f"1X2: {betting_odds.home_win} / {betting_odds.draw} / {betting_odds.away_win}")
        
        if any([betting_odds.home_or_draw, betting_odds.away_or_draw, betting_odds.home_or_away]):
            print(f"Double Chance: {betting_odds.home_or_draw} / {betting_odds.away_or_draw} / {betting_odds.home_or_away}")
        
        if any([betting_odds.over_2_5, betting_odds.under_2_5]):
            print(f"O/U 2.5: {betting_odds.over_2_5} / {betting_odds.under_2_5}")
        
        if any([betting_odds.both_teams_score_yes, betting_odds.both_teams_score_no]):
            print(f"BTTS: {betting_odds.both_teams_score_yes} / {betting_odds.both_teams_score_no}")
        
        print(f"===============================\n")

    def close(self):
        """Close WebDriver and clean up storage."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                print("Browser closed")
            except Exception as e:
                print(f"Error closing browser: {e}")
          # Close storage
        if self.storage:
            self.storage.close()

    def scrape(self, url: str, duration_minutes: Optional[float] = None, interval_seconds: int = 10) -> Dict[str, Any]:
        """
        Unified scraping method that handles both one-shot and continuous scraping.
        
        Args:
            url: The URL of the Sisal betting page to scrape
            duration_minutes: How long to run scraping (None for one-shot, >0 for continuous)
            interval_seconds: How often to scrape data in continuous mode (default: 10 seconds)
            
        Returns:
            Dictionary with scraping results including successful_scrapes count and data
        """
        # Determine scraping mode
        is_continuous = duration_minutes is not None and duration_minutes > 0
        mode_text = f"continuous ({duration_minutes} minutes)" if is_continuous else "one-shot"
        
        print(f"Starting {mode_text} scraping session")
        print(f"   URL: {url}")
        if is_continuous:
            print(f"   Duration: {duration_minutes} minutes")
            print(f"   Interval: {interval_seconds} seconds")
        print(f"   Storage: {self.storage.__class__.__name__}")
          # Initialize session state
        self._is_running = True
        self._session_start_time = datetime.now()
        session_end_time = None
        if is_continuous and duration_minutes:
            session_end_time = self._session_start_time + timedelta(minutes=duration_minutes)
        successful_scrapes = 0
        failed_scrapes = 0
        scraped_data = []
          # Set up signal handler for graceful shutdown (only for continuous mode)
        if is_continuous:
            def signal_handler(signum, frame):
                print("\nReceived interrupt signal. Stopping scraping session...")
                self._is_running = False
            
            signal.signal(signal.SIGINT, signal_handler)
            print(f"Session started at {self._session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if session_end_time:
                print(f"Session will end at {session_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("   Press Ctrl+C to stop early")
            print("-" * 60)
        
        try:
            # Initialize storage
            if not self.storage._is_initialized:
                self.storage.initialize()
            
            # Setup browser (keep open for continuous scraping)
            if not self._setup_driver():
                return self._create_result_summary(successful_scrapes, failed_scrapes, scraped_data)
            
            # Navigate to page initially
            if not self._navigate_and_setup_page(url):
                return self._create_result_summary(successful_scrapes, failed_scrapes, scraped_data)
            
            # Scraping loop (runs once for one-shot, multiple times for continuous)
            while self._is_running:
                try:
                    # Extract data
                    betting_odds = self._extract_betting_data(url)
                    
                    if betting_odds:
                        successful_scrapes += 1
                        scraped_data.append(betting_odds)
                        
                        # Store data
                        self.storage.store(betting_odds)
                        
                        # Log based on mode
                        if is_continuous:
                            print(f"{betting_odds.timestamp.strftime('%H:%M:%S')} - {betting_odds.home_team} vs {betting_odds.away_team} - 1X2: {betting_odds.home_win}/{betting_odds.draw}/{betting_odds.away_win}")
                        else:
                            self._print_debug_info(betting_odds)
                    else:
                        failed_scrapes += 1
                        if not is_continuous:
                            print("Failed to extract betting odds")
                    
                    # Break for one-shot mode
                    if not is_continuous:
                        break
                    
                    # Check if continuous session should end
                    if session_end_time and datetime.now() >= session_end_time:
                        break
                    
                    # Wait for next scrape
                    time.sleep(interval_seconds)
                    
                except KeyboardInterrupt:
                    if is_continuous:
                        print("\nKeyboard interrupt received. Stopping...")
                    break
                    
                except Exception as e:
                    print(f"Error during scraping: {e}")
                    failed_scrapes += 1
                    if not is_continuous:
                        break
                    time.sleep(1)  # Brief pause before retrying
                    
        except Exception as e:
            print(f"Critical error in scraping: {e}")
            
        finally:
            # Clean up
            self._is_running = False
            
            # Close browser
            if self.driver:
                try:
                    self.driver.quit()
                    self.driver = None
                    print("Browser closed")
                except Exception as e:
                    print(f"Error closing browser: {e}")
        
        # Print session summary
        result = self._create_result_summary(successful_scrapes, failed_scrapes, scraped_data)
        self._print_session_summary(result, is_continuous)
        
        return result
    
    def _navigate_and_setup_page(self, url: str) -> bool:
        """Navigate to the page and handle initial setup."""
        try:
            if not self.driver or not self.wait:
                print("Driver or wait not initialized")
                return False
            
            # Navigate to page
            print(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Handle cookie banner
            self._handle_cookie_banner()
            
            # Wait for page to load
            self._wait_for_page_load()
            
            return True
            
        except Exception as e:
            print(f"Error setting up page: {e}")
            return False
    
    def _extract_betting_data(self, url: str) -> Optional[BettingOdds]:
        """Extract betting odds data from the current page."""
        try:
            # Extract team names
            team_names = self._extract_team_names()
            if not team_names:
                print("Could not extract team names")
                return None
            
            # Extract odds data
            odds_data = self._extract_odds()
            match_id = self._generate_match_id(url)
            
            # Create BettingOdds instance
            betting_odds = BettingOdds(
                timestamp=datetime.now(),
                source="Sisal",
                match_id=match_id,
                home_team=team_names[0],
                away_team=team_names[1],
                **odds_data
            )
            
            return betting_odds
            
        except Exception as e:
            print(f"Error extracting betting data: {e}")
            return None
    
    def _create_result_summary(self, successful_scrapes: int, failed_scrapes: int, scraped_data: list) -> Dict[str, Any]:
        """Create a summary of scraping results."""
        total_scrapes = successful_scrapes + failed_scrapes
        success_rate = (successful_scrapes / total_scrapes * 100) if total_scrapes > 0 else 0
        
        return {
            'successful_scrapes': successful_scrapes,
            'failed_scrapes': failed_scrapes,
            'total_scrapes': total_scrapes,
            'success_rate': success_rate,
            'data': scraped_data,
            'session_duration': datetime.now() - self._session_start_time if self._session_start_time else timedelta(0),
            'storage_path': getattr(self.storage, 'get_file_path', lambda: None)()
        }
    
    def _print_session_summary(self, result: Dict[str, Any], is_continuous: bool) -> None:
        """Print a summary of the scraping session."""
        print("-" * 60)
        mode_text = "CONTINUOUS" if is_continuous else "ONE-SHOT"
        print(f"{mode_text} SCRAPING SESSION SUMMARY")
        print(f"   Duration: {result['session_duration']}")
        print(f"   Successful scrapes: {result['successful_scrapes']}")
        print(f"   Failed scrapes: {result['failed_scrapes']}")
        print(f"   Success rate: {result['success_rate']:.1f}%")
        print(f"   Data saved to: {result['storage_path'] or 'Storage backend'}")
        print("Session completed")
