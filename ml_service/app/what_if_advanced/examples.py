"""
Examples of using the Advanced What-If Analyzer.
These can be run as tests or reference for API usage.
"""

EXAMPLE_SCRIPT = """INT. WAREHOUSE - NIGHT

JOHN, a tough detective, enters the dark warehouse. He pulls out his gun.

JOHN
Where the fuck are you hiding?

Suddenly, VILLAIN emerges from shadows with a knife.

VILLAIN
You'll never take me alive!

They FIGHT violently. Blood splatters everywhere. John SHOOTS the villain.

EXT. STREET - DAY

MARY walks down the street, enjoying the sunshine.

MARY
What a beautiful day!

INT. BAR - NIGHT

JOHN sits at the bar, drinking whiskey heavily.

BARTENDER
Another one?

JOHN
Keep them coming.
"""


EXAMPLE_1_REDUCE_VIOLENCE = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "reduce_violence",
            "params": {
                "content_types": ["violence", "gore"],
            }
        }
    ],
    "use_llm": False,
    "preserve_structure": True,
}


EXAMPLE_2_REDUCE_PROFANITY = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "reduce_profanity",
            "params": {
                "content_types": ["profanity"],
            }
        }
    ],
}


EXAMPLE_3_REMOVE_SCENES = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "remove_scenes",
            "params": {
                "scene_ids": [0, 2],
            }
        }
    ],
}


EXAMPLE_4_REMOVE_BY_TYPE = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "remove_scenes",
            "params": {
                "scene_types": ["action"],
            }
        }
    ],
}


EXAMPLE_5_RENAME_CHARACTER = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "modify_character",
            "params": {
                "action": "rename",
                "character_name": "JOHN",
                "new_name": "JACK",
            }
        }
    ],
}


EXAMPLE_6_REMOVE_CHARACTER = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "modify_character",
            "params": {
                "action": "remove",
                "character_name": "VILLAIN",
                "remove_scenes": True,
            }
        }
    ],
}


EXAMPLE_7_MULTIPLE_MODS = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "reduce_violence",
            "params": {
                "content_types": ["violence", "gore"],
            }
        },
        {
            "type": "reduce_profanity",
            "params": {
                "content_types": ["profanity"],
            }
        },
        {
            "type": "reduce_drugs",
            "params": {
                "content_types": ["drugs"],
            }
        },
    ],
}


EXAMPLE_8_CUSTOM_REPLACEMENTS = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "reduce_violence",
            "params": {
                "content_types": [],
                "custom_replacements": {
                    "gun": "badge",
                    "knife": "document",
                    "fight": "argue",
                }
            }
        }
    ],
}


EXAMPLE_9_TARGET_CHARACTERS = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "reduce_profanity",
            "params": {
                "content_types": ["profanity"],
                "target_characters": ["JOHN"],
            }
        }
    ],
}


EXAMPLE_10_LLM_REWRITE = {
    "script_text": EXAMPLE_SCRIPT,
    "modifications": [
        {
            "type": "llm_rewrite",
            "params": {
                "instruction": "Rewrite the violent confrontation as a tense verbal argument instead",
                "scope": [0],
                "preserve_style": True,
            }
        }
    ],
    "use_llm": True,
    "llm_provider": "openai",
}


ALL_EXAMPLES = {
    "reduce_violence": EXAMPLE_1_REDUCE_VIOLENCE,
    "reduce_profanity": EXAMPLE_2_REDUCE_PROFANITY,
    "remove_scenes": EXAMPLE_3_REMOVE_SCENES,
    "remove_by_type": EXAMPLE_4_REMOVE_BY_TYPE,
    "rename_character": EXAMPLE_5_RENAME_CHARACTER,
    "remove_character": EXAMPLE_6_REMOVE_CHARACTER,
    "multiple_modifications": EXAMPLE_7_MULTIPLE_MODS,
    "custom_replacements": EXAMPLE_8_CUSTOM_REPLACEMENTS,
    "target_characters": EXAMPLE_9_TARGET_CHARACTERS,
    "llm_rewrite": EXAMPLE_10_LLM_REWRITE,
}


def print_example(name: str):
    """Print an example request."""
    import json
    print(f"\n{'='*60}")
    print(f"EXAMPLE: {name}")
    print(f"{'='*60}")
    print(json.dumps(ALL_EXAMPLES[name], indent=2))


if __name__ == "__main__":
    for name in ALL_EXAMPLES:
        print_example(name)
