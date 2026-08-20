"""
Moteur IA de l'application :

- Embeddings & LLM (Google Generative AI)
- Indexation RAG (FAISS)
- Résumé automatique du document
- Génération de quiz mixtes (QCM / questions ouvertes / exercices)
- Correction automatique (QCM instantanée, réponses ouvertes via LLM)
- Identification des points faibles de l'apprenant
- Génération de recommandations personnalisées
"""

import os
import json
import random
import shutil
import time
from datetime import datetime, timedelta

import streamlit as st
from pydantic import SecretStr

from langchain_core.prompts.prompt import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config


# ============================================================
# Gestion du quota API
# ============================================================

# Cache pour suivre les requêtes
_request_timestamps = []
_last_rate_limit_warning = None

def check_rate_limit():
    """Vérifie et gère le rate limiting avec une marge de sécurité."""
    global _request_timestamps, _last_rate_limit_warning
    
    # Nettoyer les timestamps de plus de 24h
    now = datetime.now()
    _request_timestamps = [t for t in _request_timestamps if (now - t).total_seconds() < 86400]
    
    # Limite de 18 requêtes (garder 2 requêtes de marge sur 20)
    if len(_request_timestamps) >= 18:
        oldest = _request_timestamps[0]
        wait_seconds = 86400 - (now - oldest).total_seconds()
        if wait_seconds > 0:
            if not _last_rate_limit_warning or (now - _last_rate_limit_warning).total_seconds() > 60:
                _last_rate_limit_warning = now
                st.warning(f"⚠️ Quota quotidien presque atteint. Plus que {20 - len(_request_timestamps)} requêtes disponibles.")
            return False
    
    _request_timestamps.append(now)
    return True

def call_with_retry(func, max_retries=3, initial_delay=5):
    """Appelle une fonction avec retry sur erreur de quota."""
    for attempt in range(max_retries):
        try:
            if not check_rate_limit():
                # Si quota atteint, retourner None pour utiliser le fallback
                return None
            return func()
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                delay = initial_delay * (2 ** attempt)
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Quota API dépassé. Nouvelle tentative dans {delay}s...")
                    time.sleep(delay)
                    continue
                else:
                    st.error("❌ Quota API dépassé. Veuillez réessayer plus tard.")
                    return None
            else:
                raise e
    return None


# ============================================================
# Mode dégradé (fallback sans API)
# ============================================================

def generate_quiz_fallback(text_chunks, num_questions=5, question_types=None):
    """Génère un quiz simple sans utiliser l'API (mode dégradé)."""
    question_types = question_types or ["qcm"]
    
    # Extraire quelques phrases du texte pour créer des questions
    sample_text = ""
    if text_chunks:
        sample_text = " ".join(text_chunks[:3])[:1000]
    
    # Si pas de texte, utiliser des questions génériques
    if not sample_text:
        sample_text = "Document de formation sur les concepts clés."
    
    questions = []
    categories = ["Concepts fondamentaux", "Applications pratiques", "Analyse", "Synthèse", "Évaluation"]
    
    # Générer des questions basées sur le texte disponible
    for i in range(min(num_questions, 5)):
        # Extraire des mots clés du texte pour créer des questions
        words = sample_text.split()[:20]
        topic = " ".join(words[i*2:(i*2)+3]) if len(words) > i*2+2 else "concept"
        
        if "qcm" in question_types and i % 2 == 0:
            question = {
                "type": "qcm",
                "question": f"Question {i+1} : Quel est l'élément clé abordé dans le document concernant '{topic}' ?",
                "options": [
                    "Option A : Comprendre les bases",
                    "Option B : Appliquer les concepts",
                    "Option C : Analyser les données",
                    "Option D : Synthétiser les informations"
                ],
                "correct_option": "Option A : Comprendre les bases",
                "category": categories[i % len(categories)],
                "expected_answer": ""
            }
        else:
            question = {
                "type": "open",
                "question": f"Question {i+1} : En vous basant sur le document, expliquez ce que vous avez compris à propos de '{topic}'.",
                "options": [],
                "correct_option": "",
                "category": categories[i % len(categories)],
                "expected_answer": "Une réponse complète qui démontre une bonne compréhension du sujet abordé."
            }
        questions.append(question)
    
    return questions


