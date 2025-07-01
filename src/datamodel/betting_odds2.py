from datetime import datetime
from attr import frozen
from pydantic import BaseModel, field_validator, ConfigDict, PositiveFloat, Strict, StrictStr
from typing import Annotated
import annotated_types as at
from .data_sources import DataSource
from .etl_version import EtlVersion
from .sport import Sport

class BaseModelWithConfig(BaseModel):
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

# Type aliases for improved readability
QuoteValue = Annotated[float, at.Gt(1.0), Strict()]
QuotesByName = Annotated[dict[StrictStr, QuoteValue], at.MinLen(1)]
MatchQuotesByType = Annotated[dict[StrictStr, QuotesByName], at.MinLen(1)]

class Match(BaseModelWithConfig):
    """ Data model for a specific match with betting odds."""
    
    # Match ID
    match_id: StrictStr
    
    # Metadata (repeated across all matches for downstream processing)
    source: DataSource
    timestamp: datetime
    etl_version: EtlVersion = EtlVersion.ONE
    sport: Sport  
    league: str | None = None
    
    # Odds for the match
    # dict[str, dict[str, float]] where the first key is the quote type (e.g., "1x2" or "over/under"), 
    # the second key is the outcome (e.g., "1", "goal", "X2"), and the value is the quote (must be > 1.0).
    quotes: MatchQuotesByType

class BettingOdds2(BaseModelWithConfig):
    """ Data model for timestamped betting odds from a specific source."""
    
    matches: Annotated[list[Match], at.MinLen(1)]
