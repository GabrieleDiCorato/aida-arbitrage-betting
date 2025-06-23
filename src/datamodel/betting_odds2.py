from pydantic import BaseModel, field_validator
from typing import List, Dict

class Odd(BaseModel):
    odd_name: str
    value: float
    
    @field_validator('value')
    def greater_than_one(cls, v):
        if not v or v <= 1:
            raise ValueError('Value must be greater than 1')
        return v

class Odds(BaseModel):
    odds_type: str
    odds: List[Odd]
    
    @field_validator('odds')
    def odds_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('odds list cannot be empty')
        return v

class Match(BaseModel):
    match_id: int
    tags: List[Odds]

class BettingOdds(BaseModel):
    matches: List[Match]
    
    def to_dict(self) -> Dict:
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict):
        return cls(**data)