"""
Sauvegarde des résultats de quiz au format JSON.

Conformément au cahier des charges : aucune base de données n'est requise
pour le prototype, les résultats sont persistés dans un fichier JSON.
"""

import os
import json
from datetime import datetime

import config


def save_result(learner_name, document_names, score_summary, category_breakdown, weak_points):
    """Ajoute une nouvelle entrée de résultat dans le fichier JSON des résultats."""

    os.makedirs(config.RESULTS_DIR, exist_ok=True)

    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "learner_name": learner_name or "Anonyme",
        "documents": document_names,
        "score": score_summary,
        "category_breakdown": category_breakdown,
        "weak_points": weak_points,
    }

    history = load_results()
    history.append(entry)

    with open(config.RESULTS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return entry


def load_results():
    """Charge l'historique des résultats depuis le fichier JSON."""

    if not os.path.exists(config.RESULTS_JSON_PATH):
        return []

    try:
        with open(config.RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []
