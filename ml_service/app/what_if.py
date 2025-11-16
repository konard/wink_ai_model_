import re
from typing import Dict, Any, List, Tuple, cast
from loguru import logger
from sentence_transformers import SentenceTransformer, util
import numpy as np

from .repair_pipeline import (
    parse_script_to_scenes,
    extract_scene_features,
    normalize_and_contextualize_scores,
    map_scores_to_rating,
)


class WhatIfAnalyzer:
    def __init__(self):
        logger.info("Initializing What-If Analyzer")
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        self.modification_patterns = {
            "remove_scenes": [
                r"убрать сцен[уы]?\s+(\d+)(?:\s*[-–—]\s*(\d+))?",
                r"удалить сцен[уы]?\s+(\d+)(?:\s*[-–—]\s*(\d+))?",
                r"без сцен[ыи]?\s+(\d+)(?:\s*[-–—]\s*(\d+))?",
                r"remove scene[s]?\s+(\d+)(?:\s*[-–—]\s*(\d+))?",
                r"delete scene[s]?\s+(\d+)(?:\s*[-–—]\s*(\d+))?",
            ],
            "reduce_violence": [
                r"заменить\s+.*?(драк[уи]|насилие|бой|убийств[оа]).*?на\s+(.*?)(?:\.|$|,)",
                r"смягчить\s+.*?(драк[уи]|насилие|бой)",
                r"убрать\s+.*?(драк[уи]|насилие|бой|убийств[оа]|оружи)",
                r"replace\s+.*?(fight|violence|battle|killing|weapon).*?with\s+(.*?)(?:\.|$|,)",
                r"reduce\s+.*?(fight|violence|battle|weapon)",
                r"remove\s+.*?(fight|violence|battle|killing|weapon)",
                r"без\s+.*?(драк|насил|бо[ея]|оружи)",
                r"no\s+.*?(fight|violence|weapon)",
            ],
            "reduce_profanity": [
                r"убрать\s+мат",
                r"удалить\s+мат",
                r"без\s+мат[аи]",
                r"убрать\s+.*?(?:мат|ненормативн|нецензурн)",
                r"у\s+персонаж[ае]\s+(\w+)",
                r"remove\s+profanity",
                r"remove\s+swearing",
                r"no\s+profanity",
                r"remove\s+all\s+profanity",
            ],
            "reduce_gore": [
                r"убрать\s+кров[ьи]",
                r"без\s+кров[ии]",
                r"смягчить\s+.*?кров[ьи]",
                r"убрать\s+.*?увечи",
                r"без\s+.*?(?:крови|увечи)",
                r"remove\s+blood",
                r"remove\s+gore",
                r"reduce\s+gore",
                r"no\s+blood",
            ],
            "reduce_sexual": [
                r"убрать\s+.*?(секс|интим|наг)",
                r"без\s+.*?(секс|интим|наг)",
                r"смягчить\s+.*?(секс|интим)",
                r"remove\s+.*?(sex|nudity|intimate|sexual)",
                r"reduce\s+.*?(sex|sexual)",
                r"no\s+.*?(sex|sexual)",
            ],
            "reduce_drugs": [
                r"убрать\s+.*?(?:наркотик|алкоголь|курен)",
                r"без\s+.*?(?:наркотик|алкоголь|курен)",
                r"remove\s+.*?(?:drug|alcohol|smoking)",
                r"no\s+.*?(?:drug|alcohol|smoking)",
            ],
        }

        self.context_examples = {
            "replace_violence_verbal": [
                "verbal confrontation without physical violence",
                "heated argument instead of fight",
                "словесный конфликт вместо драки",
                "напряженный спор вместо боя",
            ],
            "replace_violence_mild": [
                "stylized action without graphic violence",
                "cartoon-style action sequence",
                "стилизованный экшн без графического насилия",
                "мультяшный стиль боевых сцен",
            ],
        }

    def analyze_modification_request(self, request: str) -> Dict[str, Any]:
        """Parse user's what-if request and extract modification intent."""
        request_lower = request.lower()
        modifications = {
            "remove_scenes": [],
            "reduce_violence": False,
            "reduce_profanity": False,
            "reduce_gore": False,
            "reduce_sexual": False,
            "reduce_drugs": False,
            "violence_replacement": None,
        }

        for pattern_type, patterns in self.modification_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, request_lower, re.I | re.U)
                if match:
                    if pattern_type == "remove_scenes":
                        start_scene = int(match.group(1))
                        end_scene = (
                            int(match.group(2)) if match.group(2) else start_scene
                        )
                        scene_list = cast(List[int], modifications["remove_scenes"])
                        scene_list.extend(range(start_scene, end_scene + 1))
                    elif pattern_type == "reduce_violence":
                        modifications["reduce_violence"] = True
                        if match.lastindex and match.lastindex >= 2:
                            replacement = match.group(match.lastindex).strip()
                            if replacement:
                                modifications["violence_replacement"] = replacement
                    elif pattern_type == "reduce_profanity":
                        modifications["reduce_profanity"] = True
                    elif pattern_type == "reduce_gore":
                        modifications["reduce_gore"] = True
                    elif pattern_type == "reduce_sexual":
                        modifications["reduce_sexual"] = True
                    elif pattern_type == "reduce_drugs":
                        modifications["reduce_drugs"] = True

        replacement = modifications["violence_replacement"]
        if replacement and isinstance(replacement, str):
            verbal_sim = self._get_max_similarity(
                replacement, self.context_examples["replace_violence_verbal"]
            )
            mild_sim = self._get_max_similarity(
                replacement, self.context_examples["replace_violence_mild"]
            )

            if verbal_sim > 0.5:
                modifications["violence_replacement_type"] = "verbal"
            elif mild_sim > 0.5:
                modifications["violence_replacement_type"] = "mild"
            else:
                modifications["violence_replacement_type"] = "mild"

        return modifications

    def _get_max_similarity(self, text: str, examples: List[str]) -> float:
        """Calculate maximum semantic similarity between text and examples."""
        text_emb = self.embedder.encode([text], convert_to_numpy=True)[0]
        example_embs = self.embedder.encode(examples, convert_to_numpy=True)
        similarities = util.cos_sim(text_emb, example_embs)[0]
        return float(similarities.max())

    def apply_modifications(
        self, original_text: str, modifications: Dict[str, Any]
    ) -> Tuple[str, List[str]]:
        """Apply modifications to script text and return modified text + changes description."""
        scenes = parse_script_to_scenes(original_text)
        changes_description = []

        if modifications["remove_scenes"]:
            scenes_to_remove = set(modifications["remove_scenes"])
            original_count = len(scenes)
            scenes = [s for s in scenes if s["scene_id"] not in scenes_to_remove]
            removed_count = original_count - len(scenes)

            if removed_count > 0:
                changes_description.append(
                    f"Removed {removed_count} scene(s): {sorted(list(scenes_to_remove))}"
                )

            for idx, scene in enumerate(scenes):
                scene["scene_id"] = idx

        modified_scenes = []
        for scene in scenes:
            scene_text = scene["text"]

            if modifications["reduce_violence"]:
                replacement_type = modifications.get(
                    "violence_replacement_type", "mild"
                )
                scene_text, _ = self._reduce_violence_in_text(
                    scene_text, replacement_type
                )

            if modifications["reduce_profanity"]:
                scene_text, _ = self._reduce_profanity_in_text(scene_text)

            if modifications["reduce_gore"]:
                scene_text, _ = self._reduce_gore_in_text(scene_text)

            if modifications["reduce_sexual"]:
                scene_text, _ = self._reduce_sexual_in_text(scene_text)

            if modifications["reduce_drugs"]:
                scene_text, _ = self._reduce_drugs_in_text(scene_text)

            scene["text"] = scene_text
            modified_scenes.append(scene)

        if modifications["reduce_violence"]:
            changes_description.append("Reduced violence intensity across all scenes")
        if modifications["reduce_profanity"]:
            changes_description.append("Removed profanity throughout the script")
        if modifications["reduce_gore"]:
            changes_description.append("Reduced graphic gore and blood descriptions")
        if modifications["reduce_sexual"]:
            changes_description.append("Reduced sexual content and nudity")
        if modifications["reduce_drugs"]:
            changes_description.append("Reduced drug and alcohol references")

        modified_text = "\n\n".join([s["text"] for s in modified_scenes])
        return modified_text, changes_description

    def _reduce_violence_in_text(
        self, text: str, replacement_type: str = "mild"
    ) -> Tuple[str, bool]:
        """Reduce violence in text by replacing violent words with milder alternatives."""
        modified = False

        violence_replacements = {
            "kill": "confront",
            "shoot": "point at",
            "stab": "threaten",
            "murder": "argue with",
            "attack": "approach",
            "beating": "pushing",
            "fight": "argue" if replacement_type == "verbal" else "scuffle",
            "автомат": "устройство",
            "винтовка": "инструмент",
            "пистолет": "предмет",
            "оружие": "предмет",
            "gun": "device",
            "rifle": "tool",
            "weapon": "item",
            "убить": "противостоять",
            "убийство": "конфликт",
            "стрелять": "направить на",
            "зарезать": "угрожать",
            "атаковать": "приблизиться",
            "избиение": "толкание",
            "драка": "спор" if replacement_type == "verbal" else "потасовка",
            "бьет": "толкает",
            "ударил": "подтолкнул",
            "ломает": "скручивает",
            "broke": "twisted",
            "smashed": "pushed",
            "crushed": "squeezed",
        }

        for violent_word, replacement in violence_replacements.items():
            pattern = r"\b" + re.escape(violent_word) + r"\w*"
            if re.search(pattern, text, re.I):
                text = re.sub(pattern, replacement, text, flags=re.I)
                modified = True

        return text, modified

    def _reduce_profanity_in_text(self, text: str) -> Tuple[str, bool]:
        """Remove profanity from text."""
        modified = False

        profanity_patterns = [
            (r"\bfuck\w*\b", "darn", re.I),
            (r"\bshit\b", "crap", re.I),
            (r"\bmotherfucker\b", "jerk", re.I),
            (r"\bbitch\b", "witch", re.I),
            (r"\basshole\b", "idiot", re.I),
            (r"\bблядь\b", "черт", re.I),
            (r"\bбля\b", "блин", re.I),
            (r"\bсука\b", "зараза", re.I),
            (r"\bхуй\w*\b", "черт", re.I),
            (r"\bпизд\w*\b", "черт", re.I),
            (r"\bебать\b", "черт", re.I),
            (r"\bебал\w*\b", "черт", re.I),
            (r"\bдерьм\w*\b", "ерунда", re.I),
            (r"\bговн\w*\b", "ерунда", re.I),
        ]

        for pattern, replacement, flags in profanity_patterns:
            if re.search(pattern, text, flags):
                text = re.sub(pattern, replacement, text, flags=flags)
                modified = True

        return text, modified

    def _reduce_gore_in_text(self, text: str) -> Tuple[str, bool]:
        """Reduce gore descriptions in text."""
        modified = False

        gore_replacements = {
            "blood": "mark",
            "bloody": "marked",
            "bleeding": "injured",
            "wound": "injury",
            "guts": "injury",
            "dismember": "injured",
            "gore": "impact",
            "mutilate": "harm",
            "кровь": "след",
            "кровавый": "помеченный",
            "кровоточ": "ранен",
            "рана": "повреждение",
            "кишки": "повреждение",
            "увечь": "поврежд",
            "изуродован": "поврежден",
            "расчленен": "поврежден",
            "брызга": "полет",
            "текла": "появилась",
            "пролилась": "образовалась",
        }

        for gore_word, replacement in gore_replacements.items():
            pattern = r"\b" + re.escape(gore_word) + r"\w*"
            if re.search(pattern, text, re.I):
                text = re.sub(pattern, replacement, text, flags=re.I)
                modified = True

        return text, modified

    def _reduce_sexual_in_text(self, text: str) -> Tuple[str, bool]:
        """Reduce sexual content in text."""
        modified = False

        sexual_patterns = [
            (r"\brape\b", "assault", re.I),
            (r"\bsex scene\b", "romantic scene", re.I),
            (r"\bnaked\b", "undressed", re.I),
            (r"\bnude\b", "unclothed", re.I),
            (r"\bизнасилов\w*\b", "напад", re.I),
            (r"\bсексуальн\w*\b", "романтическ", re.I),
            (r"\bголый\b", "раздетый", re.I),
            (r"\bголая\b", "раздетая", re.I),
        ]

        for pattern, replacement, flags in sexual_patterns:
            if re.search(pattern, text, flags):
                text = re.sub(pattern, replacement, text, flags=flags)
                modified = True

        return text, modified

    def _reduce_drugs_in_text(self, text: str) -> Tuple[str, bool]:
        """Reduce drug references in text."""
        modified = False

        drug_patterns = [
            (r"\bheroin\b", "substance", re.I),
            (r"\bcocaine\b", "substance", re.I),
            (r"\bmarijuana\b", "substance", re.I),
            (r"\bгероин\b", "вещество", re.I),
            (r"\bкокаин\b", "вещество", re.I),
            (r"\bмарихуан\w*\b", "вещество", re.I),
        ]

        for pattern, replacement, flags in drug_patterns:
            if re.search(pattern, text, flags):
                text = re.sub(pattern, replacement, text, flags=flags)
                modified = True

        return text, modified

    def simulate_what_if(self, original_text: str, user_request: str) -> Dict[str, Any]:
        """Simulate what-if scenario and return rating comparison."""
        logger.info(f"Processing what-if request: {user_request}")

        original_result = self._analyze_script(original_text)

        modifications = self.analyze_modification_request(user_request)
        modified_text, changes = self.apply_modifications(original_text, modifications)

        modified_result = self._analyze_script(modified_text)

        explanation = self._generate_explanation(
            original_result, modified_result, changes, modifications
        )

        return {
            "original_rating": original_result["rating"],
            "modified_rating": modified_result["rating"],
            "original_scores": original_result["scores"],
            "modified_scores": modified_result["scores"],
            "changes_applied": changes,
            "explanation": explanation,
            "rating_changed": original_result["rating"] != modified_result["rating"],
        }

    def _analyze_script(self, text: str) -> Dict[str, Any]:
        """Analyze script and return rating with scores."""
        scenes = parse_script_to_scenes(text)

        features = []
        for scene in scenes:
            feat = extract_scene_features(scene["text"])
            features.append(feat)

        scores = [normalize_and_contextualize_scores(f) for f in features]

        score_keys = [
            "violence",
            "gore",
            "sex_act",
            "nudity",
            "profanity",
            "drugs",
            "child_risk",
        ]
        agg = {}

        for k in score_keys:
            values = [s[k] for s in scores]
            max_val = float(np.max(values))
            p95_val = float(np.percentile(values, 95))
            p90_val = float(np.percentile(values, 90))

            if k in ["violence", "gore"]:
                agg[k] = max_val * 0.7 + p95_val * 0.3
            elif k in ["sex_act", "nudity", "child_risk"]:
                agg[k] = max_val * 0.85 + p90_val * 0.15
            else:
                agg[k] = float(np.percentile(values, 90))

        all_excerpts: Dict[str, List[Any]] = {
            "violence": [],
            "gore": [],
            "sex": [],
            "nudity": [],
            "profanity": [],
            "drugs": [],
        }
        for s in scores:
            for key in all_excerpts.keys():
                all_excerpts[key].extend(s["excerpts"][key])

        limited_excerpts = {k: v[:5] for k, v in all_excerpts.items()}
        agg["excerpts"] = cast(Any, limited_excerpts)

        rating_info = map_scores_to_rating(agg)

        return {
            "rating": rating_info["rating"],
            "reasons": rating_info["reasons"],
            "scores": {k: round(agg[k], 3) for k in score_keys},
            "total_scenes": len(scenes),
        }

    def _generate_explanation(
        self,
        original: Dict[str, Any],
        modified: Dict[str, Any],
        changes: List[str],
        modifications: Dict[str, Any],
    ) -> str:
        """Generate human-readable explanation of rating change."""
        if original["rating"] == modified["rating"]:
            explanation = (
                f"Рейтинг остался прежним: {original['rating']}. "
                f"Внесенные изменения ({', '.join(changes)}) "
                f"не были достаточно значительными для изменения возрастного рейтинга."
            )

            score_changes = []
            for key in ["violence", "gore", "sex_act", "nudity", "profanity", "drugs"]:
                orig_score = original["scores"].get(key, 0)
                mod_score = modified["scores"].get(key, 0)
                diff = mod_score - orig_score

                if abs(diff) > 0.05:
                    direction = "увеличился" if diff > 0 else "снизился"
                    score_changes.append(f"{key}: {direction} на {abs(diff):.2f}")

            if score_changes:
                explanation += f" Изменения в оценках: {', '.join(score_changes)}."
        else:
            direction = (
                "повысился" if modified["rating"] > original["rating"] else "понизился"
            )
            explanation = (
                f"Рейтинг {direction}: было {original['rating']}, стало {modified['rating']}. "
                f"Изменения: {', '.join(changes)}. "
            )

            key_changes = []
            for key in ["violence", "gore", "sex_act", "nudity", "profanity", "drugs"]:
                orig_score = original["scores"].get(key, 0)
                mod_score = modified["scores"].get(key, 0)
                diff = mod_score - orig_score

                if abs(diff) > 0.1:
                    direction = "увеличен" if diff > 0 else "снижен"
                    key_changes.append(
                        f"{key} {direction} с {orig_score:.2f} до {mod_score:.2f}"
                    )

            if key_changes:
                explanation += f"Ключевые изменения: {', '.join(key_changes)}."

        return explanation

    def generate_smart_suggestions(
        self,
        script_text: str,
        current_scores: Dict[str, float] | None = None,
        language: str = "ru",
        max_suggestions: int = 8,
    ) -> Dict[str, Any]:
        """Generate smart, personalized suggestions based on script analysis."""
        logger.info("Generating smart suggestions for script")

        # Analyze script if scores not provided
        if current_scores is None:
            analysis = self._analyze_script(script_text)
            current_scores = analysis["scores"]
            current_rating = analysis["rating"]
            total_scenes = analysis["total_scenes"]
        else:
            # Quick analysis for rating
            analysis = self._analyze_script(script_text)
            current_rating = analysis["rating"]
            total_scenes = analysis["total_scenes"]

        # Parse scenes for detailed analysis
        scenes = parse_script_to_scenes(script_text)

        suggestions = []

        # Define thresholds and icons
        category_config = {
            "violence": {
                "threshold": 0.3,
                "icon": "💬",
                "ru": "насилие",
                "en": "violence",
            },
            "gore": {"threshold": 0.25, "icon": "🩹", "ru": "кровь", "en": "gore"},
            "profanity": {
                "threshold": 0.3,
                "icon": "🤐",
                "ru": "мат",
                "en": "profanity",
            },
            "sex_act": {
                "threshold": 0.2,
                "icon": "🔞",
                "ru": "секс",
                "en": "sexual content",
            },
            "nudity": {"threshold": 0.2, "icon": "👗", "ru": "нагота", "en": "nudity"},
            "drugs": {"threshold": 0.2, "icon": "💊", "ru": "наркотики", "en": "drugs"},
        }

        # Analyze each category
        for category, config in category_config.items():
            score = current_scores.get(category, 0)

            if score > config["threshold"]:
                # Find problematic scenes
                affected_scenes = []
                for scene in scenes:
                    features = extract_scene_features(scene["text"])
                    normalized = normalize_and_contextualize_scores(features)
                    if normalized.get(category, 0) > 0.5:
                        affected_scenes.append(scene["scene_id"])

                # Calculate priority (higher score = higher priority)
                priority = min(10, int(score * 10) + 2)
                confidence = min(1.0, score * 1.2)

                # Generate suggestion text based on language
                if language == "ru":
                    category_name = config["ru"]
                    if len(affected_scenes) > 0:
                        if len(affected_scenes) == 1:
                            suggestion_text = (
                                f"убрать {category_name} в сцене {affected_scenes[0]}"
                            )
                        elif len(affected_scenes) <= 3:
                            scenes_str = ", ".join(map(str, affected_scenes[:3]))
                            suggestion_text = (
                                f"убрать {category_name} в сценах {scenes_str}"
                            )
                        else:
                            suggestion_text = f"смягчить {category_name} ({len(affected_scenes)} сцен)"
                    else:
                        suggestion_text = f"убрать {category_name}"

                    reasoning = f"Уровень {category_name}: {int(score * 100)}% - выше нормы для более низкого рейтинга"
                else:
                    category_name = config["en"]
                    if len(affected_scenes) > 0:
                        if len(affected_scenes) == 1:
                            suggestion_text = (
                                f"remove {category_name} in scene {affected_scenes[0]}"
                            )
                        elif len(affected_scenes) <= 3:
                            scenes_str = ", ".join(map(str, affected_scenes[:3]))
                            suggestion_text = (
                                f"remove {category_name} in scenes {scenes_str}"
                            )
                        else:
                            suggestion_text = f"reduce {category_name} ({len(affected_scenes)} scenes)"
                    else:
                        suggestion_text = f"remove {category_name}"

                    reasoning = f"{category_name.capitalize()} level: {int(score * 100)}% - above threshold for lower rating"

                suggestions.append(
                    {
                        "text": suggestion_text,
                        "category": category,
                        "icon": config["icon"],
                        "priority": priority,
                        "confidence": confidence,
                        "affected_scenes": affected_scenes[:5],  # Limit to 5 scenes
                        "reasoning": reasoning,
                    }
                )

        # Sort by priority (descending)
        suggestions.sort(key=lambda x: (-x["priority"], -x["confidence"]))

        # Limit to max_suggestions
        suggestions = suggestions[:max_suggestions]

        # Generate summary
        if language == "ru":
            high_scores = [k for k, v in current_scores.items() if v > 0.5]
            if high_scores:
                summary = f"Обнаружены высокие показатели: {', '.join(high_scores)}. Рекомендуется смягчить контент для получения более низкого рейтинга."
            else:
                summary = f"Сценарий имеет рейтинг {current_rating}. Предложены улучшения для снижения возрастных ограничений."
        else:
            high_scores = [k for k, v in current_scores.items() if v > 0.5]
            if high_scores:
                summary = f"High levels detected: {', '.join(high_scores)}. Consider reducing content for lower rating."
            else:
                summary = f"Script rated {current_rating}. Suggestions provided to reduce age restrictions."

        return {
            "suggestions": suggestions,
            "analysis_summary": summary,
            "current_rating": current_rating,
            "total_scenes": total_scenes,
        }


_analyzer: WhatIfAnalyzer | None = None


def get_what_if_analyzer() -> WhatIfAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = WhatIfAnalyzer()
    return _analyzer
