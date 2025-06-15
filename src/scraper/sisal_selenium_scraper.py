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
from datetime import datetime
import csv
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from ..datamodel.betting_odds import BettingOdds


class SisalSeleniumScraper:
    """Simplified Sisal scraper focused on speed and reliability."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.wait: Optional[WebDriverWait] = None
        self.csv_file_path = None
        self.session_id = None
        
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
            
            print("✓ Chrome WebDriver setup successful")
            return True
            
        except Exception as e:
            print(f"✗ Failed to setup Chrome WebDriver: {e}")
            return False

    def scrape_betting_odds(self, url: str) -> Optional[BettingOdds]:
        """Main scraping method."""
        try:
            print(f"Starting scraping for: {url}")
            
            if not self.driver and not self._setup_driver():
                return None
            
            if not self.driver or not self.wait:
                print("✗ Driver or wait not initialized")
                return None
            
            # Navigate to page
            self.driver.get(url)
            
            # Handle cookie banner
            self._handle_cookie_banner()
            
            # Wait for page to load
            self._wait_for_page_load()
            
            # Extract data
            team_names = self._extract_team_names()
            if not team_names:
                print("✗ Could not extract team names")
                return None
                
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
            
            # Debug output
            self._print_debug_info(betting_odds)
            
            # Save to CSV
            self._save_betting_odds_to_csv(betting_odds)
            
            return betting_odds
            
        except Exception as e:
            print(f"✗ Scraping error: {e}")
            return None
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
                print("✓ Browser closed")

    def _wait_for_page_load(self):
        """Wait for the main betting content to load."""
        try:
            if not self.wait:
                return
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '1X2 ESITO FINALE')]"))
            )
            print("✓ Page content loaded")
        except TimeoutException:
            print("⚠ Page content may not be fully loaded")

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
                print(f"✓ Teams: {home_team} vs {away_team}")
                return (home_team, away_team)
                
        except NoSuchElementException:
            print("✗ Team names element not found")
        except Exception as e:
            print(f"✗ Error extracting team names: {e}")
        
        return None

    def _extract_odds(self) -> Dict[str, Optional[float]]:
        """Extract betting odds using optimized selectors."""
        odds_data = {}
        
        if not self.driver:
            return odds_data
        
        # Define selectors based on the HTML analysis
        selectors = {
            'home_win': 'button[data-qa*="_3_0_1"] span',
            'draw': 'button[data-qa*="_3_0_2"] span', 
            'away_win': 'button[data-qa*="_3_0_3"] span',
            'home_or_draw': 'button[data-qa*="_99999_0_1"] span',
            'away_or_draw': 'button[data-qa*="_99999_0_2"] span',
            'home_or_away': 'button[data-qa*="_99999_0_3"] span',
            'under_2_5': 'button[data-qa*="450_1"] span',
            'over_2_5': 'button[data-qa*="450_2"] span',
            'both_teams_score_yes': 'button[data-qa*="_8333_4_1"] span',
            'both_teams_score_no': 'button[data-qa*="_8333_4_2"] span',
        }
        
        for bet_type, selector in selectors.items():
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                odds_text = element.text.strip()
                
                if odds_text and odds_text != '-':
                    odds_value = float(odds_text)
                    if 1.0 <= odds_value <= 1000.0:
                        odds_data[bet_type] = odds_value
                        print(f"✓ {bet_type}: {odds_value}")
                    else:
                        print(f"⚠ {bet_type}: Invalid odds value {odds_value}")
                        
            except NoSuchElementException:
                print(f"⚠ {bet_type}: Not available")
            except (ValueError, AttributeError) as e:
                print(f"⚠ {bet_type}: Conversion error - {e}")
            except Exception as e:
                print(f"⚠ {bet_type}: Unexpected error - {e}")
        
        return odds_data

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
            print("✓ Cookie banner accepted")
        except TimeoutException:
            print("⚠ No cookie banner found")
        except Exception as e:
            print(f"⚠ Cookie banner handling failed: {e}")

    def _print_debug_info(self, betting_odds: BettingOdds):
        """Print extracted betting odds for debugging."""
        print(f"\n=== EXTRACTED BETTING ODDS ===")
        print(f"Match: {betting_odds.home_team} vs {betting_odds.away_team}")
        print(f"Match ID: {betting_odds.match_id}")
        print(f"Source: {betting_odds.source}")
        print(f"Timestamp: {betting_odds.timestamp}")
        
        if any([betting_odds.home_win, betting_odds.draw, betting_odds.away_win]):
            print(f"1X2: {betting_odds.home_win} | {betting_odds.draw} | {betting_odds.away_win}")
        
        if any([betting_odds.home_or_draw, betting_odds.away_or_draw, betting_odds.home_or_away]):
            print(f"Double Chance: 1X={betting_odds.home_or_draw} | X2={betting_odds.away_or_draw} | 12={betting_odds.home_or_away}")
        
        if any([betting_odds.over_2_5, betting_odds.under_2_5]):
            print(f"Over/Under 2.5: O={betting_odds.over_2_5} | U={betting_odds.under_2_5}")
        
        if any([betting_odds.both_teams_score_yes, betting_odds.both_teams_score_no]):
            print(f"Both Teams Score: Yes={betting_odds.both_teams_score_yes} | No={betting_odds.both_teams_score_no}")
        
        print(f"===============================\n")

    def _init_csv_session(self):
        """Initialize CSV session."""
        if self.session_id is None:
            self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
        csv_filename = f"sisal_odds_{self.session_id}.csv"
        self.csv_file_path = Path("data") / csv_filename
        self.csv_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self.csv_file_path.exists():
            self._write_csv_header()

    def _write_csv_header(self):
        """Write CSV header."""
        fieldnames = [
            'timestamp', 'source', 'match_id', 'home_team', 'away_team',
            'home_win', 'draw', 'away_win',
            'home_or_draw', 'away_or_draw', 'home_or_away',
            'over_2_5', 'under_2_5', 'over_3_5', 'under_3_5',
            'both_teams_score_yes', 'both_teams_score_no',
            'first_half_home_win', 'first_half_draw', 'first_half_away_win',
            'second_half_home_win', 'second_half_draw', 'second_half_away_win'
        ]
        
        with open(str(self.csv_file_path), 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    def _save_betting_odds_to_csv(self, betting_odds: BettingOdds):
        """Save betting odds to CSV file."""
        try:
            if self.csv_file_path is None:
                self._init_csv_session()
            
            csv_row = {
                'timestamp': betting_odds.timestamp.isoformat(),
                'source': betting_odds.source,
                'match_id': betting_odds.match_id,
                'home_team': betting_odds.home_team,
                'away_team': betting_odds.away_team,
                'home_win': betting_odds.home_win,
                'draw': betting_odds.draw,
                'away_win': betting_odds.away_win,
                'home_or_draw': betting_odds.home_or_draw,
                'away_or_draw': betting_odds.away_or_draw,
                'home_or_away': betting_odds.home_or_away,
                'over_2_5': betting_odds.over_2_5,
                'under_2_5': betting_odds.under_2_5,
                'over_3_5': betting_odds.over_3_5,
                'under_3_5': betting_odds.under_3_5,
                'both_teams_score_yes': betting_odds.both_teams_score_yes,
                'both_teams_score_no': betting_odds.both_teams_score_no,
                'first_half_home_win': betting_odds.first_half_home_win,
                'first_half_draw': betting_odds.first_half_draw,
                'first_half_away_win': betting_odds.first_half_away_win,
                'second_half_home_win': betting_odds.second_half_home_win,
                'second_half_draw': betting_odds.second_half_draw,
                'second_half_away_win': betting_odds.second_half_away_win
            }
            
            with open(str(self.csv_file_path), 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(csv_row.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writerow(csv_row)
            
            print(f"✓ Saved to CSV: {self.csv_file_path}")
            
        except Exception as e:
            print(f"✗ CSV save error: {e}")

    def close(self):
        """Close WebDriver and clean up."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                print("✓ Browser closed")
            except Exception as e:
                print(f"✗ Error closing browser: {e}")
