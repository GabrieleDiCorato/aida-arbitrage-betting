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
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from urllib.parse import urlparse
import time
from ..storage import CSVBettingOddsStorage, BettingOddsStorageBase

class ScraperBase(abc.ABC):
    """Base class for Selenium-based betting odds scrapers. Scraper instances are stateful and not thread-safe."""

    def __init__(self, storage: BettingOddsStorageBase, headless: bool = True):
        # Validate inputs
        if not storage or not isinstance(storage, BettingOddsStorageBase):
            raise ValueError("Storage must be an instance of BettingOddsStorageBase")
        if not isinstance(headless, bool):
            raise ValueError("Headless mode must be a boolean value")

        # Initialize state
        self.driver: webdriver.Chrome | None = None
        self.storage: BettingOddsStorageBase = storage or CSVBettingOddsStorage()
        self.headless: bool = headless
        self._is_running: bool = False

    def _setup_options(self) -> Options:
        chrome_options: Options = Options()
        if self.headless:
            chrome_options.add_argument("--headless=new")

        # Essential options only
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )
        chrome_options.add_experimental_option("useAutomationExtension", False)

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

        # Set window size for consistent layout
        chrome_options.add_argument(f"--window-size={self._get_window_size()}")
        return chrome_options

    def _setup_driver(self, chrome_options: Options) -> webdriver.Chrome:
        """Setup Chrome WebDriver, optimizing for speed and stealth."""

        # Initialize Chrome WebDriver with options
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove webdriver property
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Set timeouts
        driver.set_page_load_timeout(15)

        print("Chrome WebDriver setup successful")
        return driver

    def _setup_wait(self, driver: webdriver.Chrome) -> WebDriverWait:
        return WebDriverWait(driver, 10)

    @abc.abstractmethod
    def _get_window_size(self) -> str:
        """Site-specific window size setup for consistent layout.
        This method can be overridden in subclasses to set specific dimensions,
        which help ensure that elements are rendered correctly and efficiently."""
        return "1200,1080"

    @abc.abstractmethod
    def _handle_cookie_banner(self, driver: webdriver.Chrome, wait: WebDriverWait):
        """Handle cookie banner."""
        try:
            if not driver:
                return
            cookie_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "#onetrust-accept-btn-handler")
                )
            )
            cookie_button.click()
            print("Cookie banner accepted")
        except TimeoutException:
            print("No cookie banner found")
        except Exception as e:
            print(f"Cookie banner handling failed: {e}")
    
    def _navigate_and_setup_page(self, driver: webdriver.Chrome, wait: WebDriverWait, url: str) -> bool:
        """Navigate to the page and handle initial setup."""
        try:
            if not driver or not wait:
                print("Driver or wait not initialized")
                return False

            # Navigate to page
            print(f"Navigating to: {url}")
            driver.get(url)

            # Handle cookie banner
            self._handle_cookie_banner(driver, wait)

            # Wait for page to load
            self._wait_for_page_load(driver, wait)

            return True

        except Exception as e:
            print(f"Error setting up page: {e}")
            return False

    @abc.abstractmethod
    def _wait_for_page_load(self, driver: webdriver.Chrome, wait: WebDriverWait):
        """Wait for the main betting content to load."""
        try:
            if not wait:
                return
            wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), '1X2 ESITO FINALE')]")
                )
            )
            print("Page content loaded")
        except TimeoutException:
            print("Page content may not be fully loaded")

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

        self._is_running = False

    def scrape(
        self,
        url: str,
        duration_minutes: float | None = None,
        interval_seconds: int = 10,
    ) -> dict[str, Any]:
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

        print(
            f"Starting scraping session. Mode:",
            f"continuous ({duration_minutes} minutes)" if is_continuous else "one-shot",
        )
        print(f"    URL: {url}")

        if is_continuous:
            print(f"   Duration: {duration_minutes} minutes")
            print(f"   Interval: {interval_seconds} seconds")
        print(f"   Storage: {self.storage.__class__.__name__}")

        # Initialize session state
        self._is_running = True
        self._session_start_time = datetime.now()
        session_end_time = None
        if is_continuous and duration_minutes:
            session_end_time = self._session_start_time + timedelta(
                minutes=duration_minutes
            )
        successful_scrapes = 0
        failed_scrapes = 0
        scraped_data = []

        try:
            # Initialize storage
            if not self.storage._is_initialized:
                self.storage.initialize()

            # Setup browser
            if not self._setup_driver():
                return self._create_result_summary(
                    successful_scrapes, failed_scrapes, scraped_data
                )

            # Navigate to page initially
            if not self._navigate_and_setup_page(url):
                return self._create_result_summary(
                    successful_scrapes, failed_scrapes, scraped_data
                )

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
                            print(
                                f"{betting_odds.timestamp.strftime('%H:%M:%S')} - {betting_odds.home_team} vs {betting_odds.away_team} - 1X2: {betting_odds.home_win}/{betting_odds.draw}/{betting_odds.away_win}"
                            )
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
        result = self._create_result_summary(
            successful_scrapes, failed_scrapes, scraped_data
        )
        self._print_session_summary(result, is_continuous)

        return result
