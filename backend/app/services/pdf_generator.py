from io import BytesIO
from datetime import datetime
from typing import Dict, List, Any, Optional
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

from ..models.script import Script, Scene

try:
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        DEFAULT_FONT = 'DejaVuSans'
        DEFAULT_FONT_BOLD = 'DejaVuSans-Bold'
    else:
        DEFAULT_FONT = 'Helvetica'
        DEFAULT_FONT_BOLD = 'Helvetica-Bold'
except:
    DEFAULT_FONT = 'Helvetica'
    DEFAULT_FONT_BOLD = 'Helvetica-Bold'


class PDFReportGenerator:
    RATING_COLORS = {
        "0+": colors.green,
        "6+": colors.blue,
        "12+": colors.yellow,
        "16+": colors.orange,
        "18+": colors.red,
    }

    CATEGORY_LABELS_RU = {
        "violence": "Насилие",
        "gore": "Жестокость",
        "sex_act": "Сексуальный контент",
        "nudity": "Нагота",
        "profanity": "Ненормативная лексика",
        "drugs": "Наркотики",
        "child_risk": "Риск для детей",
    }

    def __init__(self, language: str = "ru"):
        self.language = language
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=24,
                textColor=colors.HexColor("#1e40af"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading1"],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=16,
                textColor=colors.HexColor("#1e40af"),
                spaceAfter=12,
                spaceBefore=12,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="SubSection",
                parent=self.styles["Heading2"],
                fontName=DEFAULT_FONT_BOLD,
                fontSize=14,
                textColor=colors.HexColor("#4b5563"),
                spaceAfter=10,
            )
        )

        self.styles['Normal'].fontName = DEFAULT_FONT

    def generate_report(
        self,
        script: Script,
        scenes: List[Scene],
        recommendations: Optional[List[Dict[str, Any]]] = None,
        rating_gaps: Optional[List[Dict[str, Any]]] = None,
    ) -> BytesIO:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        story = []

        story.append(
            Paragraph(
                (
                    "ОТЧЕТ ПО ВОЗРАСТНОМУ РЕЙТИНГУ"
                    if self.language == "ru"
                    else "AGE RATING REPORT"
                ),
                self.styles["CustomTitle"],
            )
        )
        story.append(Spacer(1, 12))

        story.extend(self._create_header_section(script))
        story.append(Spacer(1, 20))

        story.extend(self._create_rating_section(script))
        story.append(Spacer(1, 20))

        scores_chart = self._create_scores_chart(dict(script.agg_scores or {}))
        if scores_chart:
            story.append(scores_chart)
            story.append(Spacer(1, 20))

        if scenes:
            story.extend(self._create_scenes_section(scenes))
            story.append(Spacer(1, 20))

        if rating_gaps:
            story.extend(self._create_gaps_section(rating_gaps))
            story.append(Spacer(1, 20))

        if recommendations:
            story.extend(self._create_recommendations_section(recommendations))

        story.append(PageBreak())
        story.extend(self._create_footer_section())

        doc.build(story)
        buffer.seek(0)
        return buffer

    def _create_header_section(self, script: Script) -> List:
        elements = []

        header_data = [
            ["Название:", script.title],
            [
                "Дата создания:",
                (
                    script.created_at.strftime("%d.%m.%Y %H:%M")
                    if script.created_at
                    else "—"
                ),
            ],
            ["Всего сцен:", str(script.total_scenes or 0)],
            ["Версия модели:", script.model_version or "—"],
        ]

        table = Table(header_data, colWidths=[2 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), DEFAULT_FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 11),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4b5563")),
                    ("FONTNAME", (0, 0), (0, -1), DEFAULT_FONT_BOLD),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(table)
        return elements

    def _create_rating_section(self, script: Script) -> List:
        elements = []

        elements.append(Paragraph("Возрастной рейтинг", self.styles["SectionHeader"]))

        rating = str(script.predicted_rating or "—")
        rating_color = self.RATING_COLORS.get(rating, colors.grey)

        rating_table = Table(
            [[Paragraph(f"<b>{rating}</b>", self.styles["Normal"])]],
            colWidths=[1.5 * inch],
        )
        rating_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("FONTSIZE", (0, 0), (-1, -1), 24),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("BACKGROUND", (0, 0), (-1, -1), rating_color),
                    ("ROUNDEDCORNERS", [10, 10, 10, 10]),
                    ("INNERGRID", (0, 0), (-1, -1), 0, colors.white),
                    ("BOX", (0, 0), (-1, -1), 2, colors.white),
                    ("TOPPADDING", (0, 0), (-1, -1), 15),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                ]
            )
        )

        elements.append(rating_table)
        return elements

    def _create_scores_chart(self, scores: Dict[str, float]) -> Optional[Image]:
        if not scores:
            return None

        fig, ax = plt.subplots(figsize=(8, 4))

        categories = [self.CATEGORY_LABELS_RU.get(k, k) for k in scores.keys()]
        values = [v * 100 for v in scores.values()]

        colors_list = [
            "#ef4444" if v > 60 else "#f59e0b" if v > 30 else "#10b981" for v in values
        ]

        bars = ax.barh(categories, values, color=colors_list)

        ax.set_xlabel("Оценка (%)", fontsize=11)
        ax.set_xlim(0, 100)
        ax.grid(axis="x", alpha=0.3)

        for i, (bar, value) in enumerate(zip(bars, values)):
            ax.text(value + 2, i, f"{value:.1f}%", va="center", fontsize=10)

        plt.tight_layout()

        img_buffer = BytesIO()
        plt.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
        plt.close(fig)
        img_buffer.seek(0)

        return Image(img_buffer, width=6 * inch, height=3 * inch)

    def _create_scenes_section(self, scenes: List[Scene]) -> List:
        elements = []

        elements.append(Paragraph("Проблемные сцены", self.styles["SectionHeader"]))

        problematic_scenes = sorted(
            [
                s
                for s in scenes
                if max(
                    s.violence,
                    s.gore,
                    s.sex_act,
                    s.nudity,
                    s.profanity,
                    s.drugs,
                    s.child_risk,
                )
                > 0.3
            ],
            key=lambda s: max(
                s.violence,
                s.gore,
                s.sex_act,
                s.nudity,
                s.profanity,
                s.drugs,
                s.child_risk,
            ),
            reverse=True,
        )[:10]

        if not problematic_scenes:
            elements.append(
                Paragraph("Проблемные сцены не обнаружены", self.styles["Normal"])
            )
            return elements

        for scene in problematic_scenes:
            scene_elements = []

            scene_elements.append(
                Paragraph(
                    f"<b>Сцена {scene.scene_id}: {scene.heading}</b>",
                    self.styles["SubSection"],
                )
            )

            issues = []
            for cat in [
                "violence",
                "gore",
                "sex_act",
                "nudity",
                "profanity",
                "drugs",
                "child_risk",
            ]:
                value = getattr(scene, cat, 0)
                if value > 0.3:
                    label = self.CATEGORY_LABELS_RU.get(cat, cat)
                    issues.append([label, f"{value*100:.1f}%"])

            if issues:
                issues_table = Table(issues, colWidths=[2.5 * inch, 1 * inch])
                issues_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (-1, -1), DEFAULT_FONT),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#991b1b")),
                            ("FONTNAME", (1, 0), (1, -1), DEFAULT_FONT_BOLD),
                            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                scene_elements.append(issues_table)

            if scene.sample_text:
                scene_elements.append(Spacer(1, 6))
                scene_elements.append(
                    Paragraph(
                        f"<i>{scene.sample_text[:200]}...</i>", self.styles["Normal"]
                    )
                )

            scene_elements.append(Spacer(1, 12))
            elements.append(KeepTogether(scene_elements))

        return elements

    def _create_gaps_section(self, rating_gaps: List[Dict[str, Any]]) -> List:
        elements = []

        elements.append(
            Paragraph("Необходимые изменения", self.styles["SectionHeader"])
        )

        if not rating_gaps:
            return elements

        gaps_data = [["Категория", "Текущее", "Целевое", "Разрыв", "Приоритет"]]

        for gap in rating_gaps[:10]:
            gaps_data.append(
                [
                    gap.get("dimension", ""),
                    f"{gap.get('current_score', 0):.2f}",
                    f"{gap.get('target_score', 0):.2f}",
                    f"-{gap.get('gap', 0)*100:.0f}%",
                    gap.get("priority", "medium").upper(),
                ]
            )

        gaps_table = Table(
            gaps_data,
            colWidths=[2 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch, 1 * inch],
        )
        gaps_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), DEFAULT_FONT_BOLD),
                    ("FONTNAME", (0, 1), (-1, -1), DEFAULT_FONT),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e40af")),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        elements.append(gaps_table)
        return elements

    def _create_recommendations_section(
        self, recommendations: List[Dict[str, Any]]
    ) -> List:
        elements = []

        elements.append(Paragraph("Рекомендации", self.styles["SectionHeader"]))

        for idx, rec in enumerate(recommendations[:15], 1):
            rec_elements = []

            rec_elements.append(
                Paragraph(
                    f"<b>{idx}. {rec.get('description', '')}</b>", self.styles["Normal"]
                )
            )

            details = []
            if rec.get("category"):
                details.append(f"Категория: {rec.get('category')}")
            if rec.get("difficulty"):
                details.append(f"Сложность: {rec.get('difficulty')}")
            if rec.get("impact_score"):
                details.append(f"Влияние: {rec.get('impact_score')*100:.0f}%")

            if details:
                rec_elements.append(
                    Paragraph(" | ".join(details), self.styles["Normal"])
                )

            if rec.get("specific_changes"):
                changes_text = "; ".join(rec.get("specific_changes", []))
                rec_elements.append(
                    Paragraph(f"<i>{changes_text}</i>", self.styles["Normal"])
                )

            rec_elements.append(Spacer(1, 10))
            elements.append(KeepTogether(rec_elements))

        return elements

    def _create_footer_section(self) -> List:
        elements = []

        footer_text = f"""
        <para align=center>
        Отчет сгенерирован автоматически<br/>
        {datetime.now().strftime("%d.%m.%Y %H:%M")}<br/>
        <i>Movie Rating Analysis System v1.0</i>
        </para>
        """

        elements.append(Paragraph(footer_text, self.styles["Normal"]))
        return elements
