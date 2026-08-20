"""
AI Quiz Maker — Assistant IA pour la création et l'évaluation de formations.
"""

import io
import os
import shutil
import asyncio

import streamlit as st

import config
import ai_engine
import pdf_utils
import ui_styles
import results_store


# ============================================================
# Stored PDF
# ============================================================

class _StoredPDF(io.BytesIO):

    def __init__(self, name, data):
        super().__init__(data)
        self.name = name


# ============================================================
# Setup asyncio
# ============================================================

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


# ============================================================
# Initialisation du session state
# ============================================================

def init_session_state():

    defaults = {
        # Quiz
        "quiz_ongoing": False,
        "quiz_ended": True,
        "quiz_completed": False,

        # Résultats
        "score": 0,
        "question_number": 0,
        "question_bank": [],
        "user_results": [],

        # Documents
        "pdf_uploaded": False,
        "document_names": [],
        "document_files": [],
        "document_page_count": 0,
        "document_summary": "",
        "last_file_count": 0,

        # Configuration
        "total_questions": config.DEFAULT_TOTAL_QUESTIONS,
        "question_types": ["qcm", "open"],
        "difficulty": config.DEFAULT_DIFFICULTY,

        # Analyse
        "review_mode": False,
        "category_breakdown": {},
        "weak_points": [],
        "recommendations": "",

        # PDF / résultats
        "report_bytes": None,
        "result_saved": False,
        "show_results": False,

        # UI
        "balloons_showed": False,
        "learner_name": "",
    }

    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


# ============================================================
# RESET QUIZ
# ============================================================

def reset_quiz_state(full_reset=False):
    """
    Réinitialise le quiz.

    full_reset=True :
        supprime également le document.

    full_reset=False :
        conserve le document pour permettre de créer un nouveau quiz.
    """

    st.session_state.quiz_ongoing = False
    st.session_state.quiz_ended = True
    st.session_state.quiz_completed = False

    st.session_state.question_bank = []
    st.session_state.user_results = []
    st.session_state.question_number = 0
    st.session_state.score = 0

    st.session_state.review_mode = False
    st.session_state.category_breakdown = {}
    st.session_state.weak_points = []
    st.session_state.recommendations = ""

    st.session_state.report_bytes = None
    st.session_state.result_saved = False
    st.session_state.show_results = False

    st.session_state.balloons_showed = False

    if full_reset:
        st.session_state.pdf_uploaded = False
        st.session_state.document_names = []
        st.session_state.document_files = []
        st.session_state.document_page_count = 0
        st.session_state.document_summary = ""


# ============================================================
# STEPPER
# ============================================================

def current_step_index():
    """
    0 = Document
    1 = Quiz
    2 = Résultats & Révision
    """

    if not st.session_state.pdf_uploaded:
        return 0

    if not st.session_state.quiz_completed:
        return 1

    return 2


# ============================================================
# TRAITEMENT DES PDF
# ============================================================

def process_pdfs(pdf_docs, alerts_placeholder):

    alerts_placeholder.info(
        "Traitement des documents en cours..."
    )

    stored_files = []

    for f in pdf_docs:

        f.seek(0)

        stored_files.append(
            {
                "name": getattr(f, "name", "document.pdf"),
                "bytes": f.read(),
            }
        )

        f.seek(0)

    raw_text = pdf_utils.get_pdf_text(pdf_docs)

    if not raw_text.strip():

        alerts_placeholder.error(
            "Aucun texte lisible n'a été trouvé dans le(s) PDF."
        )

        return

    text_chunks = ai_engine.get_text_chunks(raw_text)

    if not text_chunks:

        alerts_placeholder.error(
            "Impossible de créer des segments de texte à partir du PDF."
        )

        return

    ai_engine.create_and_save_vector_store(text_chunks)

    with st.spinner(
        "Génération du résumé du document..."
    ):

        st.session_state.document_summary = (
            ai_engine.generate_summary(raw_text)
        )

    st.session_state.document_names = [
        getattr(f, "name", "document.pdf")
        for f in pdf_docs
    ]

    st.session_state.document_files = stored_files

    st.session_state.document_page_count = (
        pdf_utils.get_pdf_page_count(pdf_docs)
    )

    # Document terminé
    st.session_state.pdf_uploaded = True

    # Nouveau parcours → étape Quiz
    st.session_state.quiz_completed = False
    st.session_state.quiz_ongoing = False
    st.session_state.quiz_ended = True

    st.cache_resource.clear()

    alerts_placeholder.success(
        "Traitement terminé. Vous pouvez configurer votre quiz !"
    )


