"""
Scraper package for extracting betting odds from betting websites.

This package provides Selenium-based scrapers that use real browsers
to extract live odds and convert them to standardized BettingOdds instances.
"""

from .sisal_selenium_scraper import SisalSeleniumScraper, scrape_sisal_odds_selenium

__all__ = ['SisalSeleniumScraper', 'scrape_sisal_odds_selenium']
