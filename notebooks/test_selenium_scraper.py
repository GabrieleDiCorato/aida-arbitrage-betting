#!/usr/bin/env python3
"""
Test the Selenium-based Sisal scraper.

This script tests the new Selenium scraper that uses a real Chrome browser
to bypass anti-bot detection.
"""

import sys
import os

# Add the project root to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.scraper.sisal_selenium_scraper import scrape_sisal_odds_selenium


def main():
    """Test the Selenium scraper."""
    print("=== Selenium Sisal Scraper Test ===")
    print()
    print("🤖 This scraper uses a real Chrome browser to bypass detection")
    print("📋 Testing with the provided URL...")
    print()
    
    # Test URL provided by user
    test_url = "https://www.sisal.it/scommesse-live/evento/calcio/irlanda/premier-division/sligo-rovers-waterford-fc"
    
    print(f"🎯 Testing URL: {test_url}")
    print()
    print("⏱️ This may take 30-60 seconds as we:")
    print("   1. Launch Chrome browser")
    print("   2. Visit Sisal homepage")
    print("   3. Navigate to live betting")
    print("   4. Load the match page")
    print("   5. Extract odds data")
    print()
    
    try:
        # Test with headless mode (no visible browser window)
        print("🔍 Running in headless mode (no visible browser)...")
        odds = scrape_sisal_odds_selenium(test_url, headless=True)
        
        if odds:
            print()
            print("🎉 SUCCESS! Selenium scraper worked!")
            print("=" * 50)
            print()
            print("📊 Match Details:")
            print(f"   Source: {odds.source}")
            print(f"   Match ID: {odds.match_id}")
            print(f"   Home Team: {odds.home_team}")
            print(f"   Away Team: {odds.away_team}")
            print(f"   Timestamp: {odds.timestamp}")
            print()
            
            print("🎲 Extracted Odds:")
            if odds.home_win and odds.draw and odds.away_win:
                print(f"   1X2 (Match Result): {odds.home_win} / {odds.draw} / {odds.away_win}")
            
            if odds.over_2_5 and odds.under_2_5:
                print(f"   Over/Under 2.5 Goals: {odds.over_2_5} / {odds.under_2_5}")
            
            if odds.both_teams_score_yes and odds.both_teams_score_no:
                print(f"   Both Teams Score: {odds.both_teams_score_yes} / {odds.both_teams_score_no}")
            
            if odds.home_or_draw and odds.away_or_draw and odds.home_or_away:
                print(f"   Double Chance: {odds.home_or_draw} / {odds.away_or_draw} / {odds.home_or_away}")
            
            print()
            print("✅ Selenium scraper successfully bypassed all anti-bot measures!")
            
        else:
            print()
            print("❌ Selenium scraper failed to extract odds")
            print()
            print("🔧 Troubleshooting suggestions:")
            print("1. Check if Chrome browser is installed")
            print("2. Verify the match URL is currently live")
            print("3. Try running with headless=False to see what's happening")
            print("4. Check internet connection")
            
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        print("🔧 Common solutions:")
        print("1. Install Chrome browser: https://www.google.com/chrome/")
        print("2. Check if chromedriver is compatible with your Chrome version")
        print("3. Try running as administrator")
        print("4. Check firewall/antivirus settings")
        
        import traceback
        print()
        print("📋 Full error traceback:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
