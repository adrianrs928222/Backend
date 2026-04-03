from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class TeamRecentStats:
    team_id: int
    name: str
    points_last5: int
    goals_for_last5: int
    goals_against_last5: int
    scored_matches_last5: int
    conceded_matches_last5: int
    over25_matches_last5: int
    btts_matches_last5: int
    venue_points_last5: int
    table_rank: Optional[int]
    streak_points_last3: int


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def points_from_result(is_home: bool, fixture: Dict) -> int:
    goals_home = fixture.get('goals', {}).get('home')
    goals_away = fixture.get('goals', {}).get('away')
    if goals_home is None or goals_away is None:
        return 0
    if goals_home == goals_away:
        return 1
    if is_home and goals_home > goals_away:
        return 3
    if not is_home and goals_away > goals_home:
        return 3
    return 0


def extract_team_recent_stats(team_id: int, team_name: str, fixtures_all: List[Dict], fixtures_venue: List[Dict], table_rank: Optional[int]) -> TeamRecentStats:
    points_last5 = 0
    goals_for_last5 = 0
    goals_against_last5 = 0
    scored_matches_last5 = 0
    conceded_matches_last5 = 0
    over25_matches_last5 = 0
    btts_matches_last5 = 0
    streak_points_last3 = 0

    for idx, fx in enumerate(fixtures_all[:5]):
        home_id = fx.get('teams', {}).get('home', {}).get('id')
        away_id = fx.get('teams', {}).get('away', {}).get('id')
        gh = fx.get('goals', {}).get('home', 0) or 0
        ga = fx.get('goals', {}).get('away', 0) or 0
        is_home = home_id == team_id
        gf = gh if is_home else ga
        gc = ga if is_home else gh
        goals_for_last5 += gf
        goals_against_last5 += gc
        points = points_from_result(is_home, fx)
        points_last5 += points
        if idx < 3:
            streak_points_last3 += points
        if gf > 0:
            scored_matches_last5 += 1
        if gc > 0:
            conceded_matches_last5 += 1
        if (gh + ga) > 2:
            over25_matches_last5 += 1
        if gh > 0 and ga > 0:
            btts_matches_last5 += 1

    venue_points_last5 = 0
    for fx in fixtures_venue[:5]:
        home_id = fx.get('teams', {}).get('home', {}).get('id')
        is_home = home_id == team_id
        venue_points_last5 += points_from_result(is_home, fx)

    return TeamRecentStats(
        team_id=team_id,
        name=team_name,
        points_last5=points_last5,
        goals_for_last5=goals_for_last5,
        goals_against_last5=goals_against_last5,
        scored_matches_last5=scored_matches_last5,
        conceded_matches_last5=conceded_matches_last5,
        over25_matches_last5=over25_matches_last5,
        btts_matches_last5=btts_matches_last5,
        venue_points_last5=venue_points_last5,
        table_rank=table_rank,
        streak_points_last3=streak_points_last3,
    )


def rank_to_score(rank: Optional[int], default_teams: int = 22) -> float:
    if rank is None:
        return 50.0
    return clamp(((default_teams - rank + 1) / default_teams) * 100.0)


def winner_strength(stats: TeamRecentStats) -> float:
    form_score = (stats.points_last5 / 15.0) * 100.0
    venue_score = (stats.venue_points_last5 / 15.0) * 100.0
    attack_score = clamp((stats.goals_for_last5 / 10.0) * 100.0)
    defense_score = clamp(100.0 - ((stats.goals_against_last5 / 10.0) * 100.0))
    table_score = rank_to_score(stats.table_rank)
    streak_score = (stats.streak_points_last3 / 9.0) * 100.0
    return (
        0.30 * form_score +
        0.20 * venue_score +
        0.15 * attack_score +
        0.15 * defense_score +
        0.10 * table_score +
        0.10 * streak_score
    )


def market_winner(home: TeamRecentStats, away: TeamRecentStats) -> Tuple[str, int, str, Optional[str]]:
    hs = winner_strength(home)
    aws = winner_strength(away)
    total = max(hs + aws, 1)
    if hs >= aws:
        prob = int(round((hs / total) * 100))
        team = home.name
    else:
        prob = int(round((aws / total) * 100))
        team = away.name
    explanation = (
        f"{team} llega con mejor forma reciente, mejor rendimiento en su contexto de local/visitante "
        f"y mejores números ofensivos/defensivos que su rival."
    )
    return f'Ganador {team}', prob, explanation, team


def market_over25(home: TeamRecentStats, away: TeamRecentStats) -> Tuple[str, int, str]:
    avg_total_goals = (home.goals_for_last5 + home.goals_against_last5 + away.goals_for_last5 + away.goals_against_last5) / 10.0
    goals_score = clamp((avg_total_goals / 3.0) * 100.0)
    over_rate_score = clamp((((home.over25_matches_last5 / 5.0) + (away.over25_matches_last5 / 5.0)) / 2.0) * 100.0)
    attack_score = clamp((((home.goals_for_last5 / 10.0) * 100.0) + ((away.goals_for_last5 / 10.0) * 100.0)) / 2.0)
    defense_fragility = clamp((((home.goals_against_last5 / 10.0) * 100.0) + ((away.goals_against_last5 / 10.0) * 100.0)) / 2.0)
    score = int(round(
        0.30 * goals_score +
        0.30 * over_rate_score +
        0.20 * attack_score +
        0.20 * defense_fragility
    ))
    explanation = (
        'Ambos equipos vienen dejando partidos relativamente abiertos, con tendencia reciente a marcadores altos '
        'y defensas que conceden con frecuencia.'
    )
    return 'Más de 2.5 goles', score, explanation


def market_btts(home: TeamRecentStats, away: TeamRecentStats) -> Tuple[str, int, str]:
    local_scores = (home.scored_matches_last5 / 5.0) * 100.0
    visitor_scores = (away.scored_matches_last5 / 5.0) * 100.0
    local_concedes = (home.conceded_matches_last5 / 5.0) * 100.0
    visitor_concedes = (away.conceded_matches_last5 / 5.0) * 100.0
    score = int(round(0.25 * local_scores + 0.25 * visitor_scores + 0.25 * local_concedes + 0.25 * visitor_concedes))
    explanation = (
        'Ambos equipos marcan con frecuencia y también suelen conceder, lo que eleva la probabilidad de que '
        'los dos vean portería.'
    )
    return 'Ambos marcan', score, explanation


def classify(probability: int) -> Tuple[str, str]:
    verdict = 'Sí' if probability >= 62 else 'No'
    if probability >= 70:
        color = 'verde'
    elif probability >= 62:
        color = 'amarillo'
    else:
        color = 'rojo'
    return verdict, color