# ============================================================
# SUPPRESSION DOCUMENT
# ============================================================

def clear_document(alerts_placeholder=None):

    if os.path.exists(config.FAISS_INDEX_PATH):

        shutil.rmtree(
            config.FAISS_INDEX_PATH
        )

    reset_quiz_state(
        full_reset=True
    )

    st.session_state.last_file_count = 0

    st.cache_resource.clear()


def remove_document(idx):

    remaining = [
        f
        for i, f in enumerate(
            st.session_state.document_files
        )
        if i != idx
    ]

    if not remaining:

        clear_document()

        st.rerun()

        return

    stored_files = [
        _StoredPDF(
            f["name"],
            f["bytes"]
        )
        for f in remaining
    ]

    alerts_placeholder = st.empty()

    with st.spinner(
        "Mise à jour du document..."
    ):

        process_pdfs(
            stored_files,
            alerts_placeholder
        )

    reset_quiz_state(
        full_reset=False
    )

    st.session_state.last_file_count = len(
        remaining
    )

    st.session_state.pdf_uploaded = True
    st.session_state.quiz_completed = False

    st.rerun()


# ============================================================
# QUESTION
# ============================================================

def create_question(
    question_data: dict,
    idx: int
):

    score_increment = 0
    question_increment = 0
    quiz_end = False

    q_type = question_data.get(
        "type",
        "qcm"
    )

    total_questions = len(
        st.session_state.question_bank
    )

    container = st.container(
        border=True
    )

    with container:

        badges_html = (
            ui_styles.type_badge(q_type)
            +
            ui_styles.category_tag(
                question_data.get(
                    "category",
                    "General"
                )
            )
        )

        st.markdown(
            badges_html,
            unsafe_allow_html=True
        )

        ui_styles.render_question_number(
            idx + 1,
            total_questions
        )

        ui_styles.render_question_title(
            question_data["question"]
        )

        # ----------------------------------------------------
        # QCM
        # ----------------------------------------------------

        if q_type == "qcm":

            user_answer = st.radio(
                "Sélectionnez votre réponse :",
                question_data["options"],
                index=None,
                key=f"answer_{idx}",
            )

            answer_is_empty = (
                user_answer is None
            )

        # ----------------------------------------------------
        # Question ouverte
        # ----------------------------------------------------

        else:

            placeholder = (
                "Rédigez votre réponse ici..."
                if q_type == "open"
                else
                "Décrivez votre démarche / solution ici..."
            )

            user_answer = st.text_area(
                "Votre réponse :",
                key=f"answer_{idx}",
                height=130,
                placeholder=placeholder,
            )

            answer_is_empty = not (
                user_answer
                and
                user_answer.strip()
            )

        # ----------------------------------------------------
        # Boutons
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        # Validation
        with col1:

            if st.button(
                "Valider la réponse",
                key=f"submit_{idx}",
                disabled=answer_is_empty,
                type="primary",
            ):

                # QCM
                if q_type == "qcm":

                    is_correct = (
                        user_answer
                        ==
                        question_data[
                            "correct_option"
                        ]
                    )

                    result = {
                        "answer": user_answer,
                        "is_correct": is_correct,
                        "score": (
                            100
                            if is_correct
                            else 0
                        ),
                        "feedback": "",
                    }

                    if is_correct:

                        st.success(
                            "Correct !"
                        )

                    else:

                        st.error(
                            "Incorrect. "
                            f"Bonne réponse : "
                            f"**{question_data['correct_option']}**"
                        )

                # Question ouverte
                else:

                    with st.spinner(
                        "Correction par l'IA en cours..."
                    ):

                        grading = (
                            ai_engine.grade_open_answer(
                                question_data[
                                    "question"
                                ],
                                question_data.get(
                                    "expected_answer",
                                    ""
                                ),
                                user_answer,
                            )
                        )

                    result = {
                        "answer": user_answer,
                        **grading,
                    }

                    if grading["is_correct"]:

                        st.success(
                            "Bonne réponse ! "
                            +
                            grading["feedback"]
                        )

                    else:

                        st.warning(
                            f"{grading['feedback']}\n\n"
                            "**Corrigé de référence :** "
                            f"{question_data.get('expected_answer', '')}"
                        )

                st.session_state.user_results.append(
                    result
                )

                question_increment = 1

                score_increment = (
                    1
                    if result["is_correct"]
                    else 0
                )

        # Terminer
        with col2:

            if st.button(
                "Terminer le quiz",
                key=f"end_{idx}",
            ):

                quiz_end = True

                st.session_state.quiz_ended = True
                st.session_state.quiz_ongoing = False
                st.session_state.quiz_completed = True

    return (
        score_increment,
        question_increment,
        quiz_end,
    )


