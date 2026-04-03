# Top 3 Picks Backend (FastAPI)

Backend para tu app Android de pronósticos sin IA real, usando datos reales de API-Football.

## Qué hace
- Lee partidos del día desde API-Football
- Filtra solo competiciones permitidas:
  - LaLiga
  - Segunda División
  - UEFA Champions League
  - FIFA World Cup
- Calcula 3 mercados por partido:
  - ganador
  - +2.5 goles
  - ambos marcan
- Se queda con el mejor mercado de cada partido
- Devuelve los 3 picks más fuertes del día

## Importante
No metas tu API key dentro de la app Android. Ponla solo en el backend.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Rellena `.env` con tu clave nueva de API-Sports.

## Ejecutar
```bash
uvicorn app.main:app --reload
```

## Endpoints
- `GET /health`
- `GET /matches-today`
- `GET /top-picks-today`

## Cómo conectar Android Studio
Haz que la app consuma:
- `GET http://TU_BACKEND/top-picks-today`

Y usa el JSON que devuelve para pintar las tarjetas.

## Notas sobre el algoritmo
Es un sistema sin IA entrenada. Usa scoring con estadísticas recientes:
- forma
- goles a favor / en contra
- BTTS reciente
- over 2.5 reciente
- posición en tabla
- rendimiento casa / fuera

## Siguientes mejoras
- caché diaria
- guardar histórico
- tareas programadas
- panel admin
- explicaciones más detalladas
