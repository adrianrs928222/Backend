from typing import List, Literal, Optional
from pydantic import BaseModel


Color = Literal['verde', 'amarillo', 'rojo']
Verdict = Literal['Sí', 'No']


class MatchOut(BaseModel):
    fixture_id: int
    competition: str
    date: str
    status: str
    home_team: str
    away_team: str


class PickOut(BaseModel):
    fixture_id: int
    competition: str
    match: str
    market: str
    probability: int
    verdict: Verdict
    color: Color
    explanation: str
    starts_at: str
    team: Optional[str] = None


class PicksResponse(BaseModel):
    date: str
    picks: List[PickOut]