def generate_summary_fallback(text):
    """Génère un résumé simple sans utiliser l'API."""
    words = text.split()[:200]
    if len(words) < 20:
        return "Le document ne contient pas assez de texte pour générer un résumé automatique."
    
    # Extraire les phrases les plus importantes
    sentences = text.split('.')
    important_sentences = [s for s in sentences if len(s.split()) > 10][:5]
    
    if important_sentences:
        summary = "Résumé du document :\n\n"
        summary += " - " + "\n - ".join(important_sentences[:4])
        summary += "\n\nCe résumé a été généré automatiquement en mode dégradé."
        return summary
    else:
        return "Le document a été importé avec succès. Le résumé automatique n'est pas disponible en mode dégradé."


# ============================================================
# Modèles Google AI
# ============================================================

@st.cache_resource
def get_embeddings():
    """Retourne une instance mise en cache des embeddings Google Generative AI."""

    if not config.GOOGLE_API_KEY:
        raise ValueError("La variable d'environnement GOOGLE_API_KEY n'est pas définie.")

    return GoogleGenerativeAIEmbeddings(
        model=config.EMBEDDING_MODEL,
        google_api_key=SecretStr(config.GOOGLE_API_KEY),
    )


@st.cache_resource
def get_llm():
    """Retourne une instance mise en cache du LLM Gemini."""

    if not config.GOOGLE_API_KEY:
        raise ValueError("La variable d'environnement GOOGLE_API_KEY n'est pas définie.")

    return ChatGoogleGenerativeAI(
        model=config.LLM_MODEL,
        google_api_key=SecretStr(config.GOOGLE_API_KEY),
    )


# ============================================================
# Découpage du texte
# ============================================================

@st.cache_data(show_spinner=False)
def get_text_chunks(text):
    """Découpe le texte extrait en segments pour l'indexation FAISS."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    return splitter.split_text(text)


# ============================================================
# FAISS (RAG)
# ============================================================

def create_and_save_vector_store(text_chunks):
    """Crée et sauvegarde l'index vectoriel FAISS à partir des segments de texte."""

    if os.path.exists(config.FAISS_INDEX_PATH):
        shutil.rmtree(config.FAISS_INDEX_PATH)

    embeddings = get_embeddings()

    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local(config.FAISS_INDEX_PATH)


@st.cache_resource
def load_vector_store():
    """Charge l'index vectoriel FAISS depuis le disque, s'il existe."""

    if not os.path.exists(config.FAISS_INDEX_PATH):
        return None

    return FAISS.load_local(
        config.FAISS_INDEX_PATH,
        get_embeddings(),
        allow_dangerous_deserialization=True,
    )


# ============================================================
# Utilitaires de réponse Gemini
# ============================================================

def extract_response_text(response):
    """Convertit le contenu de la réponse LangChain/Gemini en texte brut."""

    content = response.content

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("text"):
                parts.append(str(item["text"]))

        return "\n".join(parts).strip()

    return str(content).strip()


def clean_json_response(text):
    """Nettoie une réponse JSON potentiellement encadrée par des balises Markdown."""

    text = text.strip()

    if text.startswith("```json"):
        text = text[len("```json"):].strip()
    elif text.startswith("```"):
        text = text[len("```"):].strip()

    if text.endswith("```"):
        text = text[:-3].strip()

    return text.strip()


def _safe_llm_json_call(prompt_template, input_vars, fallback=None):
    """Appelle le LLM via une chaîne LangChain et tente de parser un JSON en sortie."""

    try:
        # Vérifier le quota avant d'appeler
        if not check_rate_limit():
            st.warning("⚠️ Quota API atteint. Utilisation du mode dégradé.")
            return fallback, "Quota API atteint - mode dégradé activé"
        
        llm = get_llm()
        chain = prompt_template | llm
        response = chain.invoke(input_vars)
        text = extract_response_text(response)

        if not text:
            return fallback, "Le modèle a retourné une réponse vide."

        cleaned = clean_json_response(text)
        return json.loads(cleaned), None

    except json.JSONDecodeError as e:
        return fallback, f"Réponse JSON invalide du modèle : {e}"
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            return fallback, "Quota API dépassé. Veuillez réessayer plus tard."
        return fallback, f"Erreur de communication avec le modèle : {e}"


# ============================================================
# Résumé automatique du document
# ============================================================

def generate_summary(text, max_chars=config.SUMMARY_MAX_CHARS):
    """Génère un résumé structuré du document de formation pour le formateur/apprenant."""

    excerpt = text[:max_chars]
    
    # Vérifier si on a assez de texte pour un résumé
    if len(excerpt) < 100:
        return "Le document est trop court pour générer un résumé significatif."

    prompt = PromptTemplate(
        input_variables=["text"],
        template="""
Tu es un expert en ingénierie pédagogique. Résume le document de formation
suivant de façon claire et structurée.

Consignes :
1. Un résumé général en 4 à 6 phrases.
2. Une liste de 5 à 8 concepts clés abordés, chacun précédé d'un tiret "-".
3. Réponds uniquement en français.
4. N'invente aucune information absente du texte.
5. Ne retourne pas de JSON, du texte simple uniquement.

Document :
{text}
"""
    )

    try:
        # Essayer avec retry
        def call_summary():
            llm = get_llm()
            chain = prompt | llm
            response = chain.invoke({"text": excerpt})
            return extract_response_text(response)
        
        result = call_with_retry(call_summary)
        
        if result is None:
            # Mode dégradé si quota atteint
            st.warning("⚠️ Mode dégradé : résumé généré sans IA")
            return generate_summary_fallback(text)
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            st.warning("⚠️ Quota API dépassé. Résumé généré en mode dégradé.")
            return generate_summary_fallback(text)
        return f"Impossible de générer le résumé automatique : {e}"


# ============================================================
# Génération du quiz (QCM + questions ouvertes + exercices)
# ============================================================

RETRIEVAL_QUERIES = [
    "Génère des questions de quiz sur les concepts clés et les idées principales du document.",
    "Crée un quiz basé sur les détails importants et les informations factuelles présentées.",
    "Formule des questions qui testent la compréhension des sujets principaux du document.",
    "Quelles seraient de bonnes questions à choix multiples et questions ouvertes à partir de ce texte ?",
    "Génère un quiz qui couvre les informations essentielles du document, avec des exercices pratiques.",
]


def _retrieve_context(vector_db, k=config.RETRIEVAL_K):
    """Récupère un contexte pertinent depuis l'index FAISS."""

    retriever = vector_db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )

    query = random.choice(RETRIEVAL_QUERIES)
    docs = retriever.invoke(query)

    if not docs:
        return None

    if len(docs) > config.MAX_CONTEXT_DOCS:
        docs = random.sample(docs, config.MAX_CONTEXT_DOCS)

    context = "\n\n".join(d.page_content for d in docs if d.page_content)
    return context.strip() or None


def validate_quiz_data(quiz_data, num_questions):
    """Valide la structure du quiz généré par le modèle (QCM, questions ouvertes, exercices)."""

    if not isinstance(quiz_data, list):
        return False, "Le modèle n'a pas retourné une liste."

    if len(quiz_data) == 0:
        return False, "Le modèle a retourné un quiz vide."

    for i, q in enumerate(quiz_data):
        if not isinstance(q, dict):
            return False, f"La question {i + 1} n'est pas un objet valide."

        if "question" not in q or not isinstance(q["question"], str):
            return False, f"La question {i + 1} a un champ 'question' invalide."

        q_type = q.get("type", "qcm")

        if q_type not in ("qcm", "open", "exercise"):
            return False, f"La question {i + 1} a un type inconnu : {q_type}."

        q.setdefault("category", "Général")

        if q_type == "qcm":
            if not isinstance(q.get("options"), list) or len(q["options"]) != 4:
                return False, f"La question {i + 1} (QCM) doit avoir exactement 4 options."

            if q.get("correct_option") not in q["options"]:
                return False, f"La question {i + 1} : correct_option absent des options."
        else:
            if not isinstance(q.get("expected_answer"), str) or not q["expected_answer"].strip():
                return False, f"La question {i + 1} ({q_type}) doit avoir une 'expected_answer'."

    return True, None


def generate_quiz_from_faiss(vector_db, num_questions=5, question_types=None, difficulty="medium"):
    """
    Génère un quiz mixte (QCM / questions ouvertes / exercices) à partir
    du contexte récupéré dans l'index FAISS.
    """

    question_types = question_types or ["qcm"]
    difficulty_label = config.DIFFICULTY_LEVELS.get(difficulty, "Moyen")

    if vector_db is None:
        st.error("Base vectorielle introuvable. Veuillez d'abord importer un document PDF.")
        return []

    context = _retrieve_context(vector_db)

    if not context:
        st.error("Aucun contenu pertinent n'a pu être récupéré dans le document.")
        return []

    types_label = ", ".join(config.QUESTION_TYPES[t] for t in question_types)

    quiz_prompt = PromptTemplate(
        input_variables=["context", "num_questions", "types_label", "types_list", "difficulty_label"],
        template="""
Tu es un expert en ingénierie pédagogique et en création de quiz.

En utilisant UNIQUEMENT le contexte fourni, génère exactement {num_questions}
questions réparties entre les types suivants : {types_label}.
Types autorisés pour le champ "type" : {types_list}.
Niveau de difficulté demandé pour l'ensemble des questions : {difficulty_label}.

Règles :
1. Génère exactement {num_questions} questions au total, réparties de façon
   équilibrée entre les types autorisés.
2. Pour les questions de type "qcm" : exactement 4 options, une seule correcte,
   "correct_option" doit être copié EXACTEMENT depuis la liste "options".
3. Pour les questions de type "open" (question ouverte) ou "exercise"
   (exercice pratique appliquant une notion du document) : fournis un champ
   "expected_answer" qui sert de corrigé de référence (2 à 4 phrases),
   et laisse "options" à [] et "correct_option" à "".
4. Ajoute pour CHAQUE question un champ "category" : un thème court
   (2 à 4 mots) résumant le sujet de la question. Ce champ sera utilisé
   pour identifier les points faibles de l'apprenant.
5. Ne pas inventer d'informations absentes du contexte.
6. Varier les questions, les thèmes abordés et la position des bonnes réponses.
7. Adapte la complexité des questions et des énoncés au niveau "{difficulty_label}"
   (questions de restitution simples pour "Facile", raisonnement et mise en
   application pour "Moyen", analyse, synthèse ou cas complexes pour "Difficile").
8. Retourne UNIQUEMENT un JSON valide : pas de Markdown, pas de balises
   ```json, pas de texte avant ou après le JSON.

Format JSON attendu (exemple) :

[
  {{
    "type": "qcm",
    "category": "Nom du thème",
    "question": "Texte de la question ?",
    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
    "correct_option": "Option 2",
    "expected_answer": ""
  }},
  {{
    "type": "open",
    "category": "Nom du thème",
    "question": "Texte de la question ouverte ?",
    "options": [],
    "correct_option": "",
    "expected_answer": "Corrigé de référence attendu."
  }}
]

Contexte :

{context}
"""
    )

    # Essayer de générer le quiz avec retry
    def call_quiz_generation():
        return _safe_llm_json_call(
            quiz_prompt,
            {
                "context": context,
                "num_questions": num_questions,
                "types_label": types_label,
                "types_list": ", ".join(question_types),
                "difficulty_label": difficulty_label,
            },
            fallback=[],
        )
    
    result = call_with_retry(call_quiz_generation)
    
    # Si le résultat est None (quota atteint), utiliser le mode dégradé
    if result is None:
        st.warning("⚠️ Mode dégradé : quiz généré sans IA")
        return generate_quiz_fallback(None, num_questions, question_types)
    
    # Sinon, utiliser le résultat normal
    quiz_data, error = result

    if error:
        st.error(f"Erreur de génération du quiz : {error}")
        st.warning("⚠️ Utilisation du mode dégradé")
        return generate_quiz_fallback(None, num_questions, question_types)

    is_valid, validation_error = validate_quiz_data(quiz_data, num_questions)

    if not is_valid:
        st.warning(f"⚠️ Quiz invalide : {validation_error}. Utilisation du mode dégradé.")
        return generate_quiz_fallback(None, num_questions, question_types)

    random.shuffle(quiz_data)

    for q in quiz_data:
        if q.get("type") == "qcm":
            random.shuffle(q["options"])

    return quiz_data


