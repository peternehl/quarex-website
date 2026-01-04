#!/usr/bin/env python3
"""
TruthAngel Book Auto-Tagger
Automatically applies 4 vocabulary-compliant tags to each chapter in standalone book JSON files.

Usage:
    python book-auto-tagger.py <book_file.json>
    python book-auto-tagger.py --dry-run <book_file.json>   # Preview without saving

This tagger works with the new standalone book format:
{
  "name": "Book Name",
  "created_by": "...",
  "mode": "followup",
  "chapters": [...]
}

Tag Strategy (4 tags per chapter):
    Tag 1 (Broad): Domain anchor - the primary knowledge domain
    Tag 2 (Medium): Conceptual lens - how we're looking at the topic
    Tag 3 (Medium/Specific): Subject differentiator - what makes this unique
    Tag 4 (Specific): Precise identifier - the most specific applicable tag
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Set, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
TAG_VOCABULARY_PATH = SCRIPT_DIR / "tag-vocabulary.json"

# Library type detection patterns (from file path)
LIBRARY_TYPE_PATTERNS = {
    "geography": ["geography-libraries"],
    "knowledge": ["knowledge-libraries"],
    "practical": ["practical-libraries"],
    "perspectives": ["perspectives-libraries"],
    "event": ["event-libraries"],
    "candidate": ["politician-libraries"],
    "infrastructure": ["infrastructure-libraries"],
}

# =============================================================================
# KEYWORD MAPPINGS (from auto-tagger.py)
# =============================================================================

SPECIFIC_TAG_KEYWORDS = {
    # Science branches
    "physics": ["physics", "physical", "force", "energy", "motion", "wave"],
    "quantum-mechanics": ["quantum", "quanta", "wave function", "heisenberg", "superposition"],
    "thermodynamics": ["thermodynamic", "heat", "entropy", "thermal", "temperature"],
    "electromagnetism": ["electromagnetic", "electric", "magnetic", "maxwell", "faraday"],
    "mechanics": ["mechanics", "newton", "momentum", "velocity", "acceleration"],
    "chemistry": ["chemistry", "chemical", "molecule", "reaction", "element"],
    "biology": ["biology", "biological", "organism", "life", "living"],
    "neuroscience": ["neuro", "brain", "neuron", "synapse", "cognitive", "neural"],
    "geology": ["geology", "geological", "rock", "mineral", "tectonic", "volcano"],
    "meteorology": ["meteorology", "weather", "atmospheric", "climate", "storm"],
    "astronomy": ["astronomy", "star", "planet", "galaxy", "telescope", "celestial"],

    # Technology
    "computer-science": ["computer science", "algorithm", "data structure", "computation"],
    "software-engineering": ["software", "programming", "code", "developer"],
    "ai-ml": ["artificial intelligence", "machine learning", "neural network", "deep learning"],
    "robotics": ["robot", "robotic", "autonomous", "automation"],
    "cybersecurity": ["cybersecurity", "hacking", "malware", "firewall", "encryption"],
    "data-science": ["data science", "analytics", "visualization", "pandas", "big data"],

    # Energy
    "solar-power": ["solar", "photovoltaic", "pv", "solar panel", "solar cell"],
    "wind-power": ["wind power", "wind turbine", "wind farm"],
    "hydropower": ["hydropower", "hydroelectric", "water turbine"],
    "nuclear-energy": ["nuclear power", "reactor", "fission", "uranium"],
    "geothermal": ["geothermal", "earth heat", "ground source"],
    "grid-systems": ["power grid", "electrical grid", "transmission grid", "distribution"],
    "energy-storage": ["battery", "energy storage", "lithium", "capacitor"],
    "fossil-fuels": ["fossil fuel", "coal", "oil", "natural gas", "petroleum"],

    # Politics and social
    "us-politics": ["american politics", "congress", "senate", "white house"],
    "elections": ["election", "vote", "ballot", "campaign", "candidate", "polling"],
    "immigration": ["immigration", "immigrant", "border", "visa", "asylum"],
    "journalism": ["journalism", "journalist", "reporter", "news media", "press"],
    "civil-rights": ["civil rights", "equality", "discrimination", "voting rights"],

    # Psychology and health
    "psychology": ["psychology", "psychological", "cognitive", "behavior", "mind"],
    "public-health": ["public health", "epidemic", "pandemic", "vaccination"],
    "medicine": ["medicine", "medical", "doctor", "hospital", "treatment", "therapy"],

    # Arts
    "visual-arts": ["visual art", "painting", "sculpture", "drawing", "gallery"],
    "music": ["music", "musician", "composer", "symphony", "orchestra"],
    "film": ["film", "cinema", "movie", "director", "screenplay"],
    "theater": ["theater", "theatre", "drama", "stage", "playwright"],

    # Regions
    "americas": ["america", "usa", "united states", "canada", "mexico", "brazil"],
    "europe": ["europe", "european", "eu", "germany", "france", "uk"],
    "asia": ["asia", "asian", "china", "japan", "india", "korea"],
    "africa": ["africa", "african", "nigeria", "egypt", "south africa"],
    "middle-east": ["middle east", "arab", "iran", "israel", "saudi"],
}

MEDIUM_TAG_KEYWORDS = {
    "critical-thinking": ["critical thinking", "analyze", "evaluate", "reasoning", "logic"],
    "systems-thinking": ["systems thinking", "interconnected", "holistic", "complexity"],
    "epistemology": ["epistemology", "knowledge", "truth", "belief", "justification"],
    "methodology": ["methodology", "method", "approach", "framework", "systematic"],
    "theory": ["theory", "theoretical", "conceptual", "model", "framework"],
    "application": ["application", "applied", "practical", "real-world"],
    "analysis": ["analysis", "examine", "investigate", "breakdown"],
    "innovation": ["innovation", "innovative", "new", "breakthrough", "pioneering"],
    "tradition": ["tradition", "traditional", "heritage", "classical"],
    "democracy": ["democracy", "democratic", "voting", "representation"],
    "governance": ["governance", "govern", "administration", "oversight", "regulation"],
    "human-rights": ["human rights", "rights", "freedom", "liberty", "dignity"],
    "justice": ["justice", "fair", "equitable", "remedy", "court"],
    "accountability": ["accountability", "accountable", "responsible"],
    "transparency": ["transparency", "transparent", "open", "disclosure"],
    "activism": ["activism", "activist", "movement", "protest", "advocacy"],
    "identity": ["identity", "belonging", "self", "who we are"],
    "cultural-heritage": ["heritage", "legacy", "tradition", "cultural"],
    "sustainability": ["sustainability", "sustainable", "renewable", "green", "eco"],
    "energy": ["energy", "power", "electricity", "fuel"],
    "development": ["development", "growth", "progress", "advancement"],
    "regulation": ["regulation", "regulate", "rule", "standard", "compliance"],
    "mental-health": ["mental health", "psychological", "therapy", "wellbeing"],
    "interpersonal-dynamics": ["relationship", "interpersonal", "social", "connection"],
    "digital-life": ["digital", "online", "virtual", "internet", "cyber"],
    "communication": ["communication", "communicate", "message", "convey"],
    "cognition": ["cognition", "cognitive", "mental", "thinking", "mind"],
    "engineering": ["engineering", "engineer", "design", "build", "construct"],
    "measurement": ["measurement", "measure", "quantify", "metric"],
    "federalism": ["federal", "state", "federalism", "interstate"],
    "sociology": ["sociology", "social", "society", "community"],
    "finance": ["finance", "financial", "money", "investment", "banking"],
}

BROAD_TAG_KEYWORDS = {
    "science": ["science", "scientific", "research", "study", "experiment"],
    "technology": ["technology", "tech", "digital", "computer", "software", "engineering"],
    "arts": ["art", "artistic", "creative", "visual", "aesthetic"],
    "history": ["history", "historical", "past", "ancient", "medieval"],
    "politics": ["politics", "political", "government", "policy", "legislature"],
    "economics": ["economics", "economic", "market", "trade", "finance"],
    "ethics": ["ethics", "ethical", "moral", "value", "right and wrong"],
    "society": ["society", "social", "community", "culture", "people"],
    "geography": ["geography", "geographic", "region", "country", "territory"],
    "health": ["health", "medical", "medicine", "disease", "wellness"],
    "education": ["education", "educational", "learning", "teaching"],
    "law": ["law", "legal", "court", "legislation", "judicial"],
    "conflict": ["conflict", "war", "military", "battle", "combat"],
    "environment": ["environment", "environmental", "ecology", "climate", "nature"],
    "media": ["media", "journalism", "news", "press", "broadcast"],
    "philosophy": ["philosophy", "philosophical", "metaphysics", "logic"],
    "religion": ["religion", "religious", "faith", "sacred", "spiritual"],
    "psychology": ["psychology", "psychological", "mental", "cognitive", "behavior"],
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def load_tag_vocabulary() -> Dict:
    """Load the tag vocabulary JSON file."""
    with open(TAG_VOCABULARY_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_valid_tags(vocabulary: Dict) -> Dict[str, Set[str]]:
    """Extract valid tag IDs by tier as sets for fast lookup."""
    valid = {"broad": set(), "medium": set(), "specific": set()}
    for tier in ["broad", "medium", "specific"]:
        valid[tier] = {tag["id"] for tag in vocabulary["tags"].get(tier, [])}
    return valid

def detect_library_type(file_path: str) -> str:
    """Detect the library type from the file path."""
    path_lower = file_path.lower()
    for lib_type, patterns in LIBRARY_TYPE_PATTERNS.items():
        for pattern in patterns:
            if pattern in path_lower:
                return lib_type
    return "knowledge"

def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    return text.lower().strip()

def find_best_tag(text: str, keyword_map: Dict[str, List[str]], valid_tags: Set[str]) -> Optional[str]:
    """Find the best matching tag from a keyword map."""
    text_lower = normalize_text(text)
    scores = {}

    for tag, keywords in keyword_map.items():
        if tag not in valid_tags:
            continue
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += len(keyword.split())
        if score > 0:
            scores[tag] = score

    if scores:
        return max(scores, key=scores.get)
    return None

def find_multiple_tags(text: str, keyword_map: Dict[str, List[str]], valid_tags: Set[str],
                       exclude: Set[str] = None, limit: int = 3) -> List[str]:
    """Find multiple matching tags, excluding already-used ones."""
    if exclude is None:
        exclude = set()

    text_lower = normalize_text(text)
    scores = {}

    for tag, keywords in keyword_map.items():
        if tag not in valid_tags or tag in exclude:
            continue
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                score += len(keyword.split())
        if score > 0:
            scores[tag] = score

    sorted_tags = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
    return sorted_tags[:limit]

# =============================================================================
# MAIN TAGGING LOGIC
# =============================================================================

def generate_tags(library_type: str, book_name: str, chapter_name: str,
                  topics: List[str], valid_tags: Dict[str, Set[str]]) -> List[str]:
    """Generate 4 diverse tags for a chapter."""

    # Combine all text for matching
    topics_text = " ".join(topics) if topics else ""
    combined_text = f"{book_name} {chapter_name} {topics_text}"

    used_tags: Set[str] = set()
    final_tags: List[str] = []

    # TAG 1: Broad domain tag
    broad_tag = find_best_tag(combined_text, BROAD_TAG_KEYWORDS, valid_tags["broad"])
    if not broad_tag:
        type_to_broad = {
            "geography": "geography",
            "knowledge": "education",
            "practical": "society",
            "perspectives": "philosophy",
            "event": "politics",
            "candidate": "politics",
            "infrastructure": "technology"
        }
        broad_tag = type_to_broad.get(library_type, "education")

    final_tags.append(broad_tag)
    used_tags.add(broad_tag)

    # TAG 2: Medium conceptual lens
    medium_tag = find_best_tag(combined_text, MEDIUM_TAG_KEYWORDS, valid_tags["medium"])
    if medium_tag and medium_tag not in used_tags:
        final_tags.append(medium_tag)
        used_tags.add(medium_tag)
    else:
        # Fallback medium tags by library type
        fallbacks = {
            "infrastructure": "systems-thinking",
            "knowledge": "epistemology",
            "practical": "application",
            "perspectives": "critical-thinking",
            "event": "governance",
            "geography": "identity",
        }
        fallback = fallbacks.get(library_type, "analysis")
        final_tags.append(fallback)
        used_tags.add(fallback)

    # TAG 3: Specific tag
    specific_tag = find_best_tag(combined_text, SPECIFIC_TAG_KEYWORDS, valid_tags["specific"])
    if specific_tag and specific_tag not in used_tags:
        final_tags.append(specific_tag)
        used_tags.add(specific_tag)
    else:
        # Try another medium tag
        medium_alts = find_multiple_tags(combined_text, MEDIUM_TAG_KEYWORDS, valid_tags["medium"], used_tags)
        if medium_alts:
            final_tags.append(medium_alts[0])
            used_tags.add(medium_alts[0])
        else:
            final_tags.append("methodology")
            used_tags.add("methodology")

    # TAG 4: Another specific or cross-library tag
    specific_alts = find_multiple_tags(combined_text, SPECIFIC_TAG_KEYWORDS, valid_tags["specific"], used_tags)
    if specific_alts:
        final_tags.append(specific_alts[0])
        used_tags.add(specific_alts[0])
    else:
        # Fallback specific tags
        fallbacks = {
            "infrastructure": "architecture",
            "knowledge": "education",
            "practical": "personal-finance",
            "perspectives": "media-literacy",
            "event": "journalism",
            "geography": "americas",
        }
        fallback = fallbacks.get(library_type, "education")
        if fallback not in used_tags:
            final_tags.append(fallback)
        else:
            final_tags.append("education")

    return final_tags[:4]

# =============================================================================
# MAIN PROCESSING
# =============================================================================

def process_book(file_path: str, dry_run: bool = False) -> int:
    """Process a standalone book file and add tags to all chapters."""
    vocabulary = load_tag_vocabulary()
    valid_tags = get_valid_tags(vocabulary)
    library_type = detect_library_type(file_path)

    print(f"\nProcessing: {file_path}")
    print(f"Library type: {library_type}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    book_name = data.get("name", "Unknown")
    chapters_tagged = 0

    for chapter in data.get("chapters", []):
        chapter_name = chapter.get("name", "")
        topics = chapter.get("topics", [])

        new_tags = generate_tags(library_type, book_name, chapter_name, topics, valid_tags)

        if dry_run:
            print(f"  {chapter_name}")
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

    return chapters_tagged

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not args:
        print("Error: No file specified")
        sys.exit(1)

    file_path = args[0]

    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    tagged = process_book(file_path, dry_run)

    print(f"\n{'=' * 60}")
    print(f"Done! {'Would tag' if dry_run else 'Tagged'} {tagged} chapters.")

if __name__ == "__main__":
    main()
