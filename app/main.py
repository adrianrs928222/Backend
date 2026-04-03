from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Top 3 Picks Backend",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Backend funcionando"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/top-picks-today")
def top_picks_today():
    return {
        "date": "2026-04-03",
        "picks": [
            {
                "competition": "LaLiga",
                "match": "Real Madrid vs Sevilla",
                "market": "Ganador Real Madrid",
                "probability": 74,
                "verdict": "Sí",
                "color": "verde",
                "explanation": "El local llega en mejor forma reciente y con mejores números ofensivos y defensivos."
            },
            {
                "competition": "Champions League",
                "match": "PSG vs Bayern",
                "market": "Más de 2.5 goles",
                "probability": 68,
                "verdict": "Sí",
                "color": "amarillo",
                "explanation": "Ambos equipos vienen generando ocasiones y tienen tendencia a partidos abiertos."
            },
            {
                "competition": "Segunda División",
                "match": "Eibar vs Oviedo",
                "market": "Ambos marcan",
                "probability": 65,
                "verdict": "Sí",
                "color": "amarillo",
                "explanation": "Los dos equipos llegan con tendencia ofensiva positiva y conceden con frecuencia."
            }
        ]
    }