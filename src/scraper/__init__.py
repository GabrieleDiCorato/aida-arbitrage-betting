"""
Scraper package for extracting betting odds from betting websites.

This package provides Selenium-based scrapers that use real browsers
to extract live odds and convert them to standardized BettingOdds instances.
"""

from .sisal.scraper_sisal import SisalScraper
from .lottomatica.scraper_lottomatica import LottomaticaScraper

__all__ = ['SisalScraper', 'LottomaticaScraper']
