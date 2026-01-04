#!/usr/bin/env python3
"""
TruthAngel Single File Auto-Tagger
Interactively asks which file to tag, then applies 4 tags to each chapter.

Usage:
    python single-auto-tagger.py
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

# Import all the tagging logic from auto-tagger
from pathlib import Path
import sys

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent

# =============================================================================
# CONFIGURATION (copied from auto-tagger.py)
# =============================================================================

TAG_VOCABULARY_PATH = SCRIPT_DIR / "tag-vocabulary.json"

LIBRARY_TYPE_PATTERNS = {
    "geography": ["geography-libraries"],
    "knowledge": ["knowledge-libraries"],
    "practical": ["practical-libraries"],
    "perspectives": ["perspectives-libraries"],
    "event": ["event-libraries"],
    "candidate": ["politician-libraries"],
    "infrastructure": ["infrastructure-libraries"],
}

BROAD_TAGS = {
    "geography": "geography",
    "knowledge": "arts",
    "practical": "society",
    "perspectives": "philosophy",
    "event": "conflict",
    "candidate": "politics",
    "infrastructure": "technology",
}

ANCHOR_TAGS = {
    "geography": {
        "national overview": "identity",
        "history": "cultural-heritage",
        "government": "governance",
        "travel": "security",
        "culture": "cultural-heritage",
        "economy": "development",
        "default": "identity",
    },
    "knowledge": {
        "history": "cultural-heritage",
        "movements": "cultural-heritage",
        "techniques": "innovation",
        "theory": "epistemology",
        "biography": "identity",
        "period": "cultural-heritage",
        "fundamentals": "epistemology",
        "default": "epistemology",
    },
    "practical": {
        "safety": "security",
        "methods": "innovation",
        "planning": "systems-thinking",
        "tools": "innovation",
        "fundamentals": "epistemology",
        "default": "systems-thinking",
    },
    "perspectives": {
        "bias": "epistemology",
        "logic": "critical-thinking",
        "media": "critical-thinking",
        "debate": "rhetoric",
        "perspective": "epistemology",
        "default": "critical-thinking",
    },
    "event": {
        "conflict": "security",
        "political": "governance",
        "social": "justice",
        "economic": "development",
        "humanitarian": "human-rights",
        "timeline": "cultural-heritage",
        "default": "security",
    },
    "candidate": {
        "senate": "democracy",
        "house": "democracy",
        "governor": "democracy",
        "default": "democracy",
    },
    "infrastructure": {
        "architecture": "systems-thinking",
        "operations": "systems-thinking",
        "security": "security",
        "failure": "accountability",
        "standards": "governance",
        "default": "systems-thinking",
    },
}

GEOGRAPHY_DIFFERENTIATORS = {
    "history": {
        "ancient-history": ["peru", "mexico", "egypt", "china", "india", "greece", "italy", "iraq", "iran", "turkey", "guatemala", "bolivia"],
        "cold-war": ["chile", "cuba", "korea", "vietnam", "germany", "poland", "hungary", "czechoslovakia", "afghanistan"],
        "migration": ["australia", "argentina", "uruguay", "usa", "united states", "canada", "new zealand", "brazil", "israel"],
        "world-wars": ["germany", "japan", "poland", "france", "uk", "united kingdom", "russia", "austria"],
        "colonialism": [],
    },
    "government": {
        "authoritarianism": ["venezuela", "china", "russia", "cuba", "north korea", "iran", "syria", "belarus", "myanmar", "eritrea", "turkmenistan"],
        "federalism": ["usa", "united states", "germany", "brazil", "india", "australia", "canada", "mexico", "argentina", "switzerland"],
        "human-rights": ["sweden", "norway", "denmark", "netherlands", "new zealand", "finland"],
        "democracy": [],
    },
    "national overview": {
        "inequality": ["brazil", "south africa", "colombia", "mexico", "chile", "india"],
        "development": ["china", "india", "vietnam", "ethiopia", "bangladesh", "indonesia"],
        "migration": ["argentina", "uruguay", "australia", "usa", "united states", "canada", "israel"],
        "globalization": ["singapore", "netherlands", "switzerland", "hong kong", "ireland", "belgium"],
        "sustainability": ["costa rica", "bhutan", "norway", "sweden", "denmark", "iceland"],
    },
    "travel": {
        "cultural-heritage": ["italy", "france", "japan", "china", "india", "peru", "mexico", "egypt", "greece", "spain", "morocco"],
        "sustainability": ["costa rica", "norway", "new zealand", "iceland", "bhutan", "galapagos", "ecuador"],
        "infrastructure": ["usa", "united states", "japan", "germany", "uk", "united kingdom", "france", "australia", "canada"],
        "security": [],
    },
}

KNOWLEDGE_DIFFERENTIATORS = {
    "arts": {
        "visual-arts": ["painting", "sculpture", "drawing", "printmaking", "photography", "ceramics"],
        "performing-arts": ["theater", "dance", "music", "opera", "ballet", "circus"],
        "media-arts": ["film", "video", "digital", "animation", "gaming"],
        "literary-arts": ["poetry", "prose", "drama", "fiction", "novel", "essay"],
        "architecture": ["architecture", "building", "design", "urban"],
    },
    "science": {
        "natural-sciences": ["biology", "chemistry", "physics", "geology", "ecology"],
        "social-sciences": ["psychology", "sociology", "anthropology", "economics"],
        "formal-sciences": ["mathematics", "logic", "statistics", "computer"],
        "applied-sciences": ["engineering", "medicine", "technology"],
    },
    "philosophy": {
        "ethics": ["ethics", "moral", "values", "virtue", "duty"],
        "epistemology": ["knowledge", "truth", "belief", "justification"],
        "metaphysics": ["reality", "existence", "being", "ontology"],
        "logic": ["logic", "reasoning", "argument", "fallacy"],
        "aesthetics": ["beauty", "art", "taste", "sublime"],
    },
}

PERSPECTIVES_DIFFERENTIATORS = {
    "bias": {
        "cognition": ["cognitive", "thinking", "mental", "brain", "psychological"],
        "bias": ["bias", "prejudice", "stereotype", "discrimination"],
        "social-dynamics": ["social", "group", "conformity", "peer"],
        "media-literacy": ["media", "news", "source", "information"],
    },
    "debate": {
        "human-rights": ["rights", "freedom", "liberty", "equality"],
        "climate-change": ["climate", "environment", "carbon", "warming"],
        "security": ["security", "safety", "defense", "military"],
        "economics": ["economic", "market", "trade", "fiscal"],
        "governance": ["government", "policy", "regulation", "law"],
    },
}

EVENT_DIFFERENTIATORS = {
    "conflict": {
        "geopolitics": ["territorial", "border", "international", "power", "influence"],
        "humanitarian": ["refugee", "civilian", "aid", "crisis", "humanitarian"],
        "terrorism": ["terror", "extremist", "insurgent", "radical"],
        "diplomacy": ["negotiation", "treaty", "agreement", "talks"],
    },
    "political": {
        "democracy": ["election", "vote", "democratic", "reform"],
        "authoritarianism": ["authoritarian", "dictator", "regime", "crackdown"],
        "activism": ["protest", "movement", "activist", "uprising"],
    },
}

REGION_TAGS = {
    "americas": ["argentina", "bolivia", "brazil", "canada", "chile", "colombia", "costa rica",
                 "cuba", "dominican republic", "ecuador", "el salvador", "guatemala", "haiti",
                 "honduras", "mexico", "nicaragua", "panama", "paraguay", "peru", "puerto rico",
                 "uruguay", "usa", "united states", "venezuela", "jamaica", "trinidad", "guyana",
                 "suriname", "belize", "bahamas", "barbados", "antigua", "grenada", "saint"],
    "europe": ["albania", "austria", "belgium", "bosnia", "bulgaria", "croatia", "czech",
               "denmark", "estonia", "finland", "france", "germany", "greece", "hungary",
               "iceland", "ireland", "italy", "latvia", "lithuania", "luxembourg", "malta",
               "netherlands", "norway", "poland", "portugal", "romania", "serbia", "slovakia",
               "slovenia", "spain", "sweden", "switzerland", "uk", "united kingdom", "ukraine"],
    "asia": ["afghanistan", "bangladesh", "bhutan", "cambodia", "china", "india", "indonesia",
             "japan", "kazakhstan", "korea", "laos", "malaysia", "mongolia", "myanmar", "nepal",
             "pakistan", "philippines", "singapore", "sri lanka", "taiwan", "thailand", "vietnam"],
    "africa": ["algeria", "angola", "botswana", "cameroon", "congo", "egypt", "ethiopia",
               "ghana", "kenya", "libya", "madagascar", "mali", "morocco", "mozambique",
               "namibia", "nigeria", "rwanda", "senegal", "somalia", "south africa", "sudan",
               "tanzania", "tunisia", "uganda", "zambia", "zimbabwe"],
    "oceania": ["australia", "fiji", "kiribati", "marshall", "micronesia", "nauru", "new zealand",
                "palau", "papua", "samoa", "solomon", "tonga", "tuvalu", "vanuatu"],
    "middle-east": ["bahrain", "iran", "iraq", "israel", "jordan", "kuwait", "lebanon",
                    "oman", "palestine", "qatar", "saudi", "syria", "turkey", "uae", "yemen"],
}

SUBJECT_TAGS = {
    "painting": ["painting", "painter", "oil", "watercolor", "acrylic", "canvas"],
    "sculpture": ["sculpture", "sculptor", "carving", "bronze", "marble", "clay"],
    "photography": ["photography", "photographer", "camera", "lens", "exposure"],
    "music": ["music", "musician", "composer", "symphony", "orchestra"],
    "theater": ["theater", "theatre", "drama", "stage", "playwright"],
    "film": ["film", "cinema", "movie", "director", "screenplay"],
    "dance": ["dance", "dancer", "choreograph", "ballet"],
    "architecture": ["architecture", "architect", "building", "structure"],
    "drawing": ["drawing", "sketch", "pencil", "charcoal"],
    "printmaking": ["print", "etching", "lithograph", "woodcut"],
    "digital-art": ["digital art", "computer art", "generative", "nft"],
    "biology": ["biology", "organism", "cell", "genetics", "evolution"],
    "physics": ["physics", "quantum", "relativity", "particle", "mechanics"],
    "chemistry": ["chemistry", "chemical", "molecule", "reaction", "element"],
    "psychology": ["psychology", "psychological", "cognitive", "behavior"],
    "sociology": ["sociology", "social", "society", "community"],
    "philosophy": ["philosophy", "philosophical", "philosopher"],
    "ethics": ["ethics", "ethical", "moral", "morality"],
    "logic": ["logic", "logical", "reasoning", "argument"],
    "cooking": ["cooking", "recipe", "kitchen", "culinary", "food"],
    "personal-finance": ["finance", "budget", "invest", "saving", "money"],
    "travel": ["travel", "tourism", "tourist", "visitor", "destination"],
}


# =============================================================================
# HELPER FUNCTIONS (copied from auto-tagger.py)
# =============================================================================

def load_tag_vocabulary() -> Dict:
    with open(TAG_VOCABULARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_valid_tags(vocabulary: Dict) -> Dict[str, List[str]]:
    valid = {"broad": [], "medium": [], "specific": []}
    for tier in ["broad", "medium", "specific"]:
        valid[tier] = [tag["id"] for tag in vocabulary["tags"].get(tier, [])]
    return valid

def detect_library_type(file_path: str) -> str:
    path_lower = file_path.lower()
    for lib_type, patterns in LIBRARY_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in path_lower:
                return lib_type
    return "knowledge"

def normalize_text(text: str) -> str:
    return text.lower().strip()

def get_chapter_type(chapter_name: str, book_name: str = "") -> str:
    combined = normalize_text(f"{chapter_name} {book_name}")

    if any(kw in combined for kw in ["national overview", "overview", "about", "introduction"]):
        return "national overview"
    if any(kw in combined for kw in ["history", "historical", "timeline", "origins"]):
        return "history"
    if any(kw in combined for kw in ["government", "political", "politics", "governance"]):
        return "government"
    if any(kw in combined for kw in ["travel", "tourism", "visiting", "destinations"]):
        return "travel"
    if any(kw in combined for kw in ["culture", "cultural", "traditions", "customs"]):
        return "culture"
    if any(kw in combined for kw in ["economy", "economic", "trade", "industry"]):
        return "economy"
    if any(kw in combined for kw in ["technique", "method", "how to", "process"]):
        return "techniques"
    if any(kw in combined for kw in ["theory", "concept", "principle", "fundamental"]):
        return "theory"
    if any(kw in combined for kw in ["movement", "period", "era", "school of"]):
        return "movements"
    if any(kw in combined for kw in ["biography", "life of", "artist", "composer"]):
        return "biography"
    if any(kw in combined for kw in ["bias", "cognitive", "fallacy", "thinking error"]):
        return "bias"
    if any(kw in combined for kw in ["logic", "reasoning", "argument", "critical"]):
        return "logic"
    if any(kw in combined for kw in ["media", "news", "source", "information"]):
        return "media"
    if any(kw in combined for kw in ["debate", "controversy", "perspective", "viewpoint"]):
        return "debate"
    if any(kw in combined for kw in ["conflict", "war", "battle", "military"]):
        return "conflict"
    if any(kw in combined for kw in ["humanitarian", "refugee", "aid", "crisis"]):
        return "humanitarian"
    if "senate" in combined:
        return "senate"
    if "house" in combined:
        return "house"
    if "governor" in combined:
        return "governor"
    if any(kw in combined for kw in ["architecture", "design", "structure"]):
        return "architecture"
    if any(kw in combined for kw in ["operation", "running", "management"]):
        return "operations"
    if any(kw in combined for kw in ["security", "protection", "safety"]):
        return "security"
    if any(kw in combined for kw in ["failure", "risk", "incident", "outage"]):
        return "failure"
    return "default"


# =============================================================================
# TAGGING LOGIC (copied from auto-tagger.py)
# =============================================================================

def get_broad_tag(library_type: str, shelf_name: str, book_name: str, valid_tags: Dict) -> str:
    if library_type == "knowledge":
        combined = normalize_text(f"{shelf_name} {book_name}")
        if any(kw in combined for kw in ["art", "paint", "sculpt", "music", "theater", "film", "dance"]):
            return "arts"
        if any(kw in combined for kw in ["science", "physics", "chemistry", "biology", "math"]):
            return "science"
        if any(kw in combined for kw in ["philosophy", "ethics", "logic", "epistemology"]):
            return "philosophy"
        if any(kw in combined for kw in ["history", "historical"]):
            return "history"
        if any(kw in combined for kw in ["technology", "computer", "software", "ai", "robot"]):
            return "technology"
        return "education"
    if library_type == "perspectives":
        return "philosophy"
    if library_type == "event":
        return "conflict"
    if library_type == "practical":
        return "society"
    return BROAD_TAGS.get(library_type, "society")

def get_anchor_tag(library_type: str, chapter_type: str, valid_tags: Dict) -> str:
    anchors = ANCHOR_TAGS.get(library_type, {})
    tag = anchors.get(chapter_type, anchors.get("default", "identity"))
    if tag not in valid_tags["medium"]:
        return "identity"
    return tag

def get_differentiator_tag(library_type: str, chapter_type: str, book_name: str,
                           chapter_name: str, valid_tags: Dict) -> str:
    combined = normalize_text(f"{book_name} {chapter_name}")

    if library_type == "geography":
        diff_rules = GEOGRAPHY_DIFFERENTIATORS.get(chapter_type, {})
        for tag, countries in diff_rules.items():
            for country in countries:
                if country.lower() in combined:
                    if tag in valid_tags["medium"] or tag in valid_tags["specific"]:
                        return tag
        if chapter_type == "history":
            return "colonialism"
        if chapter_type == "government":
            return "democracy"
        if chapter_type == "travel":
            return "security"
        if chapter_type == "national overview":
            return "development"
        return "cultural-heritage"

    if library_type == "knowledge":
        for tag, keywords in KNOWLEDGE_DIFFERENTIATORS.get("arts", {}).items():
            if any(kw in combined for kw in keywords):
                if tag in valid_tags["medium"] or tag in valid_tags["specific"]:
                    return tag
        for tag, keywords in KNOWLEDGE_DIFFERENTIATORS.get("philosophy", {}).items():
            if any(kw in combined for kw in keywords):
                if tag in valid_tags["medium"] or tag in valid_tags["specific"]:
                    return tag
        return "innovation"

    if library_type == "perspectives":
        for category, rules in PERSPECTIVES_DIFFERENTIATORS.items():
            for tag, keywords in rules.items():
                if any(kw in combined for kw in keywords):
                    if tag in valid_tags["medium"] or tag in valid_tags["specific"]:
                        return tag
        return "critical-thinking"

    if library_type == "event":
        for category, rules in EVENT_DIFFERENTIATORS.items():
            for tag, keywords in rules.items():
                if any(kw in combined for kw in keywords):
                    if tag in valid_tags["medium"] or tag in valid_tags["specific"]:
                        return tag
        return "geopolitics"

    if library_type == "candidate":
        return "federalism"

    if library_type == "infrastructure":
        if any(kw in combined for kw in ["energy", "power", "cooling"]):
            return "sustainability"
        if any(kw in combined for kw in ["security", "protection"]):
            return "security"
        if any(kw in combined for kw in ["redundan", "failover", "backup"]):
            return "accountability"
        return "innovation"

    return "identity"

def get_specific_tag(library_type: str, book_name: str, chapter_name: str,
                     shelf_name: str, library_name: str, valid_tags: Dict) -> str:
    combined = normalize_text(f"{book_name} {chapter_name} {shelf_name} {library_name}")

    if library_type == "geography":
        for region, countries in REGION_TAGS.items():
            for country in countries:
                if country.lower() in combined:
                    return region
        return "geography"

    if library_type in ["perspectives", "event"]:
        if any(kw in combined for kw in ["ukraine", "russia", "kremlin", "putin", "kyiv", "moscow"]):
            return "russia-ukraine"
        if any(kw in combined for kw in ["israel", "palestine", "gaza", "hamas", "netanyahu", "west bank"]):
            return "israel-palestine"
        if any(kw in combined for kw in ["taiwan", "china", "strait", "beijing", "taipei", "ccp"]):
            return "china-taiwan"
        if any(kw in combined for kw in ["nato", "atlantic", "alliance"]):
            return "nato"
        if any(kw in combined for kw in ["trump", "maga", "january 6", "jan 6"]):
            return "trump"
        if any(kw in combined for kw in ["climate", "carbon", "warming", "emission", "green"]):
            return "climate-science"
        if any(kw in combined for kw in ["immigration", "border", "migrant", "refugee", "asylum"]):
            return "immigration"
        if any(kw in combined for kw in ["police", "policing", "criminal justice", "incarceration"]):
            return "policing"
        if any(kw in combined for kw in ["media", "news", "journalism", "press", "misinformation"]):
            return "journalism"
        if any(kw in combined for kw in ["speech", "censorship", "expression", "first amendment"]):
            return "civil-rights"
        if any(kw in combined for kw in ["equality", "civil rights", "discrimination", "race", "gender"]):
            return "civil-rights"
        if any(kw in combined for kw in ["economic", "economy", "trade", "fiscal", "monetary"]):
            return "economics-theory"
        if any(kw in combined for kw in ["technology", "digital", "ai", "algorithm", "platform"]):
            return "technology"
        for region, countries in REGION_TAGS.items():
            for country in countries:
                if country.lower() in combined:
                    return region
        return "geopolitics"

    for tag, keywords in SUBJECT_TAGS.items():
        if any(kw in combined for kw in keywords):
            if tag in valid_tags["specific"]:
                return tag

    if library_type == "knowledge":
        if "art" in combined:
            return "visual-arts"
        return "art-history"
    if library_type == "practical":
        return "personal-finance"
    if library_type == "candidate":
        return "elections"
    if library_type == "infrastructure":
        return "data-centers"

    return "education"


def get_cross_library_tag(library_type: str, book_name: str, chapter_name: str,
                          shelf_name: str, library_name: str, valid_tags: Dict) -> str:
    """Determine cross-library connector tag (Tag 4) - connects outward to other libraries."""
    combined = normalize_text(f"{book_name} {chapter_name} {shelf_name} {library_name}")

    # Physics connections
    if any(kw in combined for kw in ["physics", "electromagnetic", "thermodynamic", "frequency",
                                      "voltage", "inertia", "fusion", "fission", "superconducting"]):
        return "physics"

    # Chemistry connections
    if any(kw in combined for kw in ["battery", "lithium", "chemical", "hydrogen"]):
        return "chemistry"

    # Climate/environment connections
    if any(kw in combined for kw in ["climate", "carbon", "renewable", "fossil", "emission",
                                      "wildfire", "weather", "flood", "hurricane"]):
        return "climate-science"

    # Security connections
    if any(kw in combined for kw in ["cyber", "security", "attack", "failure", "outage",
                                      "blackout", "resilience", "reliability", "nuclear"]):
        return "security"

    # AI/ML connections
    if any(kw in combined for kw in ["ai", "machine learning", "digital twin", "predictive",
                                      "smart grid", "algorithm", "forecast"]):
        return "ai-ml"

    # Economics connections
    if any(kw in combined for kw in ["market", "economic", "dispatch", "cost", "pricing",
                                      "trading", "net metering", "subsidy"]):
        return "economics-theory"

    # Governance/policy connections
    if any(kw in combined for kw in ["policy", "regulation", "political", "cross-border",
                                      "permitting", "coordination"]):
        return "governance"

    # Human rights connections
    if any(kw in combined for kw in ["indigenous", "community", "social", "land rights",
                                      "consultation", "equity"]):
        return "human-rights"

    # Development connections
    if any(kw in combined for kw in ["global", "inequality", "developing", "rural",
                                      "remote", "access", "electrification"]):
        return "development"

    # Architecture connections
    if any(kw in combined for kw in ["architecture", "design", "substation", "topology",
                                      "urban", "building", "infrastructure"]):
        return "architecture"

    # Data centers connection
    if any(kw in combined for kw in ["data center", "backup", "ups", "power quality"]):
        return "data-centers"

    # Psychology connections
    if any(kw in combined for kw in ["human factors", "operator", "decision", "training"]):
        return "psychology"

    # Ethics connections
    if any(kw in combined for kw in ["ethical", "philosophical", "equity", "progress"]):
        return "ethics"

    # Fallback by library type
    if library_type == "infrastructure":
        return "architecture"
    if library_type == "knowledge":
        return "education"
    if library_type == "perspectives":
        return "critical-thinking"
    if library_type == "geography":
        return "geography"

    return "education"


def get_library_tag(library_type: str, shelf_name: str, book_name: str, library_name: str) -> str:
    """Determine Tag 3 - the tag that helps find this library from outside.

    This is the 'identity' tag that allows other libraries to discover this content.
    Returns the tag that best represents the library's domain.
    """
    combined = normalize_text(f"{shelf_name} {book_name} {library_name}")

    # Infrastructure libraries
    if library_type == "infrastructure":
        if any(kw in combined for kw in ["power", "energy", "electrical", "grid", "transmission"]):
            return "energy"
        if any(kw in combined for kw in ["data center", "server", "cooling"]):
            return "data-centers"
        return "technology"

    # Knowledge libraries - return the subject area
    if library_type == "knowledge":
        if any(kw in combined for kw in ["art", "paint", "sculpt", "music", "theater", "film", "dance", "visual"]):
            return "visual-arts"
        if any(kw in combined for kw in ["physics", "chemistry", "biology", "science"]):
            return "science"
        if any(kw in combined for kw in ["philosophy", "ethics", "logic"]):
            return "philosophy"
        if any(kw in combined for kw in ["ai", "artificial intelligence", "machine learning", "robot"]):
            return "ai-ml"
        if any(kw in combined for kw in ["software", "programming", "computer", "technology"]):
            return "technology"
        if any(kw in combined for kw in ["history", "historical"]):
            return "history"
        return "education"

    # Geography libraries
    if library_type == "geography":
        # Check for region
        for region, countries in REGION_TAGS.items():
            for country in countries:
                if country.lower() in combined:
                    return region
        return "geography"

    # Practical libraries
    if library_type == "practical":
        if any(kw in combined for kw in ["finance", "money", "budget", "invest"]):
            return "personal-finance"
        if any(kw in combined for kw in ["safety", "security", "fact-check"]):
            return "security"
        if any(kw in combined for kw in ["git", "software", "programming"]):
            return "technology"
        return "society"

    # Perspectives libraries
    if library_type == "perspectives":
        return "critical-thinking"

    # Event libraries
    if library_type == "event":
        return "conflict"

    # Candidate libraries
    if library_type == "candidate":
        return "elections"

    return "education"


def generate_tags(library_type: str, shelf_name: str, book_name: str,
                  chapter_name: str, library_name: str, valid_tags: Dict) -> List[str]:
    """Generate 4 tags for a chapter.

    Tag arrangement (applies to all library types):
    - Tag 1: Broad category (technology, philosophy, arts, science, etc.)
    - Tag 2: Anchor tag (systems-thinking, innovation, accountability, etc.)
    - Tag 3: Library-finding tag - helps other libraries find this one (energy, visual-arts, etc.)
    - Tag 4: Cross-library connector - points outward to other domains (physics, climate-science, etc.)
    """
    chapter_type = get_chapter_type(chapter_name, book_name)

    tag1 = get_broad_tag(library_type, shelf_name, book_name, valid_tags)
    tag2 = get_anchor_tag(library_type, chapter_type, valid_tags)
    tag3 = get_library_tag(library_type, shelf_name, book_name, library_name)
    tag4 = get_cross_library_tag(library_type, book_name, chapter_name, shelf_name, library_name, valid_tags)

    # Ensure no duplicates - replace duplicates with alternatives
    tags = [tag1]
    for i, tag in enumerate([tag2, tag3, tag4]):
        if tag not in tags:
            tags.append(tag)
        else:
            # Find alternative based on position
            if i == 0:  # tag2 duplicate
                tags.append("cultural-heritage")
            elif i == 1:  # tag3 duplicate
                tags.append("identity")
            else:  # tag4 duplicate
                tags.append("education")

    return tags[:4]


# =============================================================================
# MAIN PROCESSING
# =============================================================================

def find_all_libraries() -> List[str]:
    """Find all library JSON files."""
    libraries = []
    base_dir = SCRIPT_DIR

    for lib_type in LIBRARY_TYPE_PATTERNS.keys():
        lib_dir = base_dir / f"{lib_type}-libraries"
        if lib_dir.exists():
            for json_file in lib_dir.glob("*.json"):
                if "inventory" in json_file.name.lower():
                    continue
                if "questions" in json_file.name.lower():
                    continue
                if "bare" in json_file.name.lower():
                    continue
                libraries.append(str(json_file))

    return sorted(libraries)

def process_library(file_path: str, dry_run: bool = False) -> Tuple[int, int]:
    """Process a library file and add tags to all chapters."""
    vocabulary = load_tag_vocabulary()
    valid_tags = get_valid_tags(vocabulary)
    library_type = detect_library_type(file_path)

    print(f"\nProcessing: {file_path}")
    print(f"Library type: {library_type}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chapters_tagged = 0
    chapters_skipped = 0

    library_name = data.get("library", "Unknown")

    for shelf in data.get("shelves", []):
        shelf_name = shelf.get("name", "")

        for book in shelf.get("books", []):
            book_name = book.get("name", "")

            for chapter in book.get("chapters", []):
                chapter_name = chapter.get("name", "")

                new_tags = generate_tags(library_type, shelf_name, book_name,
                                        chapter_name, library_name, valid_tags)

                if dry_run:
                    print(f"  [{book_name}] {chapter_name}")
                    print(f"    -> {new_tags}")
                else:
                    chapter["tags"] = new_tags

                chapters_tagged += 1

    if not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved: {chapters_tagged} chapters tagged")
    else:
        print(f"Dry run: {chapters_tagged} chapters would be tagged")

    return chapters_tagged, chapters_skipped


def main():
    print("=" * 60)
    print("TruthAngel Single File Auto-Tagger")
    print("=" * 60)

    # Find all available libraries
    libraries = find_all_libraries()

    if not libraries:
        print("\nNo library files found!")
        return

    # Display numbered list
    print("\nAvailable libraries:\n")
    for i, lib in enumerate(libraries, 1):
        # Show just the filename for cleaner display
        name = Path(lib).name
        print(f"  {i:2}. {name}")

    print()

    # Ask user to select
    while True:
        try:
            choice = input("Enter the number of the file to tag (or 'q' to quit): ").strip()

            if choice.lower() == 'q':
                print("Goodbye!")
                return

            num = int(choice)
            if 1 <= num <= len(libraries):
                selected_file = libraries[num - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(libraries)}")
        except ValueError:
            print("Please enter a valid number")

    # Ask about dry run
    dry_run_choice = input("\nDry run? (y/n, default=n): ").strip().lower()
    dry_run = dry_run_choice == 'y'

    # Process the file
    print()
    tagged, skipped = process_library(selected_file, dry_run)

    print(f"\n{'=' * 60}")
    print(f"Done! {'Would tag' if dry_run else 'Tagged'} {tagged} chapters.")


if __name__ == "__main__":
    main()