# ============================================================
# Correction des réponses ouvertes / exercices
# ============================================================

def grade_open_answer(question, expected_answer, user_answer):
    """
    Fait évaluer une réponse ouverte / un exercice par le LLM.
    Retourne un dict {"score": 0-100, "is_correct": bool, "feedback": str}.
    """

    if not user_answer or not user_answer.strip():
        return {"score": 0, "is_correct": False, "feedback": "Aucune réponse fournie."}

    grading_prompt = PromptTemplate(
        input_variables=["question", "expected_answer", "user_answer", "threshold"],
        template="""
Tu es un correcteur pédagogique rigoureux mais bienveillant.

Question posée : {question}
Corrigé de référence : {expected_answer}
Réponse de l'apprenant : {user_answer}

Évalue la réponse de l'apprenant par rapport au corrigé de référence, en
tolérant les formulations différentes tant que le sens est correct.

Réponds UNIQUEMENT avec un JSON de la forme :

{{
  "score": 0-100,
  "is_correct": true/false,
  "feedback": "Feedback court et constructif en français (1 à 2 phrases)."
}}

"is_correct" doit être true si et seulement si le score est supérieur ou
égal à {threshold}. Ne retourne rien d'autre que ce JSON.
"""
    )

    def call_grading():
        return _safe_llm_json_call(
            grading_prompt,
            {
                "question": question,
                "expected_answer": expected_answer,
                "user_answer": user_answer,
                "threshold": config.CORRECT_THRESHOLD_OPEN,
            },
            fallback=None,
        )
    
    result = call_with_retry(call_grading)
    
    # Si le résultat est None (quota atteint), utiliser une correction simple
    if result is None:
        return {
            "score": 50 if len(user_answer.strip()) > 20 else 0,
            "is_correct": len(user_answer.strip()) > 20,
            "feedback": "Correction basique en mode dégradé. Relisez le corrigé pour vous assurer de votre compréhension."
        }
    
    result, error = result

    if error or not isinstance(result, dict):
        return {
            "score": 0,
            "is_correct": False,
            "feedback": "Correction automatique indisponible pour le moment.",
        }

    try:
        score = float(result.get("score", 0))
    except (TypeError, ValueError):
        score = 0

    is_correct = bool(result.get("is_correct", score >= config.CORRECT_THRESHOLD_OPEN))
    feedback = result.get("feedback", "")

    return {"score": score, "is_correct": is_correct, "feedback": feedback}


# ============================================================
# Analyse des points faibles
# ============================================================

