import os
from typing import List, Dict, Optional
import json
from openai import OpenAI
from anthropic import Anthropic

from .schemas import SceneIssue


class LLMRatingAdvisor:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None

        if os.getenv("OPENAI_API_KEY"):
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if os.getenv("ANTHROPIC_API_KEY"):
            self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def enhance_recommendations(
        self,
        script_excerpt: str,
        problematic_scenes: List[SceneIssue],
        current_rating: str,
        target_rating: str,
        language: str = "en",
    ) -> List[Dict]:
        if not self.openai_client and not self.anthropic_client:
            return []

        prompt = self._build_prompt(
            script_excerpt, problematic_scenes, current_rating, target_rating, language
        )

        try:
            if self.openai_client:
                response = self._call_openai(prompt)
            elif self.anthropic_client:
                response = self._call_anthropic(prompt)
            else:
                return []

            return self._parse_llm_response(response)
        except Exception:
            return []

    def generate_rewrite_suggestions(
        self,
        scene_content: str,
        issues: Dict[str, float],
        target_rating: str,
        language: str = "en",
    ) -> Optional[str]:
        if not self.openai_client and not self.anthropic_client:
            return None

        prompt = self._build_rewrite_prompt(
            scene_content, issues, target_rating, language
        )

        try:
            if self.openai_client:
                return self._call_openai(prompt, temperature=0.7)
            elif self.anthropic_client:
                return self._call_anthropic(prompt, temperature=0.7)
        except Exception:
            return None

    def _build_prompt(
        self,
        script_excerpt: str,
        scenes: List[SceneIssue],
        current: str,
        target: str,
        language: str,
    ) -> str:
        if language == "ru":
            return f"""Ты эксперт по возрастным рейтингам фильмов. Проанализируй сценарий и дай конкретные рекомендации.

Текущий рейтинг: {current}
Целевой рейтинг: {target}

Проблемные сцены:
{self._format_scenes_ru(scenes[:5])}

Дай 5-7 конкретных, практических рекомендаций в формате JSON:
[
  {{
    "action": "remove_scene|reduce_content|modify_dialogue|rewrite_scene",
    "scene_number": номер_сцены,
    "reason": "почему это важно",
    "specific_change": "что именно изменить",
    "impact": "ожидаемый эффект",
    "difficulty": "easy|medium|hard"
  }}
]

Отвечай только JSON массивом."""
        else:
            return f"""You are a film rating expert. Analyze the script and provide specific recommendations.

Current rating: {current}
Target rating: {target}

Problematic scenes:
{self._format_scenes_en(scenes[:5])}

Provide 5-7 specific, actionable recommendations in JSON format:
[
  {{
    "action": "remove_scene|reduce_content|modify_dialogue|rewrite_scene",
    "scene_number": scene_number,
    "reason": "why this is important",
    "specific_change": "what exactly to change",
    "impact": "expected effect",
    "difficulty": "easy|medium|hard"
  }}
]

Respond with JSON array only."""

    def _build_rewrite_prompt(
        self, scene: str, issues: Dict[str, float], target: str, language: str
    ) -> str:
        issue_list = ", ".join(issues.keys())

        if language == "ru":
            return f"""Перепиши эту сцену для рейтинга {target}, уменьшив: {issue_list}

Оригинальная сцена:
{scene}

Требования:
- Сохрани сюжет и смысл
- Убери/смягчи проблемный контент
- Сохрани формат сценария
- Сделай естественно

Переписанная сцена:"""
        else:
            return f"""Rewrite this scene for {target} rating, reducing: {issue_list}

Original scene:
{scene}

Requirements:
- Preserve plot and meaning
- Remove/soften problematic content
- Maintain screenplay format
- Keep it natural

Rewritten scene:"""

    def _format_scenes_ru(self, scenes: List[SceneIssue]) -> str:
        lines = []
        for scene in scenes:
            issues = ", ".join([f"{k} ({v:.2f})" for k, v in scene.issues.items()])
            lines.append(
                f"Сцена {scene.scene_number}: {issues}\n{scene.content_preview[:150]}..."
            )
        return "\n\n".join(lines)

    def _format_scenes_en(self, scenes: List[SceneIssue]) -> str:
        lines = []
        for scene in scenes:
            issues = ", ".join([f"{k} ({v:.2f})" for k, v in scene.issues.items()])
            lines.append(
                f"Scene {scene.scene_number}: {issues}\n{scene.content_preview[:150]}..."
            )
        return "\n\n".join(lines)

    def _call_openai(self, prompt: str, temperature: float = 0.3) -> str:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=2000,
        )
        return response.choices[0].message.content

    def _call_anthropic(self, prompt: str, temperature: float = 0.3) -> str:
        response = self.anthropic_client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _parse_llm_response(self, response: str) -> List[Dict]:
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            recommendations = json.loads(response)

            if isinstance(recommendations, list):
                return recommendations
            return []
        except Exception:
            return []
