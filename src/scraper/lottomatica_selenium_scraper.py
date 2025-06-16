"""
Simplified Selenium-based Lottomatica website scraper for live betting odds.
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
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import time
import signal
import sys
from ..datamodel.betting_odds import BettingOdds
from ..storage import CSVBettingOddsStorage, BettingOddsStorageBase


class LottomaticaSeleniumScraper:
    """Simplified Lottomatica scraper focused on speed and reliability."""
    
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
        """Wait for the page to load by checking for team names."""
        try:
            if not self.wait:
                return
            # Wait for team names to appear - indicates page is fully loaded
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.event-name"))
            )
            print("Page loaded - team names visible")
        except TimeoutException:
            print("Timeout waiting for team names to load")
            raise

    def _extract_team_names(self) -> Optional[tuple]:
        """Extract team names from Lottomatica page structure."""
        try:
            if not self.driver:
                return None
            
            # Only use the primary selector - no fallbacks
            element = self.driver.find_element(By.CSS_SELECTOR, ".sub-header .event-name")
            match_text = element.text.strip()
            
            if match_text and " - " in match_text:
                teams = match_text.split(" - ", 1)
                home_team = teams[0].strip()
                away_team = teams[1].strip()
                if home_team and away_team:
                    print(f"Teams: {home_team} vs {away_team}")
                    return (home_team, away_team)
                    
        except Exception as e:
            print(f"Error extracting team names: {e}")
        
        return None    
    
    def _extract_odds(self) -> Dict[str, Optional[float]]:
        """Extract betting odds using text-based matching approach."""
        odds_data = {}
        
        if not self.driver:
            return odds_data
        
        try:
            # Find the expected containers by looking for slot-headers
            slot_headers = self.driver.find_elements(By.CSS_SELECTOR, ".slot-header")

            for header in slot_headers:
                # Get the parent slot-container
                slot_container = header.find_element(By.XPATH, "..")
                
                header_text = header.text.strip().casefold()  # Remove leading/trailing spaces
                if header_text == "1X2".casefold():
                    odds_data.update(self._extract_1x2_main(slot_container))
                elif header_text == "Doppia Chance".casefold():
                    odds_data.update(self._extract_double_chance(slot_container))
                elif header_text == "Gol/Nogol".casefold():
                    odds_data.update(self._extract_both_teams_score(slot_container))
                elif header_text == "Under/Over".casefold():
                    odds_data.update(self._extract_over_under(slot_container))
                else:
                    # Skip any other headers
                    continue
                
        except Exception as e:
                    print(f"Error extracting odds: {e}")
        
        return odds_data

    def _extract_1x2_main(self, slot_container) -> Dict[str, Optional[float]]:
        """Extract main 1X2 market odds using direct selector."""
        odds_data = {}
        
        try:          
            # Extract the three quotes in order: 1, X, 2
            wrappers = slot_container.find_elements(By.CSS_SELECTOR, ".single-quota-wrapper")
            
            if len(wrappers) >= 3:
                # First wrapper: "1" (home win)
                home_odds = self._extract_odds_from_wrapper(wrappers[0])
                if home_odds is not None:
                    odds_data['home_win'] = home_odds
                
                # Second wrapper: "X" (draw) 
                draw_odds = self._extract_odds_from_wrapper(wrappers[1])
                if draw_odds is not None:
                    odds_data['draw'] = draw_odds
                
                # Third wrapper: "2" (away win)
                away_odds = self._extract_odds_from_wrapper(wrappers[2])
                if away_odds is not None:
                    odds_data['away_win'] = away_odds
                
                if any(odds_data.values()):
                    print("1X2 Main odds extracted")
                    
        except Exception as e:
            print(f"Error extracting 1X2 odds: {e}")
        
        return odds_data

    def _extract_double_chance(self, slot_container) -> Dict[str, Optional[float]]:
        """Extract double chance market odds using precise selector based on HTML structure."""
        odds_data = {}
        
        try:
            # Extract the three quotes in fixed order: 1X, X2, 12
            wrappers = slot_container.find_elements(By.CSS_SELECTOR, ".single-quota-wrapper")
            
            if len(wrappers) >= 3:
                # First wrapper: "1X" (home or draw)
                home_or_draw_odds = self._extract_odds_from_wrapper(wrappers[0])
                if home_or_draw_odds is not None:
                    odds_data['home_or_draw'] = home_or_draw_odds
                
                # Second wrapper: "X2" (away or draw) 
                away_or_draw_odds = self._extract_odds_from_wrapper(wrappers[1])
                if away_or_draw_odds is not None:
                    odds_data['away_or_draw'] = away_or_draw_odds
                
                # Third wrapper: "12" (home or away)
                home_or_away_odds = self._extract_odds_from_wrapper(wrappers[2])
                if home_or_away_odds is not None:
                    odds_data['home_or_away'] = home_or_away_odds
                
                if any(odds_data.values()):
                    print("Double Chance odds extracted")
            
        except Exception as e:
            print(f"Error extracting Double Chance odds: {e}")
        
        return odds_data

    def _extract_over_under(self, container) -> Dict[str, Optional[float]]:
        """Extract over/under goals market odds using optimized selector."""
        odds_data = {}
        
        try:
            # Find quote wrappers with data-spreadid in the passed container
            # One quote wrapper per spread (2.5, 1.5, etc.)
            quote_wrappers = container.find_elements(By.CSS_SELECTOR, "div.quote-wrapper[data-spreadid]")

            for quote_wrapper in quote_wrappers:
                spread_id = quote_wrapper.get_attribute("data-spreadid")

                # Get all single quota wrappers in this spread
                single_wrappers = quote_wrapper.find_elements(By.CSS_SELECTOR, ".single-quota-wrapper")

                # Skip if spread_id is not one of the expected values
                if spread_id == '1.5':
                    under15 = self._extract_odds_from_wrapper(single_wrappers[0])
                    if under15 is not None:
                        odds_data['under_1_5'] = under15
                    over15 = self._extract_odds_from_wrapper(single_wrappers[1])
                    if over15 is not None:
                        odds_data['over_1_5'] = over15
                elif spread_id == '2.5':
                    under25 = self._extract_odds_from_wrapper(single_wrappers[0])
                    if under25 is not None:
                        odds_data['under_2_5'] = under25
                    over25 = self._extract_odds_from_wrapper(single_wrappers[1])
                    if over25 is not None:
                        odds_data['over_2_5'] = over25
                elif spread_id == '3.5':
                    under35 = self._extract_odds_from_wrapper(single_wrappers[0])
                    if under35 is not None:
                        odds_data['under_3_5'] = under35
                    over35 = self._extract_odds_from_wrapper(single_wrappers[1])
                    if over35 is not None:
                        odds_data['over_3_5'] = over35
                else:
                    continue
                  
        except Exception as e:
            print(f"Error extracting Over/Under odds: {e}")
            
        return odds_data

    def _extract_both_teams_score(self, slot_container) -> Dict[str, Optional[float]]:
        """Extract both teams to score (Gol/NoGol) market odds using precise selector based on HTML structure."""
        odds_data = {}
        
        try:         
            # Extract the two quotes in fixed order: GG first, then NG
            wrappers = slot_container.find_elements(By.CSS_SELECTOR, ".single-quota-wrapper")
            
            if len(wrappers) >= 2:
                # First wrapper: "GG" (both teams score)
                gg_odds = self._extract_odds_from_wrapper(wrappers[0])
                if gg_odds is not None:
                    odds_data['both_teams_score_yes'] = gg_odds
                
                # Second wrapper: "NG" (not both teams score)
                ng_odds = self._extract_odds_from_wrapper(wrappers[1])
                if ng_odds is not None:
                    odds_data['both_teams_score_no'] = ng_odds
                
                if any(odds_data.values()):
                    print("Gol/NoGol odds extracted")
            
        except Exception as e:
            print(f"Error extracting Gol/NoGol odds: {e}")
        
        return odds_data

    def _extract_odds_from_wrapper(self, wrapper) -> Optional[float]:
        """Extract odds from a single wrapper, handling disabled markets."""
        try:
            # Try to get odds value
            try:
                odds_element = wrapper.find_element(By.CSS_SELECTOR, ".item--valore span")
                odds_text = odds_element.text.strip()
                if odds_text:
                    odds_value = float(odds_text.replace(',', '.'))
                    return odds_value
            except NoSuchElementException:
                # Market is disabled (has lock icon instead of odds)
                return None
            
        except Exception as e:
            print(f"Error extracting odds from wrapper: {e}")
            
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
        
        if any([betting_odds.over_1_5, betting_odds.under_1_5]):
            print(f"O/U 1.5: {betting_odds.over_1_5} / {betting_odds.under_1_5}")
        
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
            url: The URL of the Lottomatica betting page to scrape
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
            # Extract team names - if not found, skip this scrape
            team_names = self._extract_team_names()
            if not team_names:
                print("Could not extract team names - skipping")
                return None
            
            # Extract odds data
            odds_data = self._extract_odds()
            match_id = self._generate_match_id(url)
            
            # Create BettingOdds instance with only available data
            betting_odds = BettingOdds(
                timestamp=datetime.now(),
                source="Lottomatica",
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
