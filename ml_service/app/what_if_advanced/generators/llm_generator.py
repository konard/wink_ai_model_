from typing import Optional, Dict, Any
from loguru import logger

try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class LLMGenerator:
    """Generate or rewrite content using LLMs."""

    def __init__(
        self,
        provider: str = "openai",
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model = model or self._get_default_model()

        if self.provider == "openai" and not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI package not installed. Install with: pip install openai"
            )
        if self.provider == "anthropic" and not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        self._init_client()

    def _get_default_model(self) -> str:
        """Get default model for provider."""
        defaults = {
            "openai": "gpt-4o-mini",
            "anthropic": "claude-3-5-haiku-20241022",
        }
        return defaults.get(self.provider, "gpt-4o-mini")

    def _init_client(self):
        """Initialize LLM client."""
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning(
                f"Unknown provider: {self.provider}, LLM generation disabled"
            )

    def rewrite_scene(
        self,
        scene_text: str,
        instruction: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Rewrite a scene according to instructions."""
        if not self.client:
            logger.warning("LLM client not available, returning original text")
            return scene_text

        prompt = self._build_rewrite_prompt(scene_text, instruction, context)

        try:
            if self.provider == "openai":
                return self._generate_openai(prompt)
            elif self.provider == "anthropic":
                return self._generate_anthropic(prompt)
            else:
                return scene_text
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return scene_text

    def _build_rewrite_prompt(
        self, scene_text: str, instruction: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Build prompt for scene rewriting."""
        prompt = f"""You are a professional screenplay editor. Rewrite the following scene according to the instruction.

INSTRUCTION: {instruction}

ORIGINAL SCENE:
{scene_text}

REQUIREMENTS:
- Maintain screenplay format and structure
- Keep character names and scene headings intact
- Apply the modification naturally and contextually
- Preserve the scene's narrative purpose
"""

        if context:
            if context.get("characters"):
                prompt += f"\n- Focus on characters: {', '.join(context['characters'])}"
            if context.get("preserve_style"):
                prompt += "\n- Maintain the original writing style and tone"

        prompt += "\n\nREWRITTEN SCENE:"
        return prompt

    def _generate_openai(self, prompt: str) -> str:
        """Generate using OpenAI API."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()

    def _generate_anthropic(self, prompt: str) -> str:
        """Generate using Anthropic API."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def generate_alternative_action(
        self,
        original_action: str,
        replacement_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate alternative action description."""
        instructions = {
            "reduce_violence": "Replace violent actions with non-violent alternatives while maintaining dramatic tension",
            "reduce_profanity": "Replace profane language with family-friendly alternatives",
            "reduce_sexual": "Replace sexual content with romantic but non-explicit alternatives",
            "soften_tone": "Rewrite to be less intense and more suitable for younger audiences",
        }

        instruction = instructions.get(
            replacement_type, "Rewrite to be more appropriate"
        )
        return self.rewrite_scene(original_action, instruction, context)
