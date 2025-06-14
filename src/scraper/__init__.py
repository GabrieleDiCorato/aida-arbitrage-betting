"""
Scraper package for extracting betting odds from various betting websites.

This package provides scrapers for different betting sites that can extract
live odds and convert them to standardized BettingOdds instances.
"""

from .sisal_scraper import SisalScraper, scrape_sisal_odds

__all__ = ['SisalScraper', 'scrape_sisal_odds']
