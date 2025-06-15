#!/usr/bin/env python3
"""
Example usage of the refactored Sisal scraper with dedicated storage.

This script demonstrates how to use the modular scraper and storage system.
"""

from src.scraper.sisal_selenium_scraper import SisalSeleniumScraper
from src.storage import CSVBettingOddsStorage, BettingOddsStorageBase
from datetime import datetime
import uuid


def main():
    """Example usage of the refactored scraper with dedicated storage."""
    
    print("=== Sisal Scraper with Dedicated Storage Example ===\n")
    
    # 1. Create a storage instance with a custom session ID
    session_id = f"example_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    storage = CSVBettingOddsStorage(
        session_id=session_id,
        output_dir="data/examples",
        filename_prefix="sisal_odds_example"
    )
    
    print(f"✓ Created storage with session ID: {session_id}")
    
    # 2. Create the scraper with the storage instance
    scraper = SisalSeleniumScraper(
        headless=True,  # Run in headless mode for this example
        storage=storage
    )
    
    print("✓ Created scraper with dedicated storage")
    
    # 3. Example URLs (you can replace with actual Sisal URLs)
    example_urls = [
        "https://www.sisal.it/scommesse/sport/calcio/match/123",
        # Add more URLs as needed
    ]
    
    print(f"\n=== Scraping {len(example_urls)} matches ===")
    
    # 4. Scrape the URLs
    results = []
    for i, url in enumerate(example_urls, 1):
        print(f"\n[{i}/{len(example_urls)}] Scraping: {url}")
        
        try:
            # The scraper will automatically use the storage instance to save data
            betting_odds = scraper.scrape_betting_odds(url)
            
            if betting_odds:
                results.append(betting_odds)
                print(f"✓ Successfully scraped {betting_odds.home_team} vs {betting_odds.away_team}")
            else:
                print("✗ Failed to scrape betting odds")
                
        except Exception as e:
            print(f"✗ Error scraping {url}: {e}")
    
    # 5. Close the scraper (this also closes the storage)
    scraper.close()
    
    # 6. Show results summary
    print(f"\n=== Scraping Summary ===")
    print(f"Total matches scraped: {len(results)}")
    print(f"Data saved to: {storage.get_file_path()}")
    
    if results:
        print("\nSample data:")
        sample = results[0]
        print(f"- Match: {sample.home_team} vs {sample.away_team}")
        print(f"- Home Win: {sample.home_win}")
        print(f"- Draw: {sample.draw}")
        print(f"- Away Win: {sample.away_win}")
    
    print("\n=== Example completed ===")


def demonstrate_custom_storage():
    """Demonstrate how to use a custom storage implementation."""
    
    print("\n=== Custom Storage Example ===")
    
    # You can create your own storage class by inheriting from BettingOddsStorageBase
    class MemoryStorage(BettingOddsStorageBase):
        """Example in-memory storage for demonstration."""
        
        def __init__(self):
            super().__init__()
            self.data = []
        
        def initialize(self):
            if not self._is_initialized:
                print("✓ Memory storage initialized")
                self._is_initialized = True
        
        def store(self, betting_odds):
            self._ensure_initialized()
            self.data.append(betting_odds)
            print(f"✓ Stored in memory: {betting_odds.home_team} vs {betting_odds.away_team}")
        
        def store_batch(self, betting_odds_list):
            self._ensure_initialized()
            self.data.extend(betting_odds_list)
            print(f"✓ Stored batch of {len(betting_odds_list)} records in memory")
        
        def close(self):
            print(f"✓ Memory storage closed with {len(self.data)} records")
            self._is_initialized = False
    
    # Use the custom storage
    custom_storage = MemoryStorage()
    scraper = SisalSeleniumScraper(headless=True, storage=custom_storage)
    
    print("✓ Created scraper with custom memory storage")
    print("This demonstrates the flexibility of the storage system")
    
    # Don't forget to close
    scraper.close()


if __name__ == "__main__":
    # Run the main example
    main()
    
    # Demonstrate custom storage
    demonstrate_custom_storage()
