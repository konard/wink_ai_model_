# Advanced What-If Analyzer

ML-powered script modification analyzer with intelligent entity extraction, scene classification, and flexible modification strategies.

## Features

### Core Capabilities

- **Entity Extraction (NER)**: Automatically identify characters, locations, and objects
- **Scene Classification**: Zero-shot classification into action, dialogue, emotional, suspense, etc.
- **Plugin Architecture**: Extensible modification strategies
- **LLM Integration**: Optional LLM-based intelligent rewriting (OpenAI, Anthropic)
- **Structured API**: JSON-based precise control over modifications

### Modification Strategies

1. **Scene Removal** - Remove scenes by ID, type, characters, or location
2. **Content Reduction** - Reduce violence, profanity, gore, sexual content, drugs
3. **Character-Focused** - Modify, remove, or rename specific characters
4. **LLM Rewrite** - Context-aware intelligent scene rewriting

## API Usage

### Basic Example (No LLM)

```json
POST /what_if_advanced

{
  "script_text": "INT. WAREHOUSE - NIGHT\n\nJOHN pulls out a gun...",
  "modifications": [
    {
      "type": "reduce_violence",
      "params": {
        "content_types": ["violence"],
        "scope": [0, 1, 2]
      }
    }
  ],
  "use_llm": false,
  "preserve_structure": true
}
```

### Advanced Example (With LLM)

```json
{
  "script_text": "...",
  "modifications": [
    {
      "type": "llm_rewrite",
      "params": {
        "instruction": "Rewrite violent scenes as verbal confrontations",
        "preserve_style": true
      }
    }
  ],
  "use_llm": true,
  "llm_provider": "openai"
}
```

### Remove Specific Scenes

```json
{
  "script_text": "...",
  "modifications": [
    {
      "type": "remove_scenes",
      "params": {
        "scene_ids": [3, 5, 7]
      }
    }
  ]
}
```

### Remove Scenes by Type

```json
{
  "script_text": "...",
  "modifications": [
    {
      "type": "remove_scenes",
      "params": {
        "scene_types": ["action", "suspense"]
      }
    }
  ]
}
```

### Character-Focused Modifications

```json
{
  "script_text": "...",
  "modifications": [
    {
      "type": "modify_character",
      "params": {
        "action": "rename",
        "character_name": "JOHN",
        "new_name": "JACK"
      }
    }
  ]
}
```

### Multiple Modifications

```json
{
  "script_text": "...",
  "modifications": [
    {
      "type": "remove_scenes",
      "params": {"scene_ids": [0, 1]}
    },
    {
      "type": "reduce_violence",
      "params": {"content_types": ["violence", "gore"]}
    },
    {
      "type": "reduce_profanity",
      "params": {"content_types": ["profanity"]}
    }
  ]
}
```

## Response Format

```json
{
  "original_rating": "18+",
  "modified_rating": "16+",
  "original_scores": {
    "violence": 0.85,
    "profanity": 0.6,
    ...
  },
  "modified_scores": {
    "violence": 0.45,
    "profanity": 0.2,
    ...
  },
  "modifications_applied": [
    {
      "type": "reduce_violence",
      "metadata": {
        "total_replacements": 15,
        "scenes_modified": 3
      }
    }
  ],
  "entities_extracted": [
    {
      "type": "character",
      "name": "JOHN",
      "mentions": 25,
      "scenes": [0, 1, 2, 5, 7]
    }
  ],
  "scene_analysis": [
    {
      "scene_id": 0,
      "scene_type": "action",
      "characters": ["JOHN", "MARY"],
      "location": "WAREHOUSE",
      "summary": "INT. WAREHOUSE - NIGHT..."
    }
  ],
  "explanation": "Applied 1 modification(s)...",
  "modified_script": "...",
  "rating_changed": true
}
```

## Modification Types Reference

### `remove_scenes`
- `scene_ids`: List[int] - specific IDs
- `scene_types`: List[str] - by classified type
- `characters`: List[str] - scenes with these characters
- `locations`: List[str] - scenes in these locations

### `reduce_violence` / `reduce_profanity` / `reduce_gore` / `reduce_sexual` / `reduce_drugs`
- `content_types`: List[str] - which content to reduce
- `custom_replacements`: Dict[str, str] - custom word mappings
- `scope`: List[int] - scene IDs to apply to
- `target_characters`: List[str] - only modify these characters' scenes

### `modify_character`
- `action`: "remove" | "rename" | "modify_actions"
- `character_name`: str - target character
- `new_name`: str - for rename
- `remove_scenes`: bool - remove scenes or just lines
- `action_replacements`: Dict[str, str] - action word replacements

### `llm_rewrite`
- `instruction`: str - how to modify
- `scope`: List[int] - scene IDs
- `target_characters`: List[str] - focus on these characters
- `preserve_style`: bool - maintain writing style

## LLM Configuration

Set environment variables or pass at runtime:

```bash
OPENAI_API_KEY=your-key
# or
ANTHROPIC_API_KEY=your-key
```

Supported providers: `openai`, `anthropic`

## Architecture

```
what_if_advanced/
├── analyzer.py           # Main AdvancedWhatIfAnalyzer
├── schemas.py            # Pydantic models
├── analyzers/
│   ├── entity_extractor.py  # NER (spaCy or fallback)
│   └── scene_classifier.py  # Zero-shot classification
├── generators/
│   └── llm_generator.py     # LLM integration
└── strategies/
    ├── base.py              # Strategy pattern base
    ├── scene_removal.py
    ├── content_reduction.py
    ├── character_focused.py
    └── llm_rewrite.py
```

## Extending with Custom Strategies

```python
from ml_service.app.what_if_advanced.strategies import ModificationStrategy, get_strategy_registry

class MyCustomStrategy(ModificationStrategy):
    def can_handle(self, modification_type: str) -> bool:
        return modification_type == "my_custom_type"

    def apply(self, scenes, params, entities, **kwargs):
        # Your logic here
        return modified_scenes, metadata

    def validate_params(self, params):
        return True

# Register
get_strategy_registry().register(MyCustomStrategy())
```

## Dependencies

- `sentence-transformers` - scene classification
- `spacy` (optional) - better NER
- `openai` (optional) - OpenAI LLM
- `anthropic` (optional) - Anthropic LLM

Install spaCy model:
```bash
python -m spacy download en_core_web_sm
```
