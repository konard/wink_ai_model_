from typing import List, Dict, Tuple
import numpy as np
import re

from ..pipeline import MovieRatingPipeline
from .schemas import (
    RatingAdvisorRequest,
    RatingAdvisorResponse,
    RecommendationAction,
    SceneIssue,
    RatingGap,
)


class RatingAdvisor:
    RATING_ORDER = ["0+", "6+", "12+", "16+", "18+"]

    RATING_THRESHOLDS = {
        "0+": {
            "violence": 0.0,
            "gore": 0.0,
            "sex_act": 0.0,
            "nudity": 0.0,
            "profanity": 0.0,
            "drugs": 0.0,
            "child_risk": 0.0,
        },
        "6+": {
            "violence": 0.2,
            "gore": 0.0,
            "sex_act": 0.0,
            "nudity": 0.0,
            "profanity": 0.1,
            "drugs": 0.0,
            "child_risk": 0.1,
        },
        "12+": {
            "violence": 0.4,
            "gore": 0.2,
            "sex_act": 0.0,
            "nudity": 0.2,
            "profanity": 0.3,
            "drugs": 0.2,
            "child_risk": 0.2,
        },
        "16+": {
            "violence": 0.6,
            "gore": 0.4,
            "sex_act": 0.3,
            "nudity": 0.5,
            "profanity": 0.6,
            "drugs": 0.5,
            "child_risk": 0.4,
        },
        "18+": {
            "violence": 1.0,
            "gore": 1.0,
            "sex_act": 1.0,
            "nudity": 1.0,
            "profanity": 1.0,
            "drugs": 1.0,
            "child_risk": 1.0,
        },
    }

    DIMENSION_TRANSLATIONS = {
        "violence": {"en": "Violence", "ru": "Насилие"},
        "gore": {"en": "Gore", "ru": "Жестокость"},
        "sex_act": {"en": "Sexual Content", "ru": "Сексуальный контент"},
        "nudity": {"en": "Nudity", "ru": "Нагота"},
        "profanity": {"en": "Profanity", "ru": "Ненормативная лексика"},
        "drugs": {"en": "Drugs", "ru": "Наркотики"},
        "child_risk": {"en": "Child Risk", "ru": "Риск для детей"},
    }

    def __init__(self, use_llm: bool = False):
        self.pipeline = MovieRatingPipeline()

    def analyze(self, request: RatingAdvisorRequest) -> RatingAdvisorResponse:
        result = self.pipeline.rate_script(
            script_text=request.script_text, script_id=None
        )

        current_rating = request.current_rating or result["predicted_rating"]
        target_rating = request.target_rating

        current_scores = result["agg_scores"]
        target_thresholds = self.RATING_THRESHOLDS[target_rating]

        is_achievable, confidence = self._check_achievability(
            current_rating, target_rating, current_scores, target_thresholds
        )

        rating_gaps = self._calculate_gaps(
            current_scores, target_thresholds, request.language
        )

        problematic_scenes = self._identify_problematic_scenes(
            result["scenes"], target_thresholds, request.language
        )

        recommended_actions = self._generate_recommendations(
            problematic_scenes,
            rating_gaps,
            request.language,
            request.script_text,
            current_rating,
            target_rating,
            result["scenes"],
        )

        summary = self._generate_summary(
            current_rating,
            target_rating,
            is_achievable,
            rating_gaps,
            len(problematic_scenes),
            request.language,
        )

        effort = self._estimate_effort(problematic_scenes, rating_gaps)

        alternative_targets = (
            self._suggest_alternatives(current_rating, target_rating, current_scores)
            if not is_achievable
            else None
        )

        return RatingAdvisorResponse(
            current_rating=current_rating,
            target_rating=target_rating,
            is_achievable=is_achievable,
            confidence=confidence,
            current_scores=current_scores,
            target_scores=target_thresholds,
            rating_gaps=rating_gaps,
            problematic_scenes=problematic_scenes,
            recommended_actions=recommended_actions,
            summary=summary,
            estimated_effort=effort,
            alternative_targets=alternative_targets,
        )

    def _check_achievability(
        self,
        current: str,
        target: str,
        scores: Dict[str, float],
        thresholds: Dict[str, float],
    ) -> Tuple[bool, float]:
        current_idx = self.RATING_ORDER.index(current)
        target_idx = self.RATING_ORDER.index(target)

        if target_idx > current_idx:
            return False, 0.0

        if target_idx == current_idx:
            return True, 1.0

        violations = []
        for dim, threshold in thresholds.items():
            if scores.get(dim, 0) > threshold:
                excess = scores[dim] - threshold
                violations.append(excess)

        if not violations:
            return True, 1.0

        avg_violation = np.mean(violations)
        max_violation = max(violations)

        if max_violation > 0.5:
            confidence = 0.3
        elif max_violation > 0.3:
            confidence = 0.5
        elif avg_violation > 0.2:
            confidence = 0.7
        else:
            confidence = 0.9

        return True, confidence

    def _calculate_gaps(
        self, current: Dict[str, float], target: Dict[str, float], language: str
    ) -> List[RatingGap]:
        gaps = []

        for dim, target_val in target.items():
            current_val = current.get(dim, 0)
            gap = current_val - target_val

            if gap <= 0:
                continue

            if gap > 0.5:
                priority = "critical"
            elif gap > 0.3:
                priority = "high"
            elif gap > 0.15:
                priority = "medium"
            else:
                priority = "low"

            gaps.append(
                RatingGap(
                    dimension=self.DIMENSION_TRANSLATIONS[dim][language],
                    current_score=round(current_val, 3),
                    target_score=round(target_val, 3),
                    gap=round(gap, 3),
                    priority=priority,
                )
            )

        gaps.sort(key=lambda x: x.gap, reverse=True)
        return gaps

    def _identify_problematic_scenes(
        self, scenes: List[Dict], thresholds: Dict[str, float], language: str
    ) -> List[SceneIssue]:
        problematic = []

        for scene in scenes:
            issues = {}
            severity_score = 0

            for dim, threshold in thresholds.items():
                scene_val = scene.get(dim, 0)
                if scene_val > threshold:
                    excess = scene_val - threshold
                    issues[self.DIMENSION_TRANSLATIONS[dim][language]] = round(
                        excess, 3
                    )
                    severity_score += excess

            if not issues:
                continue

            if severity_score > 1.5:
                severity = "critical"
            elif severity_score > 0.8:
                severity = "high"
            elif severity_score > 0.4:
                severity = "medium"
            else:
                severity = "low"

            recommendations = self._generate_scene_recommendations(
                scene, issues, language
            )

            content = scene.get("content", "")[:200]

            problematic.append(
                SceneIssue(
                    scene_id=scene["scene_id"],
                    scene_number=scene["scene_number"],
                    content_preview=content,
                    issues=issues,
                    severity=severity,
                    recommendations=recommendations,
                )
            )

        problematic.sort(key=lambda x: sum(x.issues.values()), reverse=True)
        return problematic

    def _generate_scene_recommendations(
        self, scene: Dict, issues: Dict[str, float], language: str
    ) -> List[str]:
        recommendations = []

        templates = {
            "en": {
                "Violence": "Reduce or remove violent actions and combat descriptions",
                "Gore": "Remove graphic descriptions of injuries and blood",
                "Sexual Content": "Remove or tone down sexual scenes",
                "Nudity": "Remove nudity descriptions or make them implicit",
                "Profanity": "Replace profane language with milder alternatives",
                "Drugs": "Remove or reduce drug and alcohol references",
                "Child Risk": "Remove children from dangerous situations",
            },
            "ru": {
                "Насилие": "Уменьшить или удалить описания насилия и боевых действий",
                "Жестокость": "Убрать графические описания ранений и крови",
                "Сексуальный контент": "Удалить или смягчить сексуальные сцены",
                "Нагота": "Убрать описания наготы или сделать их косвенными",
                "Ненормативная лексика": "Заменить нецензурную лексику на более мягкие варианты",
                "Наркотики": "Убрать или уменьшить упоминания наркотиков и алкоголя",
                "Риск для детей": "Убрать детей из опасных ситуаций",
            },
        }

        for issue_dim in issues.keys():
            if issue_dim in templates[language]:
                recommendations.append(templates[language][issue_dim])

        return recommendations

    def _generate_recommendations(
        self,
        scenes: List[SceneIssue],
        gaps: List[RatingGap],
        language: str,
        script_text: str = "",
        current_rating: str = "",
        target_rating: str = "",
        all_scenes: List[Dict] = [],
    ) -> List[RecommendationAction]:
        actions = []

        actions.extend(
            self._generate_smart_recommendations(scenes, gaps, language, all_scenes)
        )

        critical_scenes = [s for s in scenes if s.severity in ["critical", "high"]]

        for scene in critical_scenes[:10]:
            max_issue = max(scene.issues.items(), key=lambda x: x[1])
            issue_dim, issue_val = max_issue

            if issue_val > 0.6:
                action_type = "remove_scene"
                difficulty = "easy"
                impact = min(issue_val * 1.2, 1.0)
                changes = self._translate(
                    "Remove entire scene", language, "Удалить сцену полностью"
                )
            elif issue_val > 0.3:
                action_type = "rewrite_scene"
                difficulty = "hard"
                impact = issue_val * 0.9
                changes = self._translate(
                    "Rewrite scene to reduce problematic content",
                    language,
                    "Переписать сцену, уменьшив проблемный контент",
                )
            else:
                action_type = "reduce_content"
                difficulty = "medium"
                impact = issue_val * 0.7
                changes = self._translate(
                    "Remove or tone down specific elements",
                    language,
                    "Убрать или смягчить отдельные элементы",
                )

            description = self._translate(
                f"Scene {scene.scene_number}: {', '.join(scene.recommendations[:2])}",
                language,
                f"Сцена {scene.scene_number}: {', '.join(scene.recommendations[:2])}",
            )

            actions.append(
                RecommendationAction(
                    action_type=action_type,
                    scene_id=scene.scene_id,
                    description=description,
                    impact_score=round(impact, 3),
                    category=issue_dim,
                    specific_changes=[changes],
                    difficulty=difficulty,
                )
            )

        actions.sort(key=lambda x: x.impact_score, reverse=True)
        return actions

    def _generate_summary(
        self,
        current: str,
        target: str,
        achievable: bool,
        gaps: List[RatingGap],
        num_scenes: int,
        language: str,
    ) -> str:
        if language == "ru":
            if not achievable:
                return f"Невозможно понизить рейтинг с {current} до {target}. Целевой рейтинг выше текущего."

            if current == target:
                return f"Сценарий уже имеет рейтинг {target}."

            gap_desc = ", ".join([f"{g.dimension} (↓{g.gap:.1%})" for g in gaps[:3]])
            return (
                f"Для достижения рейтинга {target} необходимо уменьшить: {gap_desc}. "
                f"Найдено {num_scenes} проблемных сцен. "
                f"Приоритетные изменения показаны в рекомендациях."
            )
        else:
            if not achievable:
                return f"Cannot lower rating from {current} to {target}. Target rating is higher than current."

            if current == target:
                return f"Script already has {target} rating."

            gap_desc = ", ".join([f"{g.dimension} (↓{g.gap:.1%})" for g in gaps[:3]])
            return (
                f"To achieve {target} rating, reduce: {gap_desc}. "
                f"Found {num_scenes} problematic scenes. "
                f"Priority changes shown in recommendations."
            )

    def _estimate_effort(self, scenes: List[SceneIssue], gaps: List[RatingGap]) -> str:
        critical_count = sum(1 for s in scenes if s.severity == "critical")
        high_count = sum(1 for s in scenes if s.severity == "high")
        critical_gaps = sum(1 for g in gaps if g.priority in ["critical", "high"])

        total_score = critical_count * 3 + high_count * 2 + critical_gaps * 2

        if total_score > 15:
            return "extensive"
        elif total_score > 10:
            return "significant"
        elif total_score > 5:
            return "moderate"
        else:
            return "minimal"

    def _suggest_alternatives(
        self, current: str, target: str, scores: Dict[str, float]
    ) -> List[str]:
        current_idx = self.RATING_ORDER.index(current)
        alternatives = []

        for i in range(current_idx - 1, -1, -1):
            rating = self.RATING_ORDER[i]
            if rating == target:
                continue

            thresholds = self.RATING_THRESHOLDS[rating]
            violations = sum(
                1 for dim, thresh in thresholds.items() if scores.get(dim, 0) > thresh
            )

            if violations <= 2:
                alternatives.append(rating)

        return alternatives[:2]

    def _generate_smart_recommendations(
        self,
        scenes: List[SceneIssue],
        gaps: List[RatingGap],
        language: str,
        all_scenes: List[Dict],
    ) -> List[RecommendationAction]:
        actions = []

        dimension_to_key = {
            v[language]: k for k, v in self.DIMENSION_TRANSLATIONS.items()
        }

        for scene in scenes[:15]:
            scene_data = next(
                (s for s in all_scenes if s.get("scene_number") == scene.scene_number),
                None,
            )

            if not scene_data:
                continue

            for issue_name, issue_val in sorted(
                scene.issues.items(), key=lambda x: x[1], reverse=True
            ):
                dim_key = dimension_to_key.get(issue_name, "")

                if not dim_key:
                    continue

                specific_recs = self._analyze_scene_content(
                    scene_data.get("content", ""), dim_key, issue_val, language
                )

                if specific_recs:
                    for rec in specific_recs[:2]:
                        actions.append(
                            RecommendationAction(
                                action_type=rec["type"],
                                scene_id=scene.scene_id,
                                description=rec["description"],
                                impact_score=rec["impact"],
                                category=issue_name,
                                specific_changes=rec["changes"],
                                difficulty=rec["difficulty"],
                            )
                        )

        return actions[:20]

    def _analyze_scene_content(
        self, content: str, dimension: str, severity: float, language: str
    ) -> List[Dict]:
        recs = []
        content_lower = content.lower()

        if dimension == "violence":
            violence_keywords = {
                "high": [
                    "убивает",
                    "murder",
                    "стреляет",
                    "shoot",
                    "удар",
                    "punch",
                    "бьет",
                    "hit",
                ],
                "medium": [
                    "дерутся",
                    "fight",
                    "атакует",
                    "attack",
                    "борьба",
                    "struggle",
                ],
                "low": ["угрожает", "threaten", "спор", "argue"],
            }

            for level, keywords in violence_keywords.items():
                if any(kw in content_lower for kw in keywords):
                    if level == "high" and severity > 0.5:
                        recs.append(
                            {
                                "type": "rewrite_scene",
                                "description": self._t(
                                    language,
                                    "Replace violent action with verbal conflict",
                                    "Заменить насилие на словесный конфликт",
                                ),
                                "impact": 0.85,
                                "changes": [
                                    self._t(
                                        language,
                                        "Convert physical fight to heated dialogue",
                                        "Превратить драку в напряженный диалог",
                                    )
                                ],
                                "difficulty": "medium",
                            }
                        )
                    else:
                        recs.append(
                            {
                                "type": "reduce_content",
                                "description": self._t(
                                    language,
                                    "Tone down violent descriptions",
                                    "Смягчить описания насилия",
                                ),
                                "impact": 0.6,
                                "changes": [
                                    self._t(
                                        language,
                                        "Make violence implied rather than explicit",
                                        "Сделать насилие косвенным, а не прямым",
                                    )
                                ],
                                "difficulty": "easy",
                            }
                        )

        elif dimension == "gore":
            gore_keywords = [
                "кровь",
                "blood",
                "рана",
                "wound",
                "труп",
                "corpse",
                "тело",
                "body",
            ]
            if any(kw in content_lower for kw in gore_keywords):
                recs.append(
                    {
                        "type": "modify_dialogue",
                        "description": self._t(
                            language,
                            "Remove graphic injury descriptions",
                            "Убрать графические описания ранений",
                        ),
                        "impact": 0.75,
                        "changes": [
                            self._t(
                                language,
                                "Cut to black or use off-screen action",
                                "Использовать затемнение или действие за кадром",
                            )
                        ],
                        "difficulty": "easy",
                    }
                )

        elif dimension == "sex_act":
            sex_keywords = [
                "секс",
                "sex",
                "занимаются любовью",
                "make love",
                "bed",
                "кровать",
            ]
            if any(kw in content_lower for kw in sex_keywords):
                recs.append(
                    {
                        "type": "rewrite_scene",
                        "description": self._t(
                            language,
                            "Make intimate scene implicit",
                            "Сделать интимную сцену косвенной",
                        ),
                        "impact": 0.9,
                        "changes": [
                            self._t(
                                language,
                                "Fade to black or show morning after",
                                "Затемнение или показ утра после",
                            )
                        ],
                        "difficulty": "easy",
                    }
                )

        elif dimension == "nudity":
            nudity_keywords = [
                "голый",
                "naked",
                "nude",
                "обнаженный",
                "раздевается",
                "undress",
            ]
            if any(kw in content_lower for kw in nudity_keywords):
                recs.append(
                    {
                        "type": "modify_dialogue",
                        "description": self._t(
                            language,
                            "Remove or obscure nudity",
                            "Убрать или скрыть наготу",
                        ),
                        "impact": 0.8,
                        "changes": [
                            self._t(
                                language,
                                "Use strategic camera angles or clothing",
                                "Использовать ракурсы камеры или одежду",
                            )
                        ],
                        "difficulty": "easy",
                    }
                )

        elif dimension == "profanity":
            profanity_patterns = re.findall(
                r"\b(fuck|shit|damn|hell|бля|хуй|пизд|ебать)\w*\b", content_lower
            )
            if profanity_patterns:
                count = len(profanity_patterns)
                recs.append(
                    {
                        "type": "modify_dialogue",
                        "description": self._t(
                            language,
                            f"Replace {count} profane word(s) with milder alternatives",
                            f"Заменить {count} нецензурных слов на более мягкие",
                        ),
                        "impact": min(0.6 + count * 0.05, 0.95),
                        "changes": [
                            self._t(
                                language,
                                "Use euphemisms or remove entirely",
                                "Использовать эвфемизмы или убрать полностью",
                            )
                        ],
                        "difficulty": "easy",
                    }
                )

        elif dimension == "drugs":
            drugs_keywords = [
                "наркотик",
                "drug",
                "кокаин",
                "cocaine",
                "героин",
                "heroin",
                "алкоголь",
                "alcohol",
                "пьет",
                "drink",
                "курит",
                "smoke",
            ]
            if any(kw in content_lower for kw in drugs_keywords):
                recs.append(
                    {
                        "type": "reduce_content",
                        "description": self._t(
                            language,
                            "Remove or reduce drug/alcohol references",
                            "Убрать или уменьшить упоминания наркотиков/алкоголя",
                        ),
                        "impact": 0.7,
                        "changes": [
                            self._t(
                                language,
                                "Show consequences negatively or remove usage",
                                "Показать негативные последствия или убрать употребление",
                            )
                        ],
                        "difficulty": "medium",
                    }
                )

        elif dimension == "child_risk":
            child_keywords = [
                "ребенок",
                "child",
                "дети",
                "children",
                "мальчик",
                "boy",
                "девочка",
                "girl",
                "ребёнок",
                "kid",
            ]
            danger_keywords = [
                "опасность",
                "danger",
                "ранен",
                "hurt",
                "испуган",
                "scared",
            ]

            has_child = any(kw in content_lower for kw in child_keywords)
            has_danger = any(kw in content_lower for kw in danger_keywords)

            if has_child and has_danger:
                recs.append(
                    {
                        "type": "rewrite_scene",
                        "description": self._t(
                            language,
                            "Remove children from dangerous situation",
                            "Убрать детей из опасной ситуации",
                        ),
                        "impact": 0.9,
                        "changes": [
                            self._t(
                                language,
                                "Replace child character with adult or move to safe location",
                                "Заменить ребенка на взрослого или переместить в безопасное место",
                            )
                        ],
                        "difficulty": "hard",
                    }
                )

        if severity > 0.7 and not recs:
            recs.append(
                {
                    "type": "remove_scene",
                    "description": self._t(
                        language,
                        "Consider removing this scene entirely",
                        "Рассмотрите возможность полного удаления сцены",
                    ),
                    "impact": 0.95,
                    "changes": [
                        self._t(
                            language,
                            "High severity issue with no easy fix",
                            "Высокая серьезность без простого решения",
                        )
                    ],
                    "difficulty": "easy",
                }
            )

        return recs

    def _t(self, language: str, en: str, ru: str) -> str:
        return ru if language == "ru" else en

    def _translate(self, en_text: str, language: str, ru_text: str) -> str:
        return ru_text if language == "ru" else en_text
