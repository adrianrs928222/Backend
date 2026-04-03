from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings


ALLOWED_LEAGUES = {
    'La Liga': 'LaLiga',
    'Segunda División': 'Segunda División',
    'UEFA Champions League': 'Champions League',
    'World Cup': 'Mundial',
    'FIFA World Cup': 'Mundial',
}


class ApiFootballService:
    def __init__(self) -> None:
        self.base_url = settings.apisports_base_url.rstrip('/')
        self.headers = {
            'x-apisports-key': settings.apisports_api_key,
        }

    async def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f'{self.base_url}/{path.lstrip("/")}'
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(url, headers=self.headers, params=params)
            resp.raise_for_status()
            return resp.json()

    async def fixtures_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        data = await self._get('fixtures', {'date': date_str, 'timezone': settings.tz})
        items = data.get('response', [])
        filtered = []
        for item in items:
            league_name = item.get('league', {}).get('name', '')
            if league_name in ALLOWED_LEAGUES:
                filtered.append(item)
        return filtered

    async def standings(self, league_id: int, season: int) -> Dict[str, int]:
        """Devuelve mapping team_id -> rank. Si no hay standings, devuelve vacío."""
        try:
            data = await self._get('standings', {'league': league_id, 'season': season})
            response = data.get('response', [])
            table_map: Dict[int, int] = {}
            for league_block in response:
                for standing_group in league_block.get('league', {}).get('standings', []):
                    for row in standing_group:
                        team_id = row.get('team', {}).get('id')
                        rank = row.get('rank')
                        if team_id and rank:
                            table_map[team_id] = rank
            return table_map
        except Exception:
            return {}

    async def recent_team_form(self, team_id: int, league_id: int, season: int, venue: Optional[str] = None, last: int = 5) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            'team': team_id,
            'league': league_id,
            'season': season,
            'last': last,
            'timezone': settings.tz,
        }
        if venue:
            params['venue'] = venue
        data = await self._get('fixtures', params)
        return data.get('response', [])
