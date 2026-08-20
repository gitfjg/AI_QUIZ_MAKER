"""
Système de design : CSS personnalisé + composants d'interface réutilisables
(stepper, cartes fonctionnalités, zone d'import, jauge de score, etc.).
"""

import html

import streamlit as st


CUSTOM_CSS = """
<style>
:root {
    --primary: #6C47D4;
    --primary-hover: #7B5CDE;
    --primary-light: #F0EBFF;
    --primary-dark: #4A2C8A;
    --primary-gradient: linear-gradient(135deg, #6C47D4 0%, #8B6CE6 100%);
    --on-primary: #FFFFFF;
    --ink: #1A1A2E;
    --ink-soft: #5A5A7A;
    --ink-light: #8A8AA8;
    --success: #2D9B6E;
    --success-soft: #E8F5F0;
    --success-dark: #1E7A54;
    --warning: #D48B3C;
    --warning-soft: #FEF6ED;
    --danger: #D94A5A;
    --danger-soft: #FDEAEE;
    --border: #E2E2EA;
    --bg-app: #F7F7FC;
    --bg-white: #FFFFFF;
    --radius-lg: 16px;
    --radius-md: 12px;
    --radius-sm: 8px;
    --shadow-sm: 0 2px 8px rgba(26, 26, 46, 0.06);
    --shadow-md: 0 4px 20px rgba(108, 71, 212, 0.12);
    --shadow-lg: 0 8px 32px rgba(26, 26, 46, 0.10);
    --transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ---------- Base ---------- */
.stApp { background: var(--bg-app); }
h1, h2, h3, h4 { color: var(--ink) !important; font-weight: 700 !important; letter-spacing: -0.02em; }
p, li, span, label { color: var(--ink); }
[data-testid="stAppViewContainer"] .block-container { padding-top: 1.8rem; max-width: 1100px; }
header[data-testid="stHeader"] { background: transparent; }

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background: var(--bg-white);
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] > div { padding-top: 1.2rem; }
section[data-testid="stSidebar"] .stButton button {
    background: var(--primary);
    color: var(--on-primary) !important;
    border-radius: var(--radius-sm);
    border: none;
    width: 100%;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 0.5rem 0.8rem;
    transition: var(--transition);
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: var(--primary-hover);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
}
section[data-testid="stSidebar"] hr { margin: 1rem 0; border-color: var(--border); }
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
    color: var(--ink-soft) !important;
    font-size: 0.75rem;
}

/* Document item dans la sidebar - bouton × discret */
.sidebar-doc-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.3rem 0.5rem;
    background: var(--bg-app);
    border-radius: var(--radius-sm);
    margin-bottom: 0.25rem;
    transition: var(--transition);
}
.sidebar-doc-item:hover { background: var(--primary-light); }
.sidebar-doc-name {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}
.sidebar-doc-del {
    background: none;
    border: none;
    color: var(--ink-light);
    font-size: 0.9rem;
    cursor: pointer;
    padding: 0 0.2rem;
    transition: var(--transition);
    font-weight: 300;
    opacity: 0.5;
}
.sidebar-doc-del:hover {
    opacity: 1;
    color: var(--danger);
}

/* ---------- Buttons ---------- */
.stButton > button {
    background: var(--bg-white);
    color: var(--ink);
    border-radius: var(--radius-sm);
    font-weight: 600;
    font-size: 0.85rem;
    padding: 0.5rem 1.2rem;
    transition: var(--transition);
    border: 1.5px solid var(--border);
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
    border-color: var(--primary);
    color: var(--primary);
}
.stButton > button[kind="primary"] {
    background: var(--primary);
    color: var(--on-primary);
    border: none;
    box-shadow: var(--shadow-sm);
}
.stButton > button[kind="primary"]:hover {
    background: var(--primary-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
}
.stButton > button:disabled {
    background: #F0F0F4;
    color: #B0B0C0 !important;
    border-color: var(--border);
    cursor: not-allowed;
}
.stButton > button:disabled:hover {
    transform: none;
    box-shadow: none;
}

/* ---------- Metrics ---------- */
div[data-testid="stMetric"] {
    background: var(--bg-white);
    border-radius: var(--radius-md);
    padding: 1rem;
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
}
div[data-testid="stMetric"] label {
    color: var(--ink-soft) !important;
    font-weight: 500;
}

/* ---------- Progress bar - VERT UNIFORME ---------- */
/* Correction du CSS pour avoir une barre verte uniforme */
div[data-testid="stProgress"] {
    background: #E8E8EF !important;
    border-radius: 20px !important;
    height: 8px !important;
    overflow: hidden;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    margin: 0.5rem 0 !important;
}
div[data-testid="stProgress"] > div {
    background: transparent !important;
    border-radius: 20px !important;
    height: 100% !important;
}
div[data-testid="stProgress"] > div > div {
    background: #2D9B6E !important;
    border-radius: 20px !important;
    height: 100% !important;
    transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
/* Forcer la couleur verte pour tous les états */
div[data-testid="stProgress"] > div > div > div {
    background: #2D9B6E !important;
}
/* Supprimer toute couleur par défaut de Streamlit */
.stProgress > div {
    background: #E8E8EF !important;
}

/* ---------- File uploader ---------- */
section[data-testid="stFileUploaderDropzone"] {
    background: var(--primary-light);
    border: 2px dashed var(--primary);
    border-radius: var(--radius-lg);
    padding: 2.4rem 1.5rem;
    transition: var(--transition);
}
section[data-testid="stFileUploaderDropzone"]:hover {
    border-color: var(--primary-hover);
    background: #E8DFFF;
}
section[data-testid="stFileUploaderDropzone"] button {
    background: var(--primary) !important;
    color: var(--on-primary) !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
}
section[data-testid="stFileUploaderDropzone"] button:hover {
    background: var(--primary-hover) !important;
    transform: translateY(-1px);
}
section[data-testid="stFileUploaderDropzone"] button p {
    color: var(--on-primary) !important;
}
section[data-testid="stFileUploaderDropzone"] > div {
    display: flex;
    flex-direction: column;
    align-items: center;
}
section[data-testid="stFileUploaderDropzone"] button {
    margin: 0 auto !important;
}

/* ---------- Cards ---------- */
.qm-card {
    background: var(--bg-white);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.4rem 1.5rem;
    box-shadow: var(--shadow-sm);
    transition: var(--transition);
}
.qm-card:hover { box-shadow: var(--shadow-md); }

/* ---------- Question styling - sobre et professionnel ---------- */
.question-number {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--ink-soft);
    background: #F0F0F4;
    padding: 0.2rem 0.8rem;
    border-radius: 20px;
    letter-spacing: 0.02em;
    margin-bottom: 0.5rem;
}
.question-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--ink);
    margin: 0.25rem 0 0.75rem 0;
    line-height: 1.5;
}

/* ---------- Badges ---------- */
.quiz-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 8px;
    letter-spacing: 0.01em;
}
.badge-qcm { background: #E8EEFF; color: #4A6CC4; }
.badge-open { background: #E4F5EE; color: #2D9B6E; }
.badge-exercise { background: #FEF3E8; color: #D48B3C; }

.category-tag {
    display: inline-block;
    background: #F0F0F4;
    color: var(--ink-soft);
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.68rem;
    margin-bottom: 8px;
}

/* ---------- Hero ---------- */
.hero-banner {
    background: var(--primary-gradient);
    padding: 2rem 2.2rem;
    border-radius: var(--radius-lg);
    color: white;
    margin-bottom: 1.4rem;
    box-shadow: var(--shadow-md);
}
.hero-banner h1 {
    color: white !important;
    margin: 0 0 0.3rem 0;
    font-size: 1.8rem !important;
    font-weight: 700;
}
.hero-banner p {
    color: rgba(255, 255, 255, 0.85);
    font-size: 0.95rem;
    margin: 0;
}

/* ---------- Weak points ---------- */
.weak-point-chip {
    display: inline-block;
    background: var(--danger-soft);
    color: var(--danger);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 3px 4px 3px 0;
    border: 1px solid rgba(217, 74, 90, 0.2);
}
.strong-point-chip {
    display: inline-block;
    background: var(--success-soft);
    color: var(--success);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: 3px 4px 3px 0;
    border: 1px solid rgba(45, 155, 110, 0.2);
}
.recommendation-box {
    background: var(--success-soft);
    border-left: 4px solid var(--success);
    padding: 1rem 1.2rem;
    border-radius: var(--radius-sm);
    line-height: 1.7;
}
.summary-box {
    background: var(--primary-light);
    border: 1px solid rgba(108, 71, 212, 0.15);
    border-radius: var(--radius-md);
    padding: 1.1rem 1.3rem;
    line-height: 1.7;
}

/* ---------- Stepper - dynamique ---------- */
.qm-stepper {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 2rem;
    padding: 0.6rem 1.5rem;
    background: var(--bg-white);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid var(--border);
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

.qm-step {
    display: flex;
    align-items: center;
    flex: 1;
    cursor: default;
    position: relative;
    justify-content: center;
}

.qm-step:last-child { flex: 0; }

.qm-step-circle {
    width: 36px;
    height: 36px;
    min-width: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 0.82rem;
    background: #F0F0F4;
    color: var(--ink-soft);
    border: 2px solid var(--border);
    transition: var(--transition);
    position: relative;
    z-index: 2;
}

/* État terminé - violet avec ✓ */
.qm-step.done .qm-step-circle {
    background: var(--primary);
    border-color: var(--primary);
    color: var(--on-primary);
    box-shadow: 0 0 0 4px rgba(108, 71, 212, 0.15);
}
.qm-step.done .qm-step-label {
    color: var(--primary-dark);
    font-weight: 600;
}
.qm-step-line.done {
    background: var(--primary);
}

/* État actif - reste neutre car "actif" n'est pas "terminé" */
.qm-step.active .qm-step-circle {
    background: #F0F0F4;
    border-color: var(--border);
    color: var(--ink-soft);
    transform: scale(1.05);
    box-shadow: 0 0 0 4px rgba(108, 71, 212, 0.1);
}
.qm-step.active .qm-step-label {
    color: var(--ink);
    font-weight: 600;
}

/* Les étapes futures restent neutres */
.qm-step-label {
    margin-left: 0.5rem;
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--ink-soft);
    white-space: nowrap;
    transition: var(--transition);
}

.qm-step-line {
    flex: 1;
    height: 2px;
    background: var(--border);
    margin: 0 0.5rem;
    border-radius: 2px;
    transition: var(--transition);
    position: relative;
    z-index: 1;
    max-width: 60px;
}

/* Animation d'entrée */
.qm-step {
    animation: fadeSlideIn 0.4s ease forwards;
    opacity: 0;
    transform: translateY(6px);
}
.qm-step:nth-child(1) { animation-delay: 0.05s; }
.qm-step:nth-child(3) { animation-delay: 0.10s; }
.qm-step:nth-child(5) { animation-delay: 0.15s; }
.qm-step:nth-child(7) { animation-delay: 0.20s; }

@keyframes fadeSlideIn {
    0% { opacity: 0; transform: translateY(6px); }
    100% { opacity: 1; transform: translateY(0); }
}

.qm-step-circle {
    transition: var(--transition);
}
.qm-step.done .qm-step-circle {
    animation: popCheck 0.4s ease forwards;
}
@keyframes popCheck {
    0% { transform: scale(0.9); }
    50% { transform: scale(1.15); }
    100% { transform: scale(1); }
}

/* ---------- Dropzone header ---------- */
.qm-dropzone-header { text-align: center; margin-bottom: 0.6rem; }
.qm-dropzone-title {
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--ink);
}
.qm-dropzone-sub {
    font-size: 0.8rem;
    color: var(--ink-soft);
    margin-top: 0.15rem;
}

/* ---------- Document row ---------- */
.qm-doc-row {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    background: var(--bg-white);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.8rem 1rem;
    margin-bottom: 0.5rem;
    transition: var(--transition);
}
.qm-doc-row:hover {
    border-color: var(--primary);
    box-shadow: var(--shadow-sm);
}
.qm-doc-icon {
    width: 38px;
    height: 38px;
    min-width: 38px;
    border-radius: var(--radius-sm);
    background: var(--primary-light);
    color: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.75rem;
}
.qm-doc-name {
    font-weight: 500;
    color: var(--ink);
    font-size: 0.88rem;
}
.qm-doc-meta {
    font-size: 0.75rem;
    color: var(--ink-soft);
}

/* ---------- Gauge ---------- */
.qm-gauge-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 0.5rem 0 0.2rem;
}
.qm-gauge {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    transition: var(--transition);
}
.qm-gauge-inner {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    background: var(--bg-white);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.04);
}
.qm-gauge-value {
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--ink);
}
.qm-gauge-caption {
    font-size: 0.7rem;
    color: var(--ink-soft);
    margin-top: 2px;
}

/* ---------- Revision section ---------- */
.revision-section {
    background: var(--bg-white);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.5rem;
    margin-top: 1rem;
    box-shadow: var(--shadow-sm);
}
.revision-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid var(--primary-light);
}
.revision-header h3 {
    margin: 0;
    color: var(--primary-dark);
}

/* ---------- Feature cards ---------- */
.feature-card {
    background: var(--bg-white);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.2rem 1rem;
    text-align: center;
    transition: var(--transition);
    height: 100%;
}
.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-md);
    border-color: var(--primary-light);
}
.feature-card h4 {
    font-size: 0.9rem;
    color: var(--ink);
    margin-bottom: 0.3rem;
}
.feature-card p {
    font-size: 0.8rem;
    color: var(--ink-soft);
    margin: 0;
}

/* ---------- Progress text ---------- */
.progress-text {
    font-size: 0.85rem;
    color: var(--ink-soft);
    font-weight: 500;
    text-align: center;
    margin-bottom: 0.3rem;
}

/* ---------- Container cohérent ---------- */
.stContainer {
    border-radius: var(--radius-md) !important;
}
</style>
"""


