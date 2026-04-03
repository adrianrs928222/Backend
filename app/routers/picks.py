from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.models.schemas import MatchOut, PickOut, PicksResponse
from app.services.api_football import ApiFootballService, ALLOWED_LEAGUES
from app.services.scoring import (
    classify,
    extract_team_recent_stats,
    market_btts,
    market_over25,
    market_winner,
)

router = APIRouter()
service = ApiFootballService()


def today_str() -> str:
    return datetime.now(ZoneInfo(settings.tz)).date().isoformat()


@router.get('/health')
async def health() -> Dict[str, str]:
    return {'status': 'ok'}


@router.get('/matches-today', response_model=List[MatchOut])
async def matches_today() -> List[MatchOut]:
    try:
        fixtures = await service.fixtures_by_date(today_str())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'Error consultando API-Football: {e}')

    result: List[MatchOut] = []
    for fx in fixtures:
        league_name = fx.get('league', {}).get('name', '')
        result.append(MatchOut(
            fixture_id=fx['fixture']['id'],
            competition=ALLOWED_LEAGUES.get(league_name, league_name),
            date=fx['fixture']['date'],
            status=fx['fixture']['status']['short'],
            home_team=fx['teams']['home']['name'],
            away_team=fx['teams']['away']['name'],
        ))
    return result


@router.get('/top-picks-today', response_model=PicksResponse)
async def top_picks_today() -> PicksResponse:
    try:
        fixtures = await service.fixtures_by_date(today_str())
    except Exception as e:
        raise HTTPException(status_code=502, detail=f'Error consultando API-Football: {e}')

    picks: List[PickOut] = []

    for fx in fixtures:
        # Analiza solo partidos no iniciados
        status = fx.get('fixture', {}).get('status', {}).get('short')
        if status not in {'NS', 'TBD', 'PST'}:
            continue

        league = fx.get('league', {})
        fixture = fx.get('fixture', {})
        teams = fx.get('teams', {})
        home_team = teams.get('home', {})
        away_team = teams.get('away', {})

        league_id = league.get('id')
        season = league.get('season')
        home_id = home_team.get('id')
        away_id = away_team.get('id')
        if not all([league_id, season, home_id, away_id]):
            continue

        standings_map = await service.standings(league_id, season)
        home_recent = await service.recent_team_form(home_id, league_id, season, None, 5)
        away_recent = await service.recent_team_form(away_id, league_id, season, None, 5)
        home_venue_recent = await service.recent_team_form(home_id, league_id, season, 'home', 5)
        away_venue_recent = await service.recent_team_form(away_id, league_id, season, 'away', 5)

        if len(home_recent) == 0 or len(away_recent) == 0:
            continue

        home_stats = extract_team_recent_stats(home_id, home_team['name'], home_recent, home_venue_recent, standings_map.get(home_id))
        away_stats = extract_team_recent_stats(away_id, away_team['name'], away_recent, away_venue_recent, standings_map.get(away_id))

        winner_market, winner_prob, winner_expl, winner_team = market_winner(home_stats, away_stats)
        over_market, over_prob, over_expl = market_over25(home_stats, away_stats)
        btts_market, btts_prob, btts_expl = market_btts(home_stats, away_stats)

        candidate_rows = [
            (winner_market, winner_prob, winner_expl, winner_team),
            (over_market, over_prob, over_expl, None),
            (btts_market, btts_prob, btts_expl, None),
        ]
        best_market, best_prob, best_expl, best_team = max(candidate_rows, key=lambda x: x[1])
        verdict, color = classify(best_prob)
        if best_prob < 62:
            continue

        league_name = league.get('name', '')
        picks.append(PickOut(
            fixture_id=fixture['id'],
            competition=ALLOWED_LEAGUES.get(league_name, league_name),
            match=f"{home_team['name']} vs {away_team['name']}",
            market=best_market,
            probability=best_prob,
            verdict=verdict,
            color=color,
            explanation=best_expl,
            starts_at=fixture['date'],
            team=best_team,
        ))

    picks.sort(key=lambda p: p.probability, reverse=True)
    return PicksResponse(date=today_str(), picks=picks[:3])
