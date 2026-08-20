"""
Utilitaires PDF :
- Extraction du texte des documents de formation importés.
- Génération du rapport PDF destiné au formateur
  (score, points faibles, recommandations, détail des réponses).
"""

import io
from datetime import datetime

import streamlit as st
from PyPDF2 import PdfReader

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


# ============================================================
# Extraction du texte
# ============================================================

@st.cache_data(show_spinner=False)
def get_pdf_text(pdf_files):
    """Extrait le texte de un ou plusieurs fichiers PDF uploadés."""

    full_text = ""

    for pdf_file in pdf_files:
        try:
            pdf = PdfReader(pdf_file)

            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    full_text += page_text + "\n"

        except Exception as e:
            st.error(f"Impossible de lire le PDF « {getattr(pdf_file, 'name', '?')} » : {e}")

    return full_text


@st.cache_data(show_spinner=False)
def get_pdf_page_count(pdf_files):
    """Retourne le nombre total de pages pour un ou plusieurs PDF uploadés."""

    total_pages = 0

    for pdf_file in pdf_files:
        try:
            pdf_file.seek(0)
            pdf = PdfReader(pdf_file)
            total_pages += len(pdf.pages)
        except Exception:
            continue
        finally:
            pdf_file.seek(0)

    return total_pages


# ============================================================
# Styles du rapport
# ============================================================

def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="TitleCustom",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1F2A44"),
        alignment=TA_CENTER,
        spaceAfter=6,
    ))

    styles.add(ParagraphStyle(
        name="SubtitleCustom",
        fontSize=11,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=13,
        textColor=colors.white,
        backColor=colors.HexColor("#4F46E5"),
        leading=20,
        spaceBefore=16,
        spaceAfter=10,
        leftIndent=6,
    ))

    styles.add(ParagraphStyle(
        name="BodyCustom",
        fontSize=10.2,
        leading=14.5,
        alignment=TA_LEFT,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="WeakPoint",
        fontSize=10.2,
        leading=14.5,
        textColor=colors.HexColor("#B91C1C"),
    ))

    return styles


# ============================================================
# Génération du rapport formateur
# ============================================================

def generate_pdf_report(
    learner_name,
    document_names,
    score_summary,
    category_breakdown,
    weak_points,
    recommendations,
    question_bank,
    user_results,
):
    """
    Construit le rapport PDF complet pour le formateur et retourne
    les octets du fichier (utilisables directement dans st.download_button).
    """

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
    )

    styles = _build_styles()
    story = []

    # ---------------- En-tête ----------------
    story.append(Paragraph("Rapport d'évaluation — AI Quiz Maker", styles["TitleCustom"]))
    story.append(Paragraph(
        f"Apprenant : {learner_name or 'Non renseigné'} &nbsp;|&nbsp; "
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
        styles["SubtitleCustom"],
    ))
    story.append(Paragraph(
        f"<b>Document(s) analysé(s) :</b> {', '.join(document_names) if document_names else 'N/A'}",
        styles["BodyCustom"],
    ))
    story.append(Spacer(1, 10))

    # ---------------- 1. Score global ----------------
    story.append(Paragraph("1. Score global", styles["SectionTitle"]))

    data = [
        ["Score total", f"{score_summary['score']:.1f} / {score_summary['max_score']}"],
        ["Taux de réussite", f"{score_summary['percentage']:.1f} %"],
        ["Questions répondues", f"{score_summary['answered']} / {score_summary['total']}"],
    ]
    table = Table(data, colWidths=[8 * cm, 8 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF2FF")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2A44")),
        ("FONTSIZE", (0, 0), (-1, -1), 10.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
    ]))
    story.append(table)
    story.append(Spacer(1, 14))

    # ---------------- 2. Résultats par thème ----------------
    story.append(Paragraph("2. Résultats par thème", styles["SectionTitle"]))

    cat_data = [["Thème", "Score", "Taux"]]
    for cat, stats in category_breakdown.items():
        cat_data.append([
            cat,
            f"{stats['correct']} / {stats['total']}",
            f"{stats['percentage']:.0f} %",
        ])

    cat_table = Table(cat_data, colWidths=[8 * cm, 4 * cm, 4 * cm])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 14))

    # ---------------- 3. Points faibles ----------------
    story.append(Paragraph("3. Points faibles identifiés", styles["SectionTitle"]))

    if weak_points:
        for wp in weak_points:
            story.append(Paragraph(f"• {wp}", styles["WeakPoint"]))
    else:
        story.append(Paragraph(
            "Aucun point faible majeur détecté. Excellent travail !",
            styles["BodyCustom"],
        ))
    story.append(Spacer(1, 14))

    # ---------------- 4. Recommandations ----------------
    story.append(Paragraph("4. Parcours de révision recommandé", styles["SectionTitle"]))
    story.append(Paragraph(recommendations.replace("\n", "<br/>"), styles["BodyCustom"]))
    story.append(Spacer(1, 10))

    # ---------------- 5. Détail des réponses ----------------
    story.append(PageBreak())
    story.append(Paragraph("5. Détail des réponses", styles["SectionTitle"]))

    for idx, q in enumerate(question_bank):
        result = user_results[idx] if idx < len(user_results) else {}
        is_correct = result.get("is_correct")
        icon = "OK" if is_correct else ("X" if is_correct is not None else "-")

        story.append(Paragraph(
            f"<b>Q{idx + 1} [{q.get('type', 'qcm').upper()} — {q.get('category', 'Général')}] ({icon})</b><br/>"
            f"{q['question']}",
            styles["BodyCustom"],
        ))

        user_answer = result.get("answer", "Non répondu")
        story.append(Paragraph(f"Réponse de l'apprenant : {user_answer}", styles["BodyCustom"]))

        if q.get("type") == "qcm":
            story.append(Paragraph(f"Réponse correcte : {q.get('correct_option', '')}", styles["BodyCustom"]))
        else:
            story.append(Paragraph(f"Corrigé de référence : {q.get('expected_answer', '')}", styles["BodyCustom"]))
            if result.get("feedback"):
                story.append(Paragraph(f"Feedback IA : {result['feedback']}", styles["BodyCustom"]))

        story.append(Spacer(1, 8))

    doc.build(story)

    buffer.seek(0)
    return buffer.getvalue()