def inject_custom_css():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# Hero
# ============================================================

def hero_banner(title, subtitle):
    st.markdown(
        f"""
        <div class="hero-banner">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Stepper - 3 étapes avec ✓ pour les étapes terminées
# ============================================================

STEPS = [
    ("1", "Document"),
    ("2", "Quiz"),
    ("3", "Resultats & Revision"),
]


def render_stepper(current_index: int):
    """
    Affiche le stepper avec :
    - Les étapes terminées (index < current_index) : violettes avec ✓
    - Si on est sur la dernière étape (current_index == 2), toutes les étapes sont violettes avec ✓
    - L'étape active (current_index == 1) : neutre mais en gras
    - Les étapes futures : neutres
    """
    parts = ['<div class="qm-stepper">']
    
    # Déterminer combien d'étapes sont terminées
    # Si on est sur la dernière étape, tout est terminé
    if current_index >= len(STEPS) - 1:
        # Toutes les étapes sont terminées
        done_count = len(STEPS)
    else:
        # Seulement les étapes avant l'étape active sont terminées
        done_count = current_index

    for i, (num, label) in enumerate(STEPS):
        if i < done_count:
            # Étape terminée → violet avec ✓
            step_state = "done"
            display_text = "✓"
        elif i == current_index:
            # Étape active → neutre mais visible
            step_state = "active"
            display_text = num
        else:
            # Étape future → neutre
            step_state = ""
            display_text = num

        parts.append(f'<div class="qm-step {step_state}">')
        parts.append(f'<div class="qm-step-circle">{display_text}</div>')
        parts.append(f'<div class="qm-step-label">{label}</div>')
        parts.append("</div>")

        if i < len(STEPS) - 1:
            line_state = "done" if i < done_count else ""
            parts.append(f'<div class="qm-step-line {line_state}"></div>')

    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


# ============================================================
# Feature cards
# ============================================================

FEATURES = [
    ("Generation automatique du quiz", "L'IA lit votre document et cree des questions variees (QCM, ouvertes, exercices)."),
    ("Evaluation des reponses", "Correction automatique, y compris pour les reponses redigees, avec feedback."),
    ("Analyse des resultats", "Score detaille par theme pour reperer precisement vos points faibles."),
    ("Parcours de revision personnalise", "Des recommandations ciblees pour progresser la ou ca compte."),
]


def render_feature_cards():
    cols = st.columns(len(FEATURES))
    for col, (title, desc) in zip(cols, FEATURES):
        with col:
            st.markdown(
                f"""
                <div class="feature-card">
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
# Dropzone
# ============================================================

def render_dropzone_header():
    st.markdown(
        """
        <div class="qm-dropzone-header">
            <div class="qm-dropzone-title">Deposez votre cours ici</div>
            <div class="qm-dropzone-sub">PDF • 200 Mo maximum par fichier — plusieurs fichiers acceptes</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Document row
# ============================================================

def render_doc_row(name, meta):
    safe_name = html.escape(str(name))
    safe_meta = html.escape(str(meta))
    st.markdown(
        f"""
        <div class="qm-doc-row">
            <div class="qm-doc-icon">PDF</div>
            <div>
                <div class="qm-doc-name">{safe_name}</div>
                <div class="qm-doc-meta">{safe_meta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Question number helper
# ============================================================

def render_question_number(num, total):
    st.markdown(
        f'<div class="question-number">Question {num} / {total}</div>',
        unsafe_allow_html=True,
    )


def render_question_title(title):
    st.markdown(
        f'<div class="question-title">{title}</div>',
        unsafe_allow_html=True,
    )


def render_progress_text(current, total):
    st.markdown(
        f'<div class="progress-text">Question {current} sur {total}</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# Gauge
# ============================================================

def render_score_gauge(percentage: float, caption: str = "Score global"):
    pct = max(0, min(100, percentage))

    if pct >= 75:
        color = "#2D9B6E"
    elif pct >= 50:
        color = "#D48B3C"
    else:
        color = "#D94A5A"

    gauge_bg = f"conic-gradient({color} {pct * 3.6:.1f}deg, #EDEBF5 0deg)"

    st.markdown(
        f"""
        <div class="qm-gauge-wrap">
            <div class="qm-gauge" style="background: {gauge_bg};">
                <div class="qm-gauge-inner">
                    <div class="qm-gauge-value">{pct:.0f}%</div>
                    <div class="qm-gauge-caption">{html.escape(caption)}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Badges
# ============================================================

def type_badge(q_type):
    labels = {"qcm": "QCM", "open": "Question ouverte", "exercise": "Exercice"}
    classes = {"qcm": "badge-qcm", "open": "badge-open", "exercise": "badge-exercise"}
    label = labels.get(q_type, q_type)
    cls = classes.get(q_type, "badge-qcm")
    return f'<span class="quiz-badge {cls}">{label}</span>'


def category_tag(category):
    return f'<span class="category-tag">{html.escape(str(category))}</span>'


def weak_point_chips(weak_points):
    if not weak_points:
        return '<span class="strong-point-chip">Aucun point faible</span>'
    return "".join(f'<span class="weak-point-chip">{html.escape(str(wp))}</span>' for wp in weak_points)


def strong_point_chips(strong_points):
    if not strong_points:
        return ""
    return "".join(f'<span class="strong-point-chip">{html.escape(str(sp))}</span>' for sp in strong_points)


# ============================================================
# Revision section
# ============================================================

def render_revision_header():
    st.markdown(
        """
        <div class="revision-section">
            <div class="revision-header">
                <h3>Parcours de revision personnalise</h3>
            </div>
        """,
        unsafe_allow_html=True,
    )


def render_revision_footer():
    st.markdown("</div>", unsafe_allow_html=True)