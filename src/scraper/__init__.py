"""
Scraper package for extracting betting odds from various betting websites.

This package provides scrapers for different betting sites that can extract
live odds and convert them to standardized BettingOdds instances.
"""

from .sisal_scraper_v2 import SisalScraper, scrape_sisal_odds
from .sisal_selenium_scraper import SisalSeleniumScraper, scrape_sisal_odds_selenium

__all__ = [
    'SisalScraper', 'scrape_sisal_odds',
    'SisalSeleniumScraper', 'scrape_sisal_odds_selenium'
]
