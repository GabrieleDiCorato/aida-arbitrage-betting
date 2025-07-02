"""
Simplified Selenium-based Sisal website scraper for live betting odds.
"""

import abc
from typing import Any

from pydantic_core import Url
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

from src.datamodel.betting_odds import BettingOdds2
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
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
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

    def _navigate_and_setup_page(
        self, driver: webdriver.Chrome, wait: WebDriverWait, url: Url
    ):
        """Navigate to the page and handle initial setup."""

        if not driver or not wait:
            raise RuntimeError("Driver or wait not initialized")

        # Validate
        if not url or not isinstance(url, Url):
            raise RuntimeError("Invalid URL provided")
        elif url.scheme not in ["https"]:
            raise RuntimeError(f"Invalid URL scheme: {url.scheme}. Expected 'https'.")
        elif not url.path:
            raise RuntimeError("URL path is empty")

        print(f"Navigating to: {url.path}")
        driver.get(url.path)

        # Handle cookie banner
        self._handle_cookie_banner(driver, wait)

        # Wait for page to load
        self._wait_for_page_load(driver, wait)

        print("Page navigation and setup complete")

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

    @abc.abstractmethod
    def _extract_betting_data(self, url: Url) -> BettingOdds2:
        """Extract betting data from the page.
        This method should be implemented in subclasses to handle specific page structures.
        """
        pass

    def scrape(
        self,
        url: Url,
        duration_minutes: float = 0,
        interval_seconds: int = 0,
    ) -> BettingOdds2:
        """
        Unified scraping method that handles both one-shot and continuous scraping.

        Args:
            url: The URL of the Sisal betting page to scrape
            duration_minutes: How long to run scraping (0 for one-shot, > 0 for continuous. Default: 0)
            interval_seconds: How often to scrape data in continuous mode (default: 0 seconds for one-shot)

        Returns:
            Dictionary with scraping results including successful_scrapes count and data
        """
        if self._is_running:
            raise RuntimeError("Scraper is already running")

        # Determine scraping mode and validate parameters
        is_continuous = abs(duration_minutes) > 1e-6
        if is_continuous and (duration_minutes < 0 or interval_seconds <= 0):
            raise ValueError("Invalid continuous scraping config. Duration must be >= 0 and interval must be > 0 seconds")

        print(
            f"Starting scraping.",
            f"Mode: [" + 
                ("continuous (duration={duration_minutes}min, freq={interval_seconds}sec)" if is_continuous else "one-shot")
            + "]",
            "URL: [{url}]",
        )
        print(f"Storage: {self.storage.__class__.__name__}")

        self._is_running = True

        try:
            # Initialize storage
            if not self.storage._is_initialized:
                self.storage.initialize()

            # Initialize webdriver and wait
            options: Options = self._setup_options()
            self.driver = self._setup_driver(options)
            wait: WebDriverWait = self._setup_wait(self.driver)

            # Navigate to page
            self._navigate_and_setup_page(self.driver, wait, url)

            # Initialize session state
            session_start_time, session_end_time = self.get_start_end_times(duration_minutes)

            # Scraping loop (runs once for one-shot, multiple times for continuous)
            while self._is_running:
                try:
                    # Extract data
                    betting_odds = self._extract_betting_data(url)

                    if betting_odds:
                        # Store data
                        print(betting_odds.model_dump())
                        self.storage.store(betting_odds)
                    else:
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

    @staticmethod
    def get_start_end_times(duration_minutes) -> tuple[datetime, datetime]:
        session_start_time: datetime = datetime.now()
        session_end_time: datetime = session_start_time + timedelta(
            minutes=duration_minutes
        )
        return (session_start_time, session_end_time)
