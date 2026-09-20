# SERGIO 2026-09-20: configuracion base del proyecto (feature/esqueleto-app)
from pathlib import Path

BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
DATA_DIR = BASE_DIR / "data"

# Un quiz de 5 preguntas se aprueba solo si las 5 estan correctas
QUIZ_APROBACION_TOTAL = True
