<div align="center">

# 📚 AI Quiz Maker

### Assistant IA pour la création et l'évaluation de formations

Transformez n'importe quel support de cours PDF en quiz interactif, corrigé automatiquement par IA, avec analyse des points faibles et parcours de révision personnalisé.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#licence)

</div>

---

## 🎯 À propos

**AI Quiz Maker** analyse un support de cours au format PDF, puis génère
automatiquement un quiz adapté (QCM, questions ouvertes, exercices
pratiques). Les réponses de l'apprenant sont corrigées par IA, avec une
analyse de performance par thème et un parcours de révision personnalisé.

## ✨ Fonctionnalités

- 📄 Import multi-documents (PDF), avec suppression individuelle
- 🧠 Résumé automatique du contenu
- 🎲 Génération de quiz mixtes : QCM, questions ouvertes, exercices — nombre de questions et difficulté réglables
- ✅ Correction automatique, y compris pour les réponses rédigées (score + feedback)
- 📊 Analyse par thème : compétences maîtrisées vs. à revoir
- 🧭 Parcours de révision personnalisé généré par IA
- 📑 Rapport PDF pour le formateur

## 🛠️ Stack technique

Python · Streamlit · LangChain · Google Gemini · FAISS · PyPDF2 · ReportLab

## 🏗️ Architecture

```
PDF
 → Extraction du texte
 → Découpage en chunks
 → Indexation vectorielle (FAISS)
 → Génération du quiz par IA
 → Correction des réponses
 → Analyse des points faibles + parcours de révision
 → Rapport PDF
```

## 📂 Structure du projet

```
ai_quiz_maker/
├── app.py              # Interface Streamlit
├── ai_engine.py         # LLM, RAG, génération du quiz, correction
├── pdf_utils.py          # Extraction PDF + rapport PDF
├── ui_styles.py          # Design (CSS, composants d'interface)
├── results_store.py      # Historique des résultats (JSON)
├── config.py             # Configuration centrale
├── requirements.txt
└── .env.example
```

## 🚀 Installation (macOS)

```bash
git clone https://github.com/<votre-utilisateur>/<nom-du-repo>.git
cd <nom-du-repo>

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
open -e .env          # renseignez votre clé API Google Gemini

python3 -m streamlit run app.py
```

L'application s'ouvre sur `http://localhost:8501`.

## 📌 Utilisation

1. Importer un ou plusieurs PDF de formation.
2. Configurer le quiz (nombre de questions, types, difficulté).
3. Répondre aux questions générées.
4. Consulter le score, les points faibles et le parcours de révision.
5. Télécharger le rapport PDF pour le formateur.

## 📄 Licence

Distribué sous licence MIT — voir [`LICENSE`](LICENSE).