# ============================================================
# FINALISATION ANALYSE
# ============================================================

def finalize_quiz_analysis():

    if st.session_state.category_breakdown:
        return

    question_bank = (
        st.session_state.question_bank
    )

    user_results = (
        st.session_state.user_results
    )

    st.session_state.category_breakdown = (
        ai_engine.compute_category_breakdown(
            question_bank,
            user_results
        )
    )

    st.session_state.weak_points = (
        ai_engine.identify_weak_points(
            st.session_state.category_breakdown
        )
    )

    with st.spinner(
        "Analyse des résultats et génération des recommandations..."
    ):

        st.session_state.recommendations = (
            ai_engine.generate_recommendations(
                st.session_state.weak_points,
                st.session_state.document_summary,
            )
        )

    if not st.session_state.result_saved:

        score_summary = build_score_summary()

        results_store.save_result(
            st.session_state.learner_name,
            st.session_state.document_names,
            score_summary,
            st.session_state.category_breakdown,
            st.session_state.weak_points,
        )

        st.session_state.result_saved = True


# ============================================================
# SCORE
# ============================================================

def build_score_summary():

    question_bank = (
        st.session_state.question_bank
    )

    user_results = (
        st.session_state.user_results
    )

    max_score = len(
        question_bank
    )

    answered = len(
        user_results
    )

    score = sum(
        1
        for r in user_results
        if r.get("is_correct")
    )

    percentage = (
        score / max_score * 100
        if max_score
        else 0.0
    )

    return {
        "score": score,
        "max_score": max_score,
        "answered": answered,
        "total": max_score,
        "percentage": percentage,
    }


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():

    with st.sidebar:

        st.markdown(
            "#### AI Quiz Maker"
        )

        st.caption(
            "Assistant IA pour vos formations"
        )

        st.divider()

        # ----------------------------------------------------
        # DOCUMENTS
        # ----------------------------------------------------

        if st.session_state.pdf_uploaded:

            st.caption(
                "Documents actifs"
            )

            for idx, name in enumerate(
                st.session_state.document_names
            ):

                # Petite colonne pour le bouton
                col_name, col_del = st.columns(
                    [8, 1]
                )

                with col_name:

                    st.markdown(
                        f'<div class="sidebar-doc-name">{name}</div>',
                        unsafe_allow_html=True,
                    )

                with col_del:

                    # Bouton suppression compact
                    if st.button(
                        "×",
                        key=f"sidebar_del_{idx}",
                        help=f"Supprimer {name}",
                    ):

                        remove_document(idx)

        else:

            st.caption(
                "Aucun document importé"
            )

        st.divider()

        # ----------------------------------------------------
        # NOM APPRENANT
        # ----------------------------------------------------

        st.session_state.learner_name = (
            st.text_input(
                "Nom de l'apprenant",
                value=(
                    st.session_state.learner_name
                ),
                placeholder="ex: Jean Dupont",
            )
        )

        st.divider()

        # ----------------------------------------------------
        # RESET
        # ----------------------------------------------------

        if st.button(
            "Réinitialiser"
        ):

            clear_document()

            st.rerun()

        # ----------------------------------------------------
        # HISTORIQUE
        # ----------------------------------------------------
        # MODIFICATION :
        # - maximum 6 éléments
        # - plus récent → plus ancien
        # ----------------------------------------------------

        with st.expander(
            "Historique"
        ):

            history = (
                results_store.load_results()
            )

            if not history:

                st.caption(
                    "Aucun résultat enregistré"
                )

            else:

                # Garder uniquement les 6 derniers résultats
                recent_history = history[-6:]

                # Afficher le plus récent en premier
                for entry in reversed(
                    recent_history
                ):

                    learner = entry.get(
                        "learner_name",
                        "Apprenant"
                    )

                    score_data = entry.get(
                        "score",
                        {}
                    )

                    percentage = score_data.get(
                        "percentage",
                        0
                    )

                    timestamp = entry.get(
                        "timestamp",
                        ""
                    )

                    if timestamp:

                        timestamp = (
                            timestamp[:16]
                            .replace(
                                "T",
                                " "
                            )
                        )

                    st.markdown(
                        f"""
                        <div class="history-item">
                            <strong>{learner}</strong><br>
                            <span>{percentage:.0f}%</span>
                            <small>{timestamp}</small>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


# ============================================================
# ACCUEIL + UPLOAD
# ============================================================

def render_home_and_upload():

    ui_styles.render_feature_cards()

    with st.container(
        border=True
    ):

        ui_styles.render_dropzone_header()

        pdf_docs = st.file_uploader(
            "Importez un ou plusieurs PDF de formation",
            accept_multiple_files=True,
            type=["pdf"],
            key="pdf_uploader",
            label_visibility="collapsed",
        )

    alerts_placeholder = st.empty()

    if (
        len(pdf_docs)
        !=
        st.session_state.last_file_count
    ):

        st.session_state.last_file_count = (
            len(pdf_docs)
        )

        if pdf_docs:

            with st.spinner(
                "Traitement des PDF... "
                "Cela peut prendre un instant."
            ):

                process_pdfs(
                    pdf_docs,
                    alerts_placeholder
                )

            st.rerun()

        else:

            clear_document()

            st.rerun()


# ============================================================
# CONFIGURATION DU QUIZ
# ============================================================

def render_quiz_setup():

    st.success(
        "Document traité avec succès"
    )

    pages = (
        st.session_state.document_page_count
    )

    doc_count = len(
        st.session_state.document_names
    )

    # Documents
    for idx, name in enumerate(
        st.session_state.document_names
    ):

        if doc_count == 1:

            meta = (
                f"{pages} page(s)"
                if pages
                else
                "Document PDF"
            )

        else:

            meta = (
                f"{doc_count} documents — "
                f"{pages} pages au total"
            )

        col_doc, col_del = st.columns(
            [6, 1]
        )

        with col_doc:

            ui_styles.render_doc_row(
                name,
                meta
            )

        with col_del:

            st.write("")

            if st.button(
                "Supprimer",
                key=f"setup_del_{idx}",
                help=f"Retirer {name}",
            ):

                remove_document(idx)

    # Résumé
    if st.session_state.document_summary:

        with st.expander(
            "Résumé du document"
        ):

            st.markdown(
                f'<div class="summary-box">{st.session_state.document_summary}</div>',
                unsafe_allow_html=True,
            )

    # Configuration
    with st.container(
        border=True
    ):

        st.markdown(
            "### Configuration du quiz"
        )

        col1, col2, col3 = st.columns(
            3
        )

        # Nombre questions
        with col1:

            st.radio(
                "Nombre de questions",
                config.QUESTION_COUNT_OPTIONS,
                key="total_questions",
                horizontal=True,
            )

        # Types
        with col2:

            st.multiselect(
                "Types de questions",
                options=list(
                    config.QUESTION_TYPES.keys()
                ),
                format_func=lambda k:
                    config.QUESTION_TYPES[k],
                key="question_types",
            )

        # Difficulté
        with col3:

            st.select_slider(
                "Difficulté",
                options=list(
                    config.DIFFICULTY_LEVELS.keys()
                ),
                format_func=lambda k:
                    config.DIFFICULTY_LEVELS[k],
                key="difficulty",
            )

        disabled = (
            len(
                st.session_state.question_types
            )
            == 0
        )

        if disabled:

            st.warning(
                "Sélectionnez au moins un type de question"
            )

        # Génération
        if st.button(
            "Générer le quiz",
            use_container_width=True,
            disabled=disabled,
            type="primary",
        ):

            with st.spinner(
                "Génération du quiz par l'IA..."
            ):

                vector_db = (
                    ai_engine.load_vector_store()
                )

                st.session_state.question_bank = (
                    ai_engine.generate_quiz_from_faiss(
                        vector_db,
                        num_questions=(
                            st.session_state.total_questions
                        ),
                        question_types=(
                            st.session_state.question_types
                        ),
                        difficulty=(
                            st.session_state.difficulty
                        ),
                    )
                )

            if st.session_state.question_bank:

                # Nouveau quiz
                st.session_state.quiz_ongoing = True
                st.session_state.quiz_ended = False
                st.session_state.quiz_completed = False

                st.session_state.score = 0
                st.session_state.question_number = 0
                st.session_state.user_results = []

                st.session_state.review_mode = False
                st.session_state.balloons_showed = False

                st.session_state.category_breakdown = {}
                st.session_state.weak_points = []
                st.session_state.recommendations = ""

                st.session_state.report_bytes = None
                st.session_state.result_saved = False
                st.session_state.show_results = False

                st.rerun()

            else:

                st.error(
                    "Impossible de générer un quiz. "
                    "Vérifiez votre document."
                )


# ============================================================
# QUIZ EN COURS
# ============================================================

def render_quiz_in_progress():

    current_q_num = (
        st.session_state.question_number
    )

    total_questions = len(
        st.session_state.question_bank
    )

    # --------------------------------------------------------
    # Barre de progression supprimée.
    # --------------------------------------------------------

    ui_styles.render_progress_text(
        current_q_num + 1,
        total_questions
    )

    question_data = (
        st.session_state.question_bank[
            current_q_num
        ]
    )

    o1, o2, o3 = create_question(
        question_data,
        current_q_num
    )

    # Réponse validée
    if o2 > 0:

        st.session_state.score += o1

        st.session_state.question_number += o2

        if (
            st.session_state.question_number
            >=
            total_questions
        ):

            st.session_state.quiz_ended = True
            st.session_state.quiz_ongoing = False
            st.session_state.quiz_completed = True

        st.rerun()

    # Bouton terminer
    if o3:

        st.session_state.quiz_ended = True
        st.session_state.quiz_ongoing = False
        st.session_state.quiz_completed = True

        st.rerun()


# ============================================================
# RÉSULTATS + RÉVISION
# ============================================================

def render_results_and_revision():

    # Sécurité
    st.session_state.quiz_completed = True
    st.session_state.quiz_ongoing = False
    st.session_state.quiz_ended = True

    finalize_quiz_analysis()

    # Ballons
    if not st.session_state.balloons_showed:

        if st.session_state.score > 0:

            st.balloons()

        st.session_state.balloons_showed = True

    score_summary = build_score_summary()

    st.markdown(
        "## Quiz terminé"
    )

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    with st.container():

        col_gauge, col_stats = st.columns(
            [1, 2]
        )

        with col_gauge:

            ui_styles.render_score_gauge(
                score_summary["percentage"],
                "Taux de réussite"
            )

        with col_stats:

            m1, m2 = st.columns(2)

            m1.metric(
                "Score",
                f"{score_summary['score']} / "
                f"{score_summary['max_score']}"
            )

            m2.metric(
                "Questions répondues",
                f"{score_summary['answered']} / "
                f"{score_summary['total']}"
            )

            st.markdown(
                "**Compétences à revoir**"
            )

            st.markdown(
                ui_styles.weak_point_chips(
                    st.session_state.weak_points
                ),
                unsafe_allow_html=True,
            )

            strong_points = [
                cat
                for cat, stats
                in st.session_state.category_breakdown.items()
                if cat
                not in
                st.session_state.weak_points
            ]

            if strong_points:

                st.markdown(
                    "**Compétences maîtrisées**"
                )

                st.markdown(
                    "".join(
                        f'<span class="strong-point-chip">{cat}</span>'
                        for cat in strong_points
                    ),
                    unsafe_allow_html=True,
                )

        # Résultats par thème
        st.markdown(
            "### Résultats par thème"
        )

        if st.session_state.category_breakdown:

            for cat, stats in (
                st.session_state.category_breakdown.items()
            ):

                st.write(
                    f"**{cat}** — "
                    f"{stats['correct']}/"
                    f"{stats['total']} "
                    f"({stats['percentage']:.0f}%)"
                )

                st.progress(
                    stats["percentage"] / 100
                )

    # --------------------------------------------------------
    # PARCOURS DE RÉVISION
    # --------------------------------------------------------

    st.markdown("---")

    st.markdown(
        "### Parcours de révision recommandé"
    )

    st.markdown(
        f'<div class="recommendation-box">'
        f'{st.session_state.recommendations}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # DÉTAIL DES RÉPONSES
    # --------------------------------------------------------

    with st.expander(
        "Voir le détail des réponses"
    ):

        for idx, q_data in enumerate(
            st.session_state.question_bank
        ):

            result = (
                st.session_state.user_results[idx]
                if idx
                <
                len(
                    st.session_state.user_results
                )
                else None
            )

            with st.container(
                border=True
            ):

                st.markdown(
                    ui_styles.type_badge(
                        q_data.get(
                            "type",
                            "qcm"
                        )
                    )
                    +
                    ui_styles.category_tag(
                        q_data.get(
                            "category",
                            "General"
                        )
                    ),
                    unsafe_allow_html=True,
                )

                ui_styles.render_question_number(
                    idx + 1,
                    len(
                        st.session_state.question_bank
                    )
                )

                st.markdown(
                    f"**{q_data['question']}**"
                )

                if result is None:

                    st.info(
                        "Non répondu."
                    )

                    continue

                is_correct = result.get(
                    "is_correct"
                )

                user_answer = result.get(
                    "answer",
                    "Non répondu"
                )

                if is_correct:

                    st.success(
                        f"Réponse : "
                        f"{user_answer} "
                        f"(Correct)"
                    )

                else:

                    st.error(
                        f"Réponse : "
                        f"{user_answer} "
                        f"(Incorrect)"
                    )

                    if (
                        q_data.get("type")
                        ==
                        "qcm"
                    ):

                        st.info(
                            "Réponse correcte : "
                            f"{q_data.get('correct_option')}"
                        )

                    else:

                        st.info(
                            "Corrigé de référence : "
                            f"{q_data.get('expected_answer')}"
                        )

                        if result.get(
                            "feedback"
                        ):

                            st.caption(
                                "Feedback IA : "
                                f"{result['feedback']}"
                            )

    # --------------------------------------------------------
    # RAPPORT PDF
    # --------------------------------------------------------

    st.markdown(
        "### Rapport PDF"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Générer le rapport PDF",
            use_container_width=True,
            type="primary",
        ):

            with st.spinner(
                "Génération du rapport PDF..."
            ):

                st.session_state.report_bytes = (
                    pdf_utils.generate_pdf_report(
                        st.session_state.learner_name,
                        st.session_state.document_names,
                        score_summary,
                        st.session_state.category_breakdown,
                        st.session_state.weak_points,
                        st.session_state.recommendations,
                        st.session_state.question_bank,
                        st.session_state.user_results,
                    )
                )

    if st.session_state.report_bytes:

        with col2:

            st.download_button(
                "Télécharger le PDF",
                data=(
                    st.session_state.report_bytes
                ),
                file_name=(
                    f"rapport_"
                    f"{(
                        st.session_state.learner_name
                        or
                        'apprenant'
                    ).replace(' ', '_')}.pdf"
                ),
                mime="application/pdf",
                use_container_width=True,
            )

    # --------------------------------------------------------
    # NOUVEAU QUIZ
    # --------------------------------------------------------

    st.markdown("---")

    if st.button(
        "Nouveau quiz",
        use_container_width=True,
        type="primary",
    ):

        # Le document reste chargé
        st.session_state.pdf_uploaded = True

        # Retour à l'étape Quiz
        st.session_state.quiz_completed = False

        st.session_state.quiz_ongoing = False
        st.session_state.quiz_ended = True

        # Nettoyage
        st.session_state.question_bank = []
        st.session_state.user_results = []

        st.session_state.score = 0
        st.session_state.question_number = 0

        st.session_state.review_mode = False
        st.session_state.balloons_showed = False

        st.session_state.category_breakdown = {}
        st.session_state.weak_points = []
        st.session_state.recommendations = ""

        st.session_state.report_bytes = None
        st.session_state.result_saved = False
        st.session_state.show_results = False

        st.rerun()


# ============================================================
# APPLICATION PRINCIPALE
# ============================================================

def main():

    st.set_page_config(
        page_title=config.APP_TITLE,
        page_icon="📄",
        layout="wide",
    )

    ui_styles.inject_custom_css()

    init_session_state()

    render_sidebar()

    ui_styles.hero_banner(
        "AI Quiz Maker",
        "Créez un quiz, corrigez automatiquement "
        "les réponses et obtenez un parcours de "
        "révision personnalisé à partir de vos documents.",
    )

    # ========================================================
    # STEPPER
    # ========================================================

    step_index = current_step_index()

    ui_styles.render_stepper(
        step_index
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    if not st.session_state.pdf_uploaded:

        render_home_and_upload()

        return

    # ========================================================
    # QUIZ CONFIGURATION
    # ========================================================

    if (
        not st.session_state.quiz_completed
        and
        not st.session_state.quiz_ongoing
    ):

        render_quiz_setup()

        return

    # ========================================================
    # QUIZ EN COURS
    # ========================================================

    if (
        st.session_state.quiz_ongoing
        and
        not st.session_state.quiz_completed
    ):

        current_q_num = (
            st.session_state.question_number
        )

        total_questions = len(
            st.session_state.question_bank
        )

        if current_q_num < total_questions:

            render_quiz_in_progress()

        else:

            st.session_state.quiz_ongoing = False
            st.session_state.quiz_ended = True
            st.session_state.quiz_completed = True

            st.rerun()

        return

    # ========================================================
    # RÉSULTATS
    # ========================================================

    if st.session_state.quiz_completed:

        render_results_and_revision()

        return


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()