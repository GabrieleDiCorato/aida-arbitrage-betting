# AIDA Arbitrage Betting Analysis

## Project Overview

This project is part of a web scraping challenge for my AI & Data Analytics master's program. The objective is to explore web scraping techniques by extracting and analyzing live betting odds data to identify potential arbitrage opportunities.

## Project Description

For this web scraping assignment, I chose to focus on the **PSG vs Atletico Madrid** football match. The project involves:

1. **Data Collection**: Scraping live betting odds from multiple betting sources during the match
2. **Data Storage**: Publishing scraped data to a local MongoDB instance
3. **Analysis**: Post-match analysis to identify arbitrage opportunities that occurred during the game

## What is Arbitrage Betting?

Arbitrage betting is a strategy that involves placing bets on all possible outcomes of an event across different bookmakers to guarantee a profit regardless of the result. This occurs when bookmakers offer different odds for the same event, creating opportunities where the combined probability is less than 100%.

## Project Structure

- **Scrapers**: Multiple web scrapers targeting different betting platforms
- **Database**: Local MongoDB instance for real-time data storage
- **Analysis**: Data analysis notebooks to identify arbitrage opportunities

## Refactored Architecture

The project has been refactored to use a modular, flexible storage system with clear separation of concerns:

### Storage Module (`src/storage/`)

- **`BettingOddsStorageBase`**: Abstract base class defining the storage interface
- **`CSVBettingOddsStorage`**: CSV file-based storage implementation
- **Session Management**: Each scraping session gets a unique identifier
- **Encapsulation**: All storage logic is contained within dedicated storage classes

### Key Features

1. **Modular Design**: Easy to add new storage backends (JSON, Database, etc.)
2. **Session-based Storage**: Each scraping session creates uniquely identified files
3. **Clean Separation**: Scrapers focus on scraping, storage handles persistence
4. **Flexible Interface**: Support for single record and batch operations

### Usage Example

```python
from src.scraper.sisal_selenium_scraper import SisalSeleniumScraper
from src.storage import CSVBettingOddsStorage

# Create storage with custom session
storage = CSVBettingOddsStorage(
    session_id="match_20240101",
    output_dir="data/matches"
)

# Create scraper with the storage
scraper = SisalSeleniumScraper(headless=True, storage=storage)

# Single scrape - data is automatically stored
betting_odds = scraper.scrape_betting_odds(url)

# Close resources
scraper.close()
```

### Continuous Scraping

The scraper now supports continuous data extraction at regular intervals:

```python
# Continuous scraping for live odds monitoring
scraper = SisalSeleniumScraper(headless=True, storage=storage)

# Scrape every 10 seconds for 30 minutes
successful_scrapes = scraper.scrape_continuously(
    url="https://www.sisal.it/scommesse/sport/calcio/match/123",
    duration_minutes=30,
    interval_seconds=10
)

scraper.close()
```

#### Command Line Usage

```bash
# Basic continuous scraping
python continuous_scraping_example.py "https://www.sisal.it/scommesse/sport/calcio/match/123"

# Custom parameters
python continuous_scraping_example.py "https://..." --duration 60 --interval 15 --headless
```

#### Key Features

- **Timed Sessions**: Automatically stops after specified duration
- **Regular Intervals**: Consistent data extraction timing
- **Session Management**: Unique CSV files for each scraping session
- **Graceful Shutdown**: Handles interruption (Ctrl+C) properly
- **Progress Monitoring**: Real-time statistics and progress updates
- **Error Resilience**: Continues running even if individual scrapes fail

### Custom Storage Implementation

You can easily create custom storage backends by inheriting from `BettingOddsStorageBase`:

```python
from src.storage import BettingOddsStorageBase

class DatabaseStorage(BettingOddsStorageBase):
    def initialize(self):
        # Connect to database
        pass
    
    def store(self, betting_odds):
        # Store to database
        pass
    
    def close(self):
        # Close database connection
        pass
```

## Technical Stack

- **Python**: Main programming language
- **MongoDB**: Database for storing betting odds data
- **Jupyter Notebooks**: For data analysis and visualization
- **Web Scraping Libraries**: For extracting betting odds from various sources

## Goals

1. Successfully scrape live betting odds from multiple sources
2. Store data efficiently in MongoDB with proper timestamps
3. Analyze the collected data to identify arbitrage opportunities
4. Visualize odds movements and potential profit margins over time

## Academic Context

This project demonstrates practical application of web scraping techniques learned in the AI & Data Analysis master's program, focusing on real-time data collection and financial data analysis.

## ⚠️ Legal Disclaimer

**IMPORTANT: This is a one-time, academic-only study for educational purposes.**

- This project is conducted solely for academic research as part of a university master's program
- The web scraping activities are limited to a single sporting event for educational analysis
- This code and methodology should **NOT** be replicated or used for commercial purposes
- Users are strongly discouraged from using this project for actual betting or financial activities
- Web scraping betting sites may violate their Terms of Service - always check and comply with website policies
- Arbitrage betting may be prohibited by betting platforms and could result in account restrictions
- The authors assume no responsibility for any misuse of this code or methodology
- This project is not intended to encourage gambling or betting activities
- **NO ACTUAL BETTING DATA IS STORED IN THIS REPOSITORY** - only code for educational purposes
- Users must obtain proper permissions before scraping any websites
- This repository is provided "AS IS" without warranty of any kind

**Use of this code is at your own risk and responsibility. The author disclaims all liability for any damages arising from the use of this software.**
