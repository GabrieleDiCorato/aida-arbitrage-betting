from datetime import datetime
from attr import frozen
from pydantic import BaseModel, field_validator, ConfigDict, PositiveFloat, Strict, StrictStr
from typing import Annotated
import annotated_types as at
from .data_sources import DataSource
from .etl_version import EtlVersion

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

class Odd(BaseModelWithConfig):
    
    odd_name: StrictStr
    value: Annotated[float, at.Gt(1.0), Strict()] # AllowInfNan(False) implicit in config

class Odds(BaseModelWithConfig):

    odds_type: StrictStr
    odds: Annotated[dict[StrictStr, Odd], at.MinLen(1)]

class Match(BaseModelWithConfig):
    
    # Match ID
    match_id: StrictStr
    
    # Metadata (repeated across all matches for downstream processing)
    source: DataSource
    timestamp: datetime
    etl_version: EtlVersion = EtlVersion.ONE
    
    # Odds for the match
    quotes: Annotated[dict[StrictStr, Odds], at.MinLen(1)]

class BettingOdds(BaseModelWithConfig):
    
    matches: Annotated[list[Match], at.MinLen(1)]