import re
import numpy as np
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from loguru import logger

from .config import settings
from .metrics import MetricsTracker
from .structured_logger import log_feature_scores


VIOLENCE_WORDS = [
    r"\bkill\w*",
    r"\bshoot\w*",
    r"\bshot\b",
    r"\bstab\w*",
    r"\bknife\b",
    r"\bgun\w*",
    r"\bpistol\b",
    r"\brifle\b",
    r"\bexplod\w*",
    r"\bblast\w*",
    r"\battack\w*",
    r"\bbeat\w*",
    r"\bcorpse\b",
    r"\bdead\b",
    r"\bmurder\w*",
    r"\bviolence\b",
    r"\bterrorist\b",
    r"\bhostage\b",
    r"\brip(ped|s)? apart\b",
    r"\battack(ed|ing)?\b",
    r"\bbeat(s|en|ing)?\b",
    r"\bthug(s)?\b",
    r"\bterror\b",
    r"\bfight(ing)?\b",
    r"\bbattle(s|d)?\b",
    r"\bwar\b",
    r"\bshoot[- ]?out\b",
    r"\bexplosion\b",
    r"\bgrenade\b",
    r"\bcorps(e|es)?\b",
]

PSYCH_VIOLENCE = [
    "torture",
    "madness",
    "scream",
    "insane",
    "asylum",
    "terror",
    "panic",
    "suicide",
    "kill himself",
    "psychotic",
    "mental hospital",
]

PROFANITY = [r"\bfuck\b", r"\bshit\b", r"\bmotherfucker\b", r"\bbitch\b"]

DRUG_WORDS = [
    r"\bdrug(s)?\b",
    r"\bheroin\b",
    r"\bcocaine\b",
    r"\bmarijuana\b",
    r"\bpill(s)?\b",
    r"\bweed\b",
    r"\balcohol\b",
    r"\bdrunk\b",
    r"\bcigarette\b",
]

CHILD_PATTERN = [
    r"\bchild\b",
    r"\bkid(s)?\b",
    r"\bson\b",
    r"\bdaughter\b",
    r"\bteen(aged)?\b",
]

NUDITY_WORDS = [
    r"\bbra\b",
    r"\bpanty|panties\b",
    r"\bunderwear\b",
    r"\bnaked\b",
    r"\bskinny[- ]?dipping\b",
]

SEX_ACT_WORDS = [
    r"\brape\b",
    r"\bsexual\b",
    r"\bintercourse\b",
    r"\bsex scene\b",
    r"\bmolest\b",
    r"\borgasm\b",
    r"\bmake love\b",
    r"\bhaving sex\b",
    r"\bsexually\b",
]

GORE_STRICT = [
    "blood",
    "bloody",
    "bloodied",
    "bleeding",
    "corpse",
    "wound",
    "scar",
    "injur",
    "crash",
    "burn",
    "explod",
    "guts",
    "entrails",
    "brain",
    "dead body",
]

GORE_EXCLUDE = [
    "blood oath",
    "black ink",
    "blackened tongue",
    "ink dribbl",
    "ink is now",
]


