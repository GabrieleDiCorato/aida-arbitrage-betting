"""
Pydantic-based data models for betting odds with strict validation and immutability.

This module defines a hierarchical data structure for betting odds data:
- BettingOdds: Top-level container for one or more matches
- Match: Individual match with metadata and quotes
- Odds: Collection of odds for a specific betting market (e.g., 1X2, Over/Under)
- Odd: Individual betting odd with name and value
"""

from datetime import datetime
from attr import frozen
from pydantic import BaseModel, field_validator, ConfigDict, PositiveFloat, Strict, StrictStr
from typing import Annotated
import annotated_types as at
from .data_sources import DataSource
from .etl_version import EtlVersion

class BaseModelWithConfig(BaseModel):
    """
    Base Pydantic model with shared configuration for all betting odds models.
    
    This base class enforces strict validation and immutability across all
    models in the betting odds hierarchy. All models inherit this configuration
    to ensure consistent behavior throughout the data pipeline.
    
    Configuration enforces:
    - Strict type checking (no implicit coercion)
    - Immutability after creation
    - No additional fields beyond those defined
    - Validation of all values including defaults
    - Rejection of NaN/Infinity values for numeric fields
    """
    model_config = ConfigDict(
        strict=True,  # Enforce type checking, do not allow implicit type coercion
        extra='forbid',  # Disallow extra fields
        validate_default=True,  # Validate default values
        validate_assignment=False,  # Don't validate on assignment, this class is immutable
        frozen=True,    # Make the model immutable
        use_enum_values=True,  # Use enum values directly
        allow_inf_nan=False,  # Disallow NaN and Infinity values
        cache_strings=True,  # Cache strings for performance
    )

class Odd(BaseModelWithConfig):
    """
    Represents a single betting odd with a name and numerical value.
    """
    odd_name: StrictStr # Descriptive name of the betting option (e.g., "home_win", "over_2_5")
    value: Annotated[float, at.Gt(1.0), Strict()] # AllowInfNan(False) implicit in config

class Odds(BaseModelWithConfig):
    """
    Collection of betting odds for a specific betting market.
    
    Groups related betting options together (e.g., all 1X2 odds, all Over/Under odds).
    Each odds collection has a type identifier and contains at least one betting odd.
    """
    odds_type: StrictStr    # Type identifier for the betting market (e.g., "1x2", "over_under", "btts")
    odds: Annotated[dict[StrictStr, Odd], at.MinLen(1)] #  Dictionary mapping odd names to Odd objects, must contain at least one entry

class Match(BaseModelWithConfig):
    """
    Represents a single match with its metadata and betting quotes.
    
    Contains all the betting odds for one specific match, along with essential
    metadata for tracking and processing. Each match belongs to a specific
    data source and has a timestamp for when the odds were captured.
    """
    # Match identification
    match_id: StrictStr # Unique identifier for the match (from the betting platform)
    
    # Metadata (repeated across all matches for downstream processing)
    source: DataSource  # Enum: SISAL, LOTTOMATICA, etc.
    timestamp: datetime  # When the odds were captured (should be UTC)
    etl_version: EtlVersion = EtlVersion.ONE  # ETL pipeline version for reproducibility
    
    # Odds for the match
    quotes: Annotated[dict[StrictStr, Odds], at.MinLen(1)] # Dictionary of betting markets, each containing multiple odds

class BettingOdds(BaseModelWithConfig):
    """
    Top-level container for betting odds data from one or more matches.
    
    This is the main data structure used throughout the arbitrage betting pipeline.
    It can contain odds for multiple matches, making it suitable for batch processing
    or real-time streaming scenarios.
    """
    
    matches: Annotated[list[Match], at.MinLen(1)] # List of Match objects, must contain at least one match