<div align="center">

#  AI Quiz Maker

### Assistant IA pour la création et l'évaluation de formations

Transformez n'importe quel support de cours PDF en quiz interactif, corrigé automatiquement par IA, avec analyse des points faibles et parcours de révision personnalisé.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#licence)

</div>

---

## 📖 Sommaire

- [À propos](#-à-propos)
- [Fonctionnalités](#-fonctionnalités)
- [Stack technique](#-stack-technique)
- [Architecture](#-architecture)
- [Structure du projet](#-structure-du-projet)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Licence](#-licence)

---

## 🎯 À propos

**FormaQuiz** analyse un support de cours au format PDF, en extrait le
contenu, puis génère automatiquement un quiz adapté (QCM, questions
ouvertes, exercices pratiques). Les réponses de l'apprenant — y compris les
réponses rédigées — sont corrigées par un LLM, qui produit ensuite une
analyse de performance par thème et un parcours de révision personnalisé.
Un rapport PDF récapitulatif peut être généré pour le formateur.

Projet réalisé dans le cadre d'un PFE, conformément au cahier des charges
*« Assistant IA pour la création et l'évaluation de formations »*.

## ✨ Fonctionnalités

- 📄 **Import multi-documents** — un ou plusieurs PDF, avec suppression individuelle possible.
- 🧠 **Résumé automatique** du contenu du document.
- 🔍 **Indexation sémantique (RAG)** du document via FAISS.
- 🎲 **Génération de quiz mixtes** — QCM, questions ouvertes, exercices pratiques, avec choix du nombre de questions et du niveau de difficulté.
- ✅ **Correction automatique** — instantanée pour les QCM, évaluée par le LLM pour les réponses ouvertes (score + feedback détaillé).
- 📊 **Analyse par thème** — score global, taux de réussite, compétences maîtrisées vs. à revoir.
- 🧭 **Parcours de révision personnalisé**, généré par IA à partir des points faibles identifiés.
- 📑 **Rapport PDF pour le formateur** — score, thèmes, points faibles, recommandations, détail des réponses.
- 🗂️ **Historique des résultats** persisté en JSON (aucune base de données requise).

## 🛠️ Stack technique

| Catégorie | Technologie |
|---|---|
| Interface | [Streamlit](https://streamlit.io/) |
| Orchestration LLM / RAG | [LangChain](https://www.langchain.com/) |
| Modèle de langage & embeddings | [Google Gemini](https://ai.google.dev/) |
| Index vectoriel | [FAISS](https://github.com/facebookresearch/faiss) |
| Extraction PDF | [PyPDF2](https://pypdf2.readthedocs.io/) |
| Génération de rapport PDF | [ReportLab](https://www.reportlab.com/) |
| Langage | Python 3.10+ |

## 🏗️ Architecture

```
PDF → Extraction du texte → Résumé (LLM) → Indexation RAG (FAISS)
    → Génération du quiz (QCM / questions ouvertes / exercices)
    → Réponses de l'apprenant
    → Correction (instantanée QCM / LLM pour réponses ouvertes)
    → Score + analyse par thème → Points faibles
    → Recommandations personnalisées (LLM)
    → Rapport PDF pour le formateur + historique JSON
```

## 📂 Structure du projet

```
ai_quiz_maker/
├── app.py              # Interface Streamlit (orchestration des écrans)
├── ai_engine.py         # Embeddings, LLM, RAG, génération du quiz, correction, recommandations
├── pdf_utils.py          # Extraction PDF + génération du rapport PDF formateur
├── ui_styles.py          # Système de design (CSS, icônes, composants d'interface)
├── results_store.py      # Persistance des résultats au format JSON
├── config.py             # Configuration centrale (modèles, chemins, seuils)
├── assets/                # Logo de l'application
├── requirements.txt
├── .env.example
├── results/               # Historique des résultats (généré à l'usage)
└── reports/                # Rapports PDF générés (générés à l'usage)
```

## 🚀 Installation

### Prérequis

- Python 3.10 ou supérieur
- Une clé API Google Generative AI (Gemini) — [console Google AI Studio](https://aistudio.google.com/)

### Étapes (macOS)

```bash
# Cloner le dépôt
git clone https://github.com/<votre-utilisateur>/<nom-du-repo>.git
cd <nom-du-repo>

# Créer et activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier d'environnement
cp .env.example .env

# Renseigner votre clé API
open -e .env

# Lancer l'application
python3 -m streamlit run app.py
```

L'application s'ouvre automatiquement dans le navigateur à l'adresse
`http://localhost:8501`.

> Pour relancer l'application plus tard, réactivez simplement
> l'environnement virtuel (`source venv/bin/activate`) puis exécutez
> `python3 -m streamlit run app.py`.

## ⚙️ Configuration

Renseignez votre clé API dans le fichier `.env` :

```
GOOGLE_API_KEY=votre_clé_api_google
```

Les principaux paramètres applicatifs sont centralisés dans `config.py` :

| Paramètre | Rôle |
|---|---|
| `EMBEDDING_MODEL`, `LLM_MODEL` | Modèles Google Generative AI utilisés |
| `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_K` | Paramètres du découpage et de la recherche RAG |
| `QUESTION_COUNT_OPTIONS`, `DIFFICULTY_LEVELS` | Options proposées pour la génération du quiz |
| `WEAK_POINT_THRESHOLD` | Seuil (60 % par défaut) sous lequel un thème est considéré comme point faible |

## 📌 Utilisation

1. Importer un ou plusieurs PDF de formation depuis l'écran d'accueil.
2. Consulter le résumé automatique généré.
3. Choisir le nombre de questions, les types à inclure et le niveau de difficulté.
4. Générer puis répondre au quiz, question par question.
5. Consulter le score, les points faibles identifiés et le parcours de révision personnalisé.
6. Générer et télécharger le rapport PDF destiné au formateur.

## 📄 Licence

Ce projet est distribué sous licence MIT — voir le fichier `LICENSE` pour plus de détails.

---

<div align="center">
Réalisé dans le cadre d'un Projet de Fin d'Études (PFE)
</div>