def compute_category_breakdown(question_bank, user_results):
    """Calcule le taux de réussite par catégorie/thème à partir des résultats de l'apprenant."""

    breakdown = {}

    for idx, q in enumerate(question_bank):
        category = q.get("category", "Général")
        result = user_results[idx] if idx < len(user_results) else None

        stats = breakdown.setdefault(category, {"correct": 0, "total": 0, "percentage": 0.0})
        stats["total"] += 1

        if result and result.get("is_correct"):
            stats["correct"] += 1

    for stats in breakdown.values():
        stats["percentage"] = (stats["correct"] / stats["total"] * 100) if stats["total"] else 0.0

    return breakdown


def identify_weak_points(category_breakdown, threshold=config.WEAK_POINT_THRESHOLD):
    """Retourne la liste des thèmes dont le taux de réussite est sous le seuil défini."""

    weak = []

    for category, stats in category_breakdown.items():
        if stats["total"] > 0 and (stats["correct"] / stats["total"]) < threshold:
            weak.append(f"{category} ({stats['percentage']:.0f}% de réussite)")

    return weak


# ============================================================
# Recommandations personnalisées
# ============================================================

def generate_recommendations(weak_points, document_summary):
    """Génère un parcours de révision personnalisé basé sur les points faibles détectés."""

    if not weak_points:
        return (
            "Excellent travail ! Aucun point faible majeur n'a été détecté sur ce "
            "document. L'apprenant peut aborder des contenus plus avancés sur ce sujet "
            "ou passer au module suivant."
        )

    weak_points_text = "\n".join(f"- {wp}" for wp in weak_points)
    
    # Si le résumé est en mode dégradé ou indisponible, utiliser un message générique
    if not document_summary or document_summary.startswith("Le document ne contient pas") or document_summary.startswith("Impossible"):
        document_summary = "Document de formation sur les concepts abordés dans le quiz."

    prompt = PromptTemplate(
        input_variables=["weak_points", "summary"],
        template="""
Tu es un conseiller pédagogique. Un apprenant a passé un quiz basé sur un
document de formation dont voici le résumé :

{summary}

Voici les thèmes sur lesquels l'apprenant a montré des difficultés :
{weak_points}

Rédige un parcours de révision personnalisé en français, structuré ainsi :
1. Une phrase d'introduction encourageante.
2. Pour chaque point faible, une recommandation concrète (relire telle
   partie du document, refaire tel type d'exercice, approfondir tel concept).
3. Une conclusion avec un conseil de méthode de travail.

Réponds en texte brut uniquement (pas de Markdown, pas de JSON), en 150 à
250 mots.
"""
    )

    try:
        def call_recommendations():
            llm = get_llm()
            chain = prompt | llm
            response = chain.invoke({"weak_points": weak_points_text, "summary": document_summary})
            return extract_response_text(response)
        
        result = call_with_retry(call_recommendations)
        
        if result is None:
            # Mode dégradé
            return generate_recommendations_fallback(weak_points)
        
        return result
        
    except Exception as e:
        return generate_recommendations_fallback(weak_points)


def generate_recommendations_fallback(weak_points):
    """Génère des recommandations en mode dégradé."""
    recommendations = "📚 Parcours de révision personnalisé\n\n"
    recommendations += "Voici des recommandations pour renforcer vos compétences sur les points identifiés :\n\n"
    
    for wp in weak_points:
        recommendations += f"• {wp} : Relisez attentivement cette partie du document. "
        recommendations += "Prenez des notes et essayez de reformuler les concepts avec vos propres mots. "
        recommendations += "N'hésitez pas à rechercher des exemples supplémentaires pour mieux comprendre.\n\n"
    
    recommendations += "💡 Conseil de méthode : Travaillez régulièrement, même 15 minutes par jour, "
    recommendations += "plutôt que de longues sessions occasionnelles. La répétition espacée améliore la mémorisation."
    
    return recommendations