"""
Configuration centrale de l'application AI Quiz Maker.
Assistant IA pour la création et l'évaluation de formations.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Clés API & environnement
# ============================================================

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ============================================================
# Chemins
# ============================================================

FAISS_INDEX_PATH = "faiss_index"
RESULTS_DIR = "results"
RESULTS_JSON_PATH = os.path.join(RESULTS_DIR, "quiz_results.json")
REPORTS_DIR = "reports"

# ============================================================
# Modèles IA
# ============================================================

EMBEDDING_MODEL = "models/gemini-embedding-2"
LLM_MODEL = "gemini-3.6-flash"  # IMPORTANT : ne pas définir de temperature avec ce modèle

# ============================================================
# Paramètres RAG
# ============================================================

CHUNK_SIZE = 8000
CHUNK_OVERLAP = 2000
RETRIEVAL_K = 20
MAX_CONTEXT_DOCS = 15
SUMMARY_MAX_CHARS = 12000

# ============================================================
# Paramètres quiz
# ============================================================

QUESTION_TYPES = {
    "qcm": "Questions à choix multiples",
    "open": "Questions ouvertes",
    "exercise": "Exercices pratiques",
}

WEAK_POINT_THRESHOLD = 0.6  # en dessous de 60% de réussite -> point faible
CORRECT_THRESHOLD_OPEN = 60  # score IA (0-100) à partir duquel une réponse ouverte est jugée correcte

DEFAULT_TOTAL_QUESTIONS = 5
QUESTION_COUNT_OPTIONS = [5, 10, 15, 20]

DIFFICULTY_LEVELS = {
    "easy": "Facile",
    "medium": "Moyen",
    "hard": "Difficile",
}
DEFAULT_DIFFICULTY = "medium"

APP_TITLE = "AI Quiz Maker"
APP_ICON = "📚"