class RatingPipeline:
    def __init__(self):
        logger.info(f"Loading model: {settings.model_name}")
        self.embedder = SentenceTransformer(settings.model_name)
        logger.info("Model loaded successfully")

    @staticmethod
    def count_matches(regex_list: List, text: str) -> int:
        count = 0
        for rx in regex_list:
            matches = rx.findall(text)
            if matches:
                count += len(matches)
        return count

    @staticmethod
    def parse_script_to_scenes(txt: str) -> List[Dict[str, Any]]:
        scenes = []
        parts = re.split(
            r"(?=(?:INT\.|EXT\.|scene_heading\s*:|SCENE HEADING\s*:))", txt, flags=re.I
        )

        if len(parts) < 5:
            return [{"scene_id": 0, "heading": "full_text", "text": txt}]

        idx = 0
        for p in parts:
            text = p.strip()
            if not text:
                continue
            heading_match = re.match(r"((?:INT\.|EXT\.).{0,120})", text, flags=re.I)
            heading = (
                heading_match.group(1).strip() if heading_match else f"scene_{idx}"
            )
            scenes.append({"scene_id": idx, "heading": heading, "text": text})
            idx += 1

        return scenes

    def scene_feature_vector(self, scene_text: str) -> Dict[str, float]:
        txt = scene_text.lower()

        psych = self.count_matches([re.compile(p, re.I) for p in PSYCH_VIOLENCE], txt)
        violence = self.count_matches(
            [re.compile(p, re.I) for p in VIOLENCE_WORDS], txt
        )
        profanity = self.count_matches([re.compile(p, re.I) for p in PROFANITY], txt)
        drugs = self.count_matches([re.compile(p, re.I) for p in DRUG_WORDS], txt)
        child_mentions = self.count_matches(
            [re.compile(p, re.I) for p in CHILD_PATTERN], txt
        )
        nudity = self.count_matches([re.compile(p, re.I) for p in NUDITY_WORDS], txt)
        sex_act = self.count_matches([re.compile(p, re.I) for p in SEX_ACT_WORDS], txt)

        gore = 0
        for g in GORE_STRICT:
            if g in txt and not any(ex in txt for ex in GORE_EXCLUDE):
                gore += 1

        HEROIC_KEYWORDS = [
            "superman",
            "batman",
            "wonder woman",
            "lex luthor",
            "krypton",
            "metropolis",
            "hero",
            "villain",
            "save",
            "rescue",
            "laser",
            "fly",
            "power",
            "superpower",
            "comic",
            "adventure",
        ]
        if any(word in txt for word in HEROIC_KEYWORDS):
            violence *= 0.6

        if violence > 0 and not re.search(
            r"\b(blood|gore|corpse|bleeding|wound|pain|scream)\b", txt
        ):
            violence *= 0.7

        length = max(1, len(txt.split()))
        return {
            "violence": violence + psych * 0.5,
            "gore": gore,
            "sex_act": sex_act,
            "nudity": nudity,
            "profanity": profanity,
            "drugs": drugs,
            "child_mentions": child_mentions,
            "length": length,
        }

    @staticmethod
    def normalize_scene_scores(f: Dict[str, float]) -> Dict[str, float]:
        L = f["length"]
        return {
            "violence": min(1.0, f["violence"] / (L / 150)),
            "gore": min(1.0, f["gore"] / 2.0),
            "sex_act": min(1.0, f["sex_act"]),
            "nudity": min(1.0, f["nudity"] / 3.0),
            "profanity": min(1.0, f["profanity"] / 5.0),
            "drugs": min(1.0, f["drugs"] / 5.0),
            "child_risk": min(1.0, f["child_mentions"] / 3.0),
        }

    @staticmethod
    def map_scores_to_rating(agg: Dict[str, float]) -> Dict[str, Any]:
        reasons = []
        rating = "6+"

        if agg["sex_act"] >= 0.8 or agg["gore"] >= 0.8:
            rating = "18+"
            reasons.append("explicit sexual or violent content")
        elif agg["child_risk"] > 0.5 and (
            agg["sex_act"] >= 0.5 or agg["violence"] >= 0.5
        ):
            rating = "18+"
            reasons.append("violence or sexual content involving minors")
        elif agg["violence"] >= 0.4 or agg["gore"] >= 0.4:
            rating = "16+"
            reasons.append("explicit violence or murder")
        elif agg["profanity"] >= 0.5 or agg["drugs"] >= 0.4 or agg["nudity"] >= 0.3:
            rating = "12+"
            reasons.append("moderate language, alcohol/tobacco, mild nudity")
        elif agg["violence"] >= 0.3:
            rating = "12+"
            reasons.append("moderate violence or threats")

        return {"rating": rating, "reasons": reasons}

    def analyze_script(self, text: str, script_id: str | None = None) -> Dict[str, Any]:
        logger.info(f"Analyzing script (id={script_id})")
        tracker = MetricsTracker() if settings.enable_metrics else None

        if tracker:
            tracker.start_timer("parsing")
        scenes = self.parse_script_to_scenes(text)
        if tracker:
            tracker.record_scene_parsing(tracker.end_timer("parsing"))
            tracker.record_scenes_count(len(scenes))
        logger.info(f"Parsed {len(scenes)} scenes")

        if tracker:
            tracker.start_timer("feature_extraction")
        features = [self.scene_feature_vector(s["text"]) for s in scenes]
        if tracker:
            avg_time = tracker.end_timer("feature_extraction") / max(len(scenes), 1)
            tracker.record_feature_extraction(avg_time)

        scores = [self.normalize_scene_scores(f) for f in features]

        agg = {
            k: float(np.percentile([s[k] for s in scores], 90))
            for k in scores[0].keys()
        }
        rating_info = self.map_scores_to_rating(agg)

        if tracker:
            tracker.record_scores(agg)
            tracker.record_rating(rating_info["rating"])

        if settings.json_logs:
            log_feature_scores(
                script_id=script_id,
                violence=agg["violence"],
                sex_act=agg["sex_act"],
                gore=agg["gore"],
                profanity=agg["profanity"],
                drugs=agg["drugs"],
                nudity=agg["nudity"],
                predicted_rating=rating_info["rating"],
            )

        ranking = []
        for s, sc in zip(scenes, scores):
            w = (
                sc["violence"] * 0.5
                + sc["gore"] * 0.8
                + sc["sex_act"] * 0.9
                + sc["profanity"] * 0.3
                + sc["drugs"] * 0.3
                + sc["child_risk"] * 0.6
                + sc["nudity"] * 0.3
            )
            ranking.append((w, s, sc))
        ranking.sort(reverse=True, key=lambda x: x[0])

        top = []
        for w, s, sc in ranking[:5]:
            top.append(
                {
                    "scene_id": s["scene_id"],
                    "heading": s["heading"],
                    "violence": sc["violence"],
                    "gore": sc["gore"],
                    "sex_act": sc["sex_act"],
                    "nudity": sc["nudity"],
                    "profanity": sc["profanity"],
                    "drugs": sc["drugs"],
                    "child_risk": sc["child_risk"],
                    "weight": round(float(w), 2),
                    "sample_text": s["text"][:400].replace("\n", " "),
                }
            )

        return {
            "script_id": script_id,
            "predicted_rating": rating_info["rating"],
            "reasons": rating_info["reasons"],
            "agg_scores": agg,
            "top_trigger_scenes": top,
            "model_version": settings.model_version,
            "total_scenes": len(scenes),
        }


pipeline: RatingPipeline | None = None


def get_pipeline() -> RatingPipeline:
    global pipeline
    if pipeline is None:
        pipeline = RatingPipeline()
    return pipeline
