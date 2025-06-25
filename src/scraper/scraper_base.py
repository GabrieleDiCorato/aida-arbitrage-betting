"""
Simplified Selenium-based Sisal website scraper for live betting odds.
"""

import abc
from typing import Any

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time
import signal
from ..datamodel.betting_odds import BettingOdds
from ..storage import CSVBettingOddsStorage, BettingOddsStorageBase


class ScraperBase(abc.ABC):
    """Base class for Selenium-based betting odds scrapers."""
    
    def __init__(
            self, 
            headless: bool = True, 
            storage: BettingOddsStorageBase | None = None
    ):
        self.headless = headless
        self.driver: webdriver.Chrome | None = None
        self.wait: WebDriverWait | None = None
        self.storage = storage or CSVBettingOddsStorage()
        self._is_running = False
        self._session_start_time: datetime | None = None
        
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

    @abc.abstractmethod
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

    @abc.abstractmethod
    def _extract_team_names(self) -> tuple[str, str] | None:
        """Extract team names using the dropdown button selector."""
        pass  # To be implemented in subclasses

    @abc.abstractmethod
    def _extract_odds(self) -> dict[str, float] | None:
        """Extract betting odds using optimized selectors."""
        odds_data: dict[str, float] = {}
        
        if not self.driver:
            return odds_data
        
        # Extract each market using data-qa patterns
        main_1x2 = self._extract_1x2_main()
        if main_1x2:
            odds_data.update(main_1x2)
        double_chance = self._extract_double_chance()
        if double_chance:
            odds_data.update(double_chance)
        over_under = self._extract_over_under()
        if over_under:
            odds_data.update(over_under)
        both_teams_score = self._extract_both_teams_score()
        if both_teams_score:
            odds_data.update(both_teams_score)
        
        return odds_data

    @abc.abstractmethod
    def _extract_1x2_main(self) -> dict[str, float] | None:
        """Extract main 1X2 market odds."""
        pass

    @abc.abstractmethod
    def _extract_double_chance(self) -> dict[str, float] | None:
        """Extract double chance market odds."""
        pass

    @abc.abstractmethod
    def _extract_over_under(self) -> dict[str, float] | None:
        """Extract over/under goals market odds."""
        pass

    @abc.abstractmethod
    def _extract_both_teams_score(self) -> dict[str, float] | None:
        """Extract both teams to score (GOAL/NOGOAL) market odds."""
        pass
    
    @classmethod
    def _generate_match_id(cls, team1: str, team2: str) -> str:
        """Generate match ID from team names."""
        return f"{team1.lower().replace(' ', '-')}_{team2.lower().replace(' ', '-')}"

    @abc.abstractmethod
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

    def scrape(self, url: str, duration_minutes: float | None = None, interval_seconds: int = 10) -> dict[str, Any]:
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
                            print(betting_odds)
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
    
    @abc.abstractmethod
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
    
    @abc.abstractmethod
    def _extract_betting_data(self, url: str) -> BettingOdds | None:
        """Extract betting odds data from the current page."""
        try:
            # Extract team names
            team_names = self._extract_team_names()
            if not team_names:
                print("Could not extract team names")
                return None
            
            # Extract odds data
            match_id = ScraperBase._generate_match_id(*team_names)
            odds_data: dict[str, float] | None = self._extract_odds()
            
            # Create BettingOdds instance
            betting_odds = BettingOdds(
                timestamp=datetime.now(),
                source="Sisal",
                match_id=match_id,
                home_team=team_names[0],
                away_team=team_names[1],
                **(odds_data or {})
            )
            
            return betting_odds
            
        except Exception as e:
            print(f"Error extracting betting data: {e}")
            return None

    def _create_result_summary(self, successful_scrapes: int, failed_scrapes: int, scraped_data: list) -> dict[str, Any]:
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
    
    def _print_session_summary(self, result: dict[str, Any], is_continuous: bool) -> None:
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
