#!/usr/bin/env python3
"""
TruthAngel Auto-Tagger v2.0
Automatically applies 4 diverse tags to each chapter in library JSON files.

Usage:
    python auto-tagger.py <library_file.json>
    python auto-tagger.py --all              # Tag all libraries
    python auto-tagger.py --dry-run <file>   # Preview without saving

Tag Strategy (4 tags per chapter):
    Tag 1 (Broad): Domain anchor - the primary knowledge domain
    Tag 2 (Medium): Conceptual lens - how we're looking at the topic
    Tag 3 (Medium/Specific): Subject differentiator - what makes this unique
    Tag 4 (Specific): Precise identifier - the most specific applicable tag
"""

import json
import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
TAG_VOCABULARY_PATH = SCRIPT_DIR / "tag-vocabulary.json"

# Library type detection patterns
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
# COMPREHENSIVE KEYWORD MAPPINGS
# =============================================================================

# Maps keywords to specific tags - searched in order of specificity
SPECIFIC_TAG_KEYWORDS = {
    # Art periods and movements
    "prehistoric": ["prehistoric", "cave painting", "cave art", "paleolithic", "neolithic", "lascaux", "altamira"],
    "ancient-egypt": ["egypt", "egyptian", "pharaoh", "pyramid", "hieroglyph", "nile", "tutankhamun"],
    "ancient-greece": ["greek", "greece", "hellenistic", "parthenon", "acropolis", "athens", "sparta"],
    "ancient-rome": ["roman", "rome", "colosseum", "gladiator", "emperor", "latin", "pompeii"],
    "medieval": ["medieval", "middle ages", "gothic", "cathedral", "feudal", "knight", "crusade", "romanesque"],
    "renaissance": ["renaissance", "michelangelo", "leonardo", "raphael", "botticelli", "medici", "florence", "quattrocento"],
    "baroque": ["baroque", "rococo", "caravaggio", "rembrandt", "vermeer", "rubens", "bernini", "baroque period"],
    "romanticism": ["romantic period", "romanticism", "turner", "delacroix", "goya", "caspar david friedrich", "romantic movement"],
    "impressionism": ["impressionist", "impressionism", "monet", "renoir", "degas", "pissarro", "sisley", "manet"],
    "surrealism": ["surreal", "surrealism", "dali", "magritte", "ernst", "miro", "dream", "unconscious"],
    "abstract": ["abstract", "abstraction", "kandinsky", "mondrian", "malevich", "non-representational", "non-objective"],
    "expressionism": ["expressionist", "expressionism", "munch", "kirchner", "die brucke", "emotional intensity"],
    "cubism": ["cubism", "cubist", "picasso", "braque", "leger", "gris", "fragmented"],
    "pop-art": ["pop art", "warhol", "lichtenstein", "rauschenberg", "johns", "consumerism", "mass media"],
    "minimalism": ["minimal", "minimalism", "minimalist", "judd", "flavin", "andre", "simplicity"],
    "contemporary": ["contemporary", "21st century", "current", "today", "modern day", "recent"],
    "realism": ["realism", "realist", "courbet", "millet", "naturalism", "truthful"],
    "classical": ["classical", "neoclassical", "davidian", "canova", "ingres", "academic"],

    # Art forms and media
    "painting": ["painting", "paint", "oil", "watercolor", "acrylic", "fresco", "tempera", "gouache"],
    "sculpture": ["sculpture", "sculpt", "carving", "bronze", "marble", "clay", "statue", "bust", "relief"],
    "drawing": ["drawing technique", "sketch", "pencil drawing", "charcoal drawing", "graphite", "conte crayon", "line drawing"],
    "printmaking": ["print", "etching", "lithograph", "woodcut", "engraving", "screenprint", "intaglio", "relief print"],
    "photography": ["photography", "photograph", "camera", "exposure", "darkroom", "aperture", "shutter"],
    "ceramics": ["ceramic", "pottery", "clay", "kiln", "glaze", "porcelain", "stoneware", "earthenware"],
    "textiles": ["textile", "weaving", "fiber", "fabric", "tapestry", "embroidery", "quilt"],
    "glass-art": ["glass", "stained glass", "glassblowing", "fused glass", "lampwork"],
    "metalwork": ["metalwork", "jewelry", "goldsmith", "silversmith", "forge", "bronze casting"],
    "woodwork": ["woodwork", "carving", "furniture", "marquetry", "woodturning"],
    "digital-art": ["digital art", "computer art", "generative", "nft", "pixel", "vector", "3d render"],
    "mixed-media": ["mixed media", "collage", "assemblage", "combine", "multimedia"],
    "installation": ["installation", "site-specific", "immersive", "environmental art"],
    "performance-art": ["performance art", "happening", "body art", "live art", "action art"],
    "video-art": ["video art", "video installation", "new media", "time-based"],
    "street-art": ["street art", "graffiti", "mural", "banksy", "urban art", "stencil"],
    "conceptual-art": ["conceptual", "idea art", "dematerialized", "text art"],

    # Music genres and forms
    "classical-music": ["symphony", "orchestra", "concerto", "sonata", "chamber music", "beethoven", "mozart", "bach", "brahms", "chopin"],
    "opera": ["opera", "aria", "libretto", "soprano", "tenor", "verdi", "puccini", "wagner"],
    "ballet": ["ballet", "ballerina", "choreograph", "nutcracker", "swan lake", "pas de deux"],
    "jazz": ["jazz", "improvisation", "bebop", "swing", "blues", "ragtime", "ellington", "coltrane", "miles davis"],
    "rock-music": ["rock", "rock and roll", "guitar", "beatles", "rolling stones", "punk", "grunge", "metal"],
    "electronic-music": ["electronic", "synthesizer", "edm", "techno", "house", "ambient", "drum and bass"],
    "world-music": ["world music", "folk music", "traditional music", "ethnic", "gamelan", "raga"],

    # Literary forms
    "poetry": ["poetry", "poem", "verse", "sonnet", "haiku", "rhyme", "meter", "stanza"],
    "fiction": ["fiction", "novel", "short story", "narrative", "prose", "character", "plot"],
    "drama": ["drama", "playwright", "stage play", "dramatic", "theatrical", "dramaturgy"],
    "non-fiction": ["non-fiction", "essay", "memoir", "biography", "journalism", "documentary"],

    # Film and media
    "film": ["film", "cinema", "movie", "director", "screenplay", "cinematography", "editing"],
    "documentary": ["documentary", "docufilm", "non-fiction film", "journalism"],
    "animation": ["animation", "animated", "cartoon", "anime", "pixar", "stop motion"],
    "theater": ["theater", "theatre", "stage", "broadway", "west end", "drama", "acting"],
    "dance": ["dance", "dancer", "choreograph", "modern dance", "contemporary dance", "folk dance"],

    # Science branches - Physics
    "physics": ["physics", "physical", "force", "energy", "motion", "wave"],
    "quantum-mechanics": ["quantum", "quanta", "wave function", "heisenberg", "schrodinger", "superposition", "entanglement"],
    "thermodynamics": ["thermodynamic", "heat", "entropy", "thermal", "temperature", "energy transfer"],
    "electromagnetism": ["electromagnetic", "electric", "magnetic", "maxwell", "faraday", "inductance"],
    "mechanics": ["mechanics", "newton", "momentum", "velocity", "acceleration", "friction", "dynamics"],
    "optics": ["optics", "optical", "light", "lens", "refraction", "reflection", "laser"],
    "relativity": ["relativity", "einstein", "spacetime", "lorentz", "time dilation", "mass-energy"],
    "particle-physics": ["particle", "quark", "lepton", "boson", "hadron", "standard model", "cern", "accelerator"],
    "astrophysics": ["astrophysics", "stellar", "galactic", "cosmological", "black hole", "supernova"],
    "cosmology": ["cosmology", "big bang", "universe", "cosmic", "expansion", "dark matter", "dark energy"],

    # Science branches - Chemistry
    "chemistry": ["chemistry", "chemical", "molecule", "reaction", "element", "compound"],
    "organic-chemistry": ["organic", "carbon", "hydrocarbon", "polymer", "synthesis", "functional group"],
    "inorganic-chemistry": ["inorganic", "metal", "mineral", "coordination", "crystal"],
    "biochemistry": ["biochem", "protein", "enzyme", "metabolism", "dna", "rna", "amino acid"],

    # Science branches - Biology
    "biology": ["biology", "biological", "organism", "life", "living"],
    "cell-biology": ["cell", "cellular", "organelle", "membrane", "mitosis", "cytoplasm"],
    "genetics": ["genetics", "genome", "dna", "heredity", "mutation", "chromosome", "crispr", "hereditary"],
    "evolution-biology": ["evolution", "darwin", "natural selection", "speciation", "adaptation", "phylogen"],
    "microbiology": ["microb", "bacteria", "virus", "pathogen", "microorganism", "infectious"],
    "ecology": ["ecology", "ecosystem", "habitat", "biodiversity", "species interaction", "food web"],
    "botany": ["botany", "plant", "flora", "photosynthesis", "botanical", "vegetation"],
    "zoology": ["zoology", "animal", "fauna", "mammal", "vertebrate", "invertebrate"],
    "neuroscience": ["neuro", "brain", "neuron", "synapse", "cognitive", "neural"],

    # Science branches - Earth sciences
    "geology": ["geology", "geological", "rock", "mineral", "tectonic", "volcano", "earthquake", "stratigraphy"],
    "meteorology": ["meteorology", "weather", "atmospheric", "climate", "storm", "precipitation", "forecast"],
    "oceanography": ["oceanography", "marine", "ocean", "sea", "tide", "current", "deep sea"],
    "astronomy": ["astronomy", "star", "planet", "galaxy", "telescope", "celestial", "solar system"],

    # Technology and computing
    "computer-science": ["computer science", "algorithm", "data structure", "computation", "turing"],
    "software-engineering": ["software", "programming", "code", "developer", "agile", "scrum"],
    "ai-ml": ["artificial intelligence", "machine learning", "neural network", "deep learning", "nlp", "computer vision"],
    "robotics": ["robot", "robotic", "autonomous", "automation", "sensor", "actuator"],
    "cybersecurity": ["cybersecurity", "hacking", "malware", "firewall", "encryption", "vulnerability"],
    "web-development": ["web development", "html", "css", "javascript", "frontend", "backend", "fullstack"],
    "mobile-development": ["mobile app", "ios", "android", "swift", "kotlin", "react native"],
    "databases": ["database", "sql", "nosql", "mongodb", "postgresql", "data storage"],
    "cloud-computing": ["cloud", "aws", "azure", "gcp", "serverless", "container", "kubernetes"],
    "version-control": ["git", "version control", "github", "gitlab", "commit", "branch", "merge"],
    "data-science": ["data science", "analytics", "visualization", "pandas", "jupyter", "big data"],

    # Energy and power
    "power-generation": ["power generation", "generator", "turbine", "power plant", "electricity production"],
    "renewable-energy": ["renewable", "clean energy", "green energy", "sustainable energy"],
    "solar-power": ["solar", "photovoltaic", "pv", "solar panel", "solar cell", "solar thermal"],
    "wind-power": ["wind power", "wind turbine", "wind farm", "offshore wind", "onshore wind"],
    "hydropower": ["hydropower", "hydroelectric", "hydroelectricity", "water turbine", "water power plant"],
    "nuclear-energy": ["nuclear power", "reactor", "fission", "uranium", "plutonium", "nuclear plant"],
    "fossil-fuels": ["fossil fuel", "coal power", "oil drilling", "natural gas", "petroleum industry", "crude oil"],
    "geothermal": ["geothermal", "earth heat", "hot spring", "geothermal plant"],
    "grid-systems": ["power grid", "electrical grid", "grid operator", "transmission grid", "distribution"],
    "transmission": ["transmission", "high voltage", "hvdc", "power line", "substation", "transformer"],
    "energy-storage": ["battery", "energy storage", "lithium", "pumped hydro", "flywheel", "capacitor"],
    "smart-grid": ["smart grid", "demand response", "load balancing", "grid modernization", "advanced metering"],

    # Design fields
    "architecture": ["architecture", "architect", "architectural", "building design", "facade", "blueprint"],
    "graphic-design": ["graphic design", "typography", "layout", "visual design", "branding"],
    "product-design": ["product design", "industrial design", "prototype", "manufacturing"],
    "user-experience": ["ux", "user experience", "usability", "interaction design", "user research"],

    # Art techniques
    "color-theory": ["color theory", "color wheel", "hue", "saturation", "value", "complementary", "palette"],
    "light-shadow": ["light and shadow", "chiaroscuro", "value", "tonal", "shading", "highlight"],
    "perspective": ["perspective", "vanishing point", "foreshortening", "depth", "spatial"],
    "figure-drawing": ["figure drawing", "anatomy", "life drawing", "human form", "gesture"],
    "landscape": ["landscape", "plein air", "scenery", "vista", "nature scene"],
    "portrait": ["portrait", "portraiture", "likeness", "face", "bust", "self-portrait"],
    "still-life": ["still life", "nature morte", "arrangement", "objects"],

    # Critical thinking and reasoning
    "cognitive-bias": ["cognitive bias", "confirmation bias", "anchoring", "availability heuristic", "hindsight"],
    "logical-fallacies": ["fallacy", "fallacies", "ad hominem", "straw man", "false dichotomy", "slippery slope"],
    "source-evaluation": ["source evaluation", "credibility", "reliability", "fact check", "verification"],
    "media-literacy": ["media literacy", "news literacy", "information literacy", "digital literacy"],
    "scientific-method": ["scientific method", "hypothesis", "experiment", "peer review", "reproducibility"],

    # Geopolitical regions
    "russia-ukraine": ["ukraine", "russia", "kremlin", "putin", "kyiv", "moscow", "donbas", "crimea"],
    "israel-palestine": ["israel", "palestine", "gaza", "hamas", "netanyahu", "west bank", "idf"],
    "china-taiwan": ["taiwan strait", "cross-strait", "taiwanese", "taipei", "beijing-taipei", "prc-roc"],
    "middle-east": ["middle east", "arab", "persian", "gulf", "levant", "mesopotamia"],
    "africa": ["africa", "african", "sahara", "subsaharan", "maghreb", "horn of africa"],
    "asia": ["asia", "asian", "east asia", "southeast asia", "south asia", "central asia"],
    "europe": ["europe", "european", "eu", "western europe", "eastern europe", "nordic"],
    "americas": ["americas", "north america", "south america", "latin america", "caribbean"],
    "oceania": ["oceania", "pacific", "australasia", "polynesia", "melanesia"],

    # Political and social
    "us-politics": ["american politics", "congress", "senate", "house of representatives", "white house"],
    "elections": ["election", "vote", "ballot", "campaign", "candidate", "polling"],
    "trump": ["trump", "maga", "january 6", "jan 6", "mar-a-lago"],
    "journalism": ["journalism", "journalist", "reporter", "news media", "press freedom", "editorial board", "investigative reporting"],
    "immigration": ["immigration", "immigrant", "border", "visa", "asylum", "deportation"],
    "policing": ["police", "policing", "law enforcement", "officer", "patrol"],
    "civil-rights": ["civil rights", "equality", "discrimination", "segregation", "voting rights"],

    # Finance and economics
    "personal-finance": ["personal finance", "budget", "saving", "investing", "retirement", "debt"],
    "economics-theory": ["economic theory", "keynesian", "monetarist", "supply and demand", "market"],
    "monetary-policy": ["monetary policy", "federal reserve", "interest rate", "inflation", "central bank"],
    "fiscal-policy": ["fiscal policy", "taxation", "government spending", "deficit", "stimulus"],
}

# Maps keywords to medium-tier conceptual tags
MEDIUM_TAG_KEYWORDS = {
    # Analytical and methodological lenses
    "critical-thinking": ["critical thinking", "analyze", "evaluate", "reasoning", "logic", "argument"],
    "systems-thinking": ["systems thinking", "interconnected", "holistic", "complexity", "feedback loop"],
    "epistemology": ["epistemology", "knowledge", "truth", "belief", "justification", "certainty"],
    "methodology": ["methodology", "method", "approach", "framework", "systematic"],
    "empiricism": ["empirical", "observation", "evidence", "data-driven", "experimental"],
    "theory": ["theory", "theoretical", "conceptual", "model", "framework", "abstract"],
    "application": ["application", "applied", "practical", "real-world", "implementation"],
    "analysis": ["analysis", "examine", "investigate", "breakdown", "dissect"],
    "synthesis": ["synthesis", "combine", "integrate", "unify", "bring together"],

    # Creative and artistic lenses
    "aesthetics": ["aesthetic", "beauty", "taste", "sensory", "perception", "sublime"],
    "expression": ["expression", "expressive", "communicate", "convey", "voice"],
    "craft": ["craft", "craftsmanship", "skill", "mastery", "artisan", "handmade"],
    "technique": ["technique", "technical", "method", "process", "procedure"],
    "composition": ["composition", "arrange", "structure", "organize", "layout"],
    "narrative": ["narrative", "story", "storytelling", "plot", "character development"],
    "tradition": ["tradition", "traditional", "heritage", "classical", "established"],
    "innovation": ["innovation", "innovative", "new", "breakthrough", "pioneering", "revolutionary"],
    "experimentation": ["experiment", "experimental", "avant-garde", "explore", "test"],
    "modernism": ["modern", "modernist", "contemporary", "20th century", "break from tradition"],
    "postmodernism": ["postmodern", "deconstruction", "irony", "pastiche", "meta"],

    # Scientific lenses
    "discovery": ["discovery", "discover", "found", "reveal", "uncover"],
    "measurement": ["measurement", "measure", "quantify", "metric", "calibrate"],
    "modeling": ["model", "simulation", "represent", "approximate"],
    "prediction": ["prediction", "predict", "forecast", "anticipate", "project"],
    "causation": ["causation", "cause", "effect", "mechanism", "why"],
    "verification": ["verification", "verify", "confirm", "validate", "prove"],
    "replication": ["replication", "reproduce", "repeat", "confirm"],
    "uncertainty": ["uncertainty", "uncertain", "probability", "risk", "unknown"],
    "scale": ["scale", "micro", "macro", "magnitude", "level"],
    "complexity": ["complexity", "complex", "emergent", "nonlinear", "chaotic"],
    "frontiers": ["frontier", "cutting edge", "latest", "emerging", "future"],
    "foundations": ["foundation", "fundamental", "basic", "core", "essential"],
    "interdisciplinary": ["interdisciplinary", "cross-disciplinary", "multidisciplinary"],

    # Social and political lenses
    "democracy": ["democracy", "democratic", "voting", "representation", "civic"],
    "governance": ["governance", "govern", "administration", "oversight", "regulation"],
    "human-rights": ["human rights", "rights", "freedom", "liberty", "dignity"],
    "justice": ["justice", "fair", "equitable", "remedy", "court"],
    "accountability": ["accountability", "accountable", "responsible", "answerable"],
    "transparency": ["transparency", "transparent", "open", "disclosure"],
    "representation": ["representation", "represent", "voice", "inclusion"],
    "activism": ["activism", "activist", "movement", "protest", "advocacy"],
    "inequality": ["inequality", "unequal", "disparity", "gap", "divide"],
    "colonialism": ["colonial", "colonialism", "imperialism", "empire", "post-colonial"],
    "authoritarianism": ["authoritarian", "autocracy", "dictatorship", "totalitarian"],
    "nationalism": ["nationalism", "nationalist", "patriotism", "nation-state"],
    "globalization": ["globalization", "global", "international", "worldwide", "transnational"],

    # Cultural and identity lenses
    "identity": ["identity", "belonging", "self", "who we are"],
    "cultural-heritage": ["heritage", "legacy", "tradition", "cultural", "preservation"],
    "migration": ["migration", "immigrant", "emigrant", "diaspora", "displacement"],
    "spirituality": ["spiritual", "sacred", "divine", "transcendent", "faith"],

    # Communication lenses
    "rhetoric": ["rhetoric", "persuasion", "argument", "discourse", "oratory"],
    "propaganda": ["propaganda", "influence", "manipulation", "messaging"],
    "misinformation": ["misinformation", "disinformation", "fake news", "false"],
    "communication": ["communication", "communicate", "message", "convey"],
    "cognition": ["cognition", "cognitive", "mental", "thinking", "mind"],
    "bias": ["bias", "prejudice", "stereotype", "discrimination"],

    # Technical and practical lenses
    "infrastructure": ["infrastructure", "system", "network", "facility"],
    "security": ["security", "secure", "protect", "defense", "threat"],
    "sustainability": ["sustainability", "sustainable", "renewable", "green", "eco"],
    "energy": ["energy", "power", "electricity", "fuel"],
    "development": ["development", "growth", "progress", "advancement"],
    "regulation": ["regulation", "regulate", "rule", "standard", "compliance"],

    # Historical lenses
    "evolution": ["evolution", "evolve", "develop", "change over time", "gradual"],
    "revolution": ["revolution", "revolutionary", "radical change", "transformation", "upheaval"],
    "legacy": ["legacy", "lasting", "enduring", "influence", "impact"],
    "influence": ["influence", "influenced", "shaped", "affected", "inspired"],
    "controversy": ["controversy", "controversial", "debate", "disputed", "contested"],

    # Personal and interpersonal
    "mental-health": ["mental health", "psychological", "therapy", "wellbeing", "emotional"],
    "interpersonal-dynamics": ["relationship", "interpersonal", "social", "connection", "bond"],
    "workplace-dynamics": ["workplace", "career", "job", "employment", "professional"],
    "digital-life": ["digital", "online", "virtual", "internet", "cyber"],
    "privacy": ["privacy", "private", "surveillance", "data protection"],
    "free-speech": ["free speech", "expression", "censorship", "first amendment"],
    "finance": ["finance", "financial", "money", "investment", "banking"],
    "climate-change": ["climate change", "global warming", "carbon", "emission", "greenhouse"],
    "diplomacy": ["diplomacy", "diplomatic", "foreign policy", "international relations"],
}

# Maps keywords to broad-tier domain tags
BROAD_TAG_KEYWORDS = {
    "science": ["science", "scientific", "research", "study", "experiment", "hypothesis"],
    "technology": ["technology", "tech", "digital", "computer", "software", "engineering"],
    "arts": ["art", "artistic", "creative", "visual", "aesthetic", "expression"],
    "history": ["history", "historical", "past", "ancient", "medieval", "century"],
    "politics": ["politics", "political", "government", "policy", "legislature"],
    "economics": ["economics", "economic", "market", "trade", "finance", "fiscal"],
    "ethics": ["ethics", "ethical", "moral", "value", "right and wrong"],
    "society": ["society", "social", "community", "culture", "people"],
    "geography": ["geography", "geographic", "region", "country", "territory", "land"],
    "health": ["health", "medical", "medicine", "disease", "wellness", "healthcare"],
    "education": ["education", "educational", "learning", "teaching", "pedagogy"],
    "law": ["law", "legal", "court", "legislation", "judicial", "constitution"],
    "conflict": ["conflict", "war", "military", "battle", "combat", "peace"],
    "environment": ["environment", "environmental", "ecology", "climate", "nature"],
    "media": ["media", "journalism", "news", "press", "broadcast", "publication"],
    "philosophy": ["philosophy", "philosophical", "metaphysics", "logic", "epistemology"],
    "religion": ["religion", "religious", "faith", "sacred", "spiritual", "divine"],
    "psychology": ["psychology", "psychological", "mental", "cognitive", "behavior", "mind"],
}

# =============================================================================
# CONTEXT-AWARE FALLBACK ALTERNATIVES
# =============================================================================

# When a duplicate is detected, use these context-aware alternatives
FALLBACK_ALTERNATIVES = {
    # For arts content
    "arts": {
        "medium": ["aesthetics", "expression", "craft", "technique", "tradition", "innovation", "composition", "narrative"],
        "specific": ["visual-arts", "art-history", "painting", "sculpture", "drawing", "photography", "music", "theater", "dance", "film"]
    },
    # For science content
    "science": {
        "medium": ["methodology", "empiricism", "discovery", "measurement", "theory", "analysis", "verification", "frontiers"],
        "specific": ["physics", "chemistry", "biology", "astronomy", "earth-science", "neuroscience", "genetics", "ecology"]
    },
    # For technology content
    "technology": {
        "medium": ["innovation", "systems-thinking", "application", "infrastructure", "security", "development"],
        "specific": ["computer-science", "software-engineering", "ai-ml", "robotics", "cybersecurity", "data-science"]
    },
    # For history content
    "history": {
        "medium": ["cultural-heritage", "legacy", "evolution", "influence", "tradition", "revolution"],
        "specific": ["ancient-history", "medieval", "renaissance", "modern-history", "world-wars", "cold-war"]
    },
    # For philosophy content
    "philosophy": {
        "medium": ["epistemology", "ethics", "critical-thinking", "rhetoric", "analysis", "theory"],
        "specific": ["logical-fallacies", "cognitive-bias", "ethics", "ancient-greece", "enlightenment"]
    },
    # For politics content
    "politics": {
        "medium": ["democracy", "governance", "accountability", "representation", "activism", "justice"],
        "specific": ["us-politics", "elections", "civil-rights", "policing", "constitutional-law"]
    },
    # For geography content
    "geography": {
        "medium": ["identity", "cultural-heritage", "development", "migration", "globalization", "nationalism"],
        "specific": ["americas", "europe", "asia", "africa", "middle-east", "oceania"]
    },
    # For infrastructure content
    "technology": {
        "medium": ["systems-thinking", "sustainability", "security", "innovation", "regulation", "accountability"],
        "specific": ["grid-systems", "power-generation", "transmission", "renewable-energy", "data-centers"]
    },
    # For perspectives/critical thinking content
    "philosophy": {
        "medium": ["critical-thinking", "bias", "cognition", "rhetoric", "misinformation", "communication"],
        "specific": ["cognitive-bias", "logical-fallacies", "media-literacy", "source-evaluation", "journalism"]
    },
    # Default fallbacks
    "default": {
        "medium": ["analysis", "synthesis", "application", "theory", "methodology", "development"],
        "specific": ["education", "research-methods", "interdisciplinary"]
    }
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
    """Normalize text for matching - lowercase and clean."""
    return text.lower().strip()

def find_best_tag(text: str, keyword_map: Dict[str, List[str]], valid_tags: Set[str]) -> Optional[str]:
    """Find the best matching tag from a keyword map."""
    text_lower = normalize_text(text)

    # Score each potential tag by number of keyword matches and specificity
    scores = {}
    for tag, keywords in keyword_map.items():
        if tag not in valid_tags:
            continue
        score = 0
        for keyword in keywords:
            if keyword.lower() in text_lower:
                # Longer keywords are more specific, give them more weight
                score += len(keyword.split())
        if score > 0:
            scores[tag] = score

    if scores:
        # Return the tag with the highest score
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

    # Sort by score descending and return top matches
    sorted_tags = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
    return sorted_tags[:limit]

def get_fallback_tag(broad_tag: str, tier: str, used_tags: Set[str], valid_tags: Set[str]) -> Optional[str]:
    """Get a fallback tag based on the broad category context."""
    alternatives = FALLBACK_ALTERNATIVES.get(broad_tag, FALLBACK_ALTERNATIVES["default"])
    tier_alternatives = alternatives.get(tier, [])

    for alt in tier_alternatives:
        if alt in valid_tags and alt not in used_tags:
            return alt
    return None

# =============================================================================
# MAIN TAGGING LOGIC
# =============================================================================

def generate_tags(library_type: str, shelf_name: str, book_name: str,
                  chapter_name: str, library_name: str, valid_tags: Dict[str, Set[str]]) -> List[str]:
    """Generate 4 diverse tags for a chapter using comprehensive keyword matching."""

    # Combine all text for matching
    combined_text = f"{library_name} {shelf_name} {book_name} {chapter_name}"

    used_tags: Set[str] = set()
    final_tags: List[str] = []

    # -------------------------------------------------------------------------
    # TAG 1: Broad domain tag
    # -------------------------------------------------------------------------
    broad_tag = find_best_tag(combined_text, BROAD_TAG_KEYWORDS, valid_tags["broad"])

    # Library type fallbacks if no keyword match
    if not broad_tag:
        type_to_broad = {
            "geography": "geography",
            "knowledge": "education",
            "practical": "society",
            "perspectives": "philosophy",
            "event": "conflict",
            "candidate": "politics",
            "infrastructure": "technology"
        }
        broad_tag = type_to_broad.get(library_type, "education")

    final_tags.append(broad_tag)
    used_tags.add(broad_tag)

    # -------------------------------------------------------------------------
    # TAG 2: Medium conceptual lens
    # -------------------------------------------------------------------------
    medium_tag = find_best_tag(combined_text, MEDIUM_TAG_KEYWORDS, valid_tags["medium"])

    if medium_tag and medium_tag not in used_tags:
        final_tags.append(medium_tag)
        used_tags.add(medium_tag)
    else:
        # Get a fallback based on broad category
        fallback = get_fallback_tag(broad_tag, "medium", used_tags, valid_tags["medium"])
        if fallback:
            final_tags.append(fallback)
            used_tags.add(fallback)
        else:
            final_tags.append("analysis")
            used_tags.add("analysis")

    # -------------------------------------------------------------------------
    # TAG 3: Second medium or specific differentiator
    # -------------------------------------------------------------------------
    # Try to find a specific tag first for more diversity
    specific_tag = find_best_tag(combined_text, SPECIFIC_TAG_KEYWORDS, valid_tags["specific"])

    if specific_tag and specific_tag not in used_tags:
        final_tags.append(specific_tag)
        used_tags.add(specific_tag)
    else:
        # Try another medium tag
        medium_alternatives = find_multiple_tags(combined_text, MEDIUM_TAG_KEYWORDS,
                                                  valid_tags["medium"], used_tags, limit=3)
        if medium_alternatives:
            final_tags.append(medium_alternatives[0])
            used_tags.add(medium_alternatives[0])
        else:
            fallback = get_fallback_tag(broad_tag, "medium", used_tags, valid_tags["medium"])
            if fallback:
                final_tags.append(fallback)
                used_tags.add(fallback)
            else:
                final_tags.append("application")
                used_tags.add("application")

    # -------------------------------------------------------------------------
    # TAG 4: Most specific tag possible
    # -------------------------------------------------------------------------
    # Find additional specific tags
    specific_alternatives = find_multiple_tags(combined_text, SPECIFIC_TAG_KEYWORDS,
                                               valid_tags["specific"], used_tags, limit=5)

    if specific_alternatives:
        final_tags.append(specific_alternatives[0])
        used_tags.add(specific_alternatives[0])
    else:
        # Use fallback specific tags
        fallback = get_fallback_tag(broad_tag, "specific", used_tags, valid_tags["specific"])
        if fallback:
            final_tags.append(fallback)
            used_tags.add(fallback)
        else:
            # Last resort - pick something relevant to library type
            last_resort = {
                "geography": "travel",
                "knowledge": "education",
                "practical": "personal-finance",
                "perspectives": "media-literacy",
                "event": "geopolitics",
                "candidate": "elections",
                "infrastructure": "engineering"
            }
            final_tag = last_resort.get(library_type, "education")
            if final_tag not in used_tags:
                final_tags.append(final_tag)
            else:
                final_tags.append("research-methods")

    # Ensure exactly 4 tags
    while len(final_tags) < 4:
        fallback = get_fallback_tag(broad_tag, "specific", set(final_tags), valid_tags["specific"])
        if fallback and fallback not in final_tags:
            final_tags.append(fallback)
        else:
            # Absolute fallback
            for emergency in ["interdisciplinary", "methodology", "analysis", "education"]:
                if emergency not in final_tags and emergency in valid_tags["medium"]:
                    final_tags.append(emergency)
                    break
            else:
                final_tags.append("education")

    return final_tags[:4]


# =============================================================================
# MAIN PROCESSING
# =============================================================================

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
    tag_distribution: Dict[str, int] = {}

    # Navigate the JSON structure: library -> shelves -> books -> chapters
    library_name = data.get("library", "Unknown")

    for shelf in data.get("shelves", []):
        shelf_name = shelf.get("name", "")

        for book in shelf.get("books", []):
            book_name = book.get("name", "")

            for chapter in book.get("chapters", []):
                chapter_name = chapter.get("name", "")

                # Generate new tags
                new_tags = generate_tags(library_type, shelf_name, book_name,
                                         chapter_name, library_name, valid_tags)

                # Track tag distribution
                for tag in new_tags:
                    tag_distribution[tag] = tag_distribution.get(tag, 0) + 1

                if dry_run:
                    try:
                        print(f"  [{book_name}] {chapter_name}")
                        print(f"    -> {new_tags}")
                    except UnicodeEncodeError:
                        print(f"  [{book_name.encode('ascii', 'replace').decode()}] {chapter_name.encode('ascii', 'replace').decode()}")
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

    # Print tag diversity stats
    unique_tags = len(tag_distribution)
    print(f"Tag diversity: {unique_tags} unique tags used")

    # Show most common tags
    if tag_distribution:
        sorted_tags = sorted(tag_distribution.items(), key=lambda x: x[1], reverse=True)
        print("Top 10 tags:")
        for tag, count in sorted_tags[:10]:
            print(f"  {tag}: {count}")

    return chapters_tagged, unique_tags

def find_all_libraries() -> List[str]:
    """Find all library JSON files to process."""
    libraries = []
    base_dir = SCRIPT_DIR

    for lib_type in LIBRARY_TYPE_PATTERNS.keys():
        lib_dir = base_dir / f"{lib_type}-libraries"
        if lib_dir.exists():
            for json_file in lib_dir.glob("*.json"):
                # Skip inventory and other meta files
                if "inventory" in json_file.name.lower():
                    continue
                if "questions" in json_file.name.lower():
                    continue
                if "bare" in json_file.name.lower():
                    continue
                libraries.append(str(json_file))

    return sorted(libraries)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nAvailable libraries:")
        for lib in find_all_libraries():
            print(f"  {lib}")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--all" in sys.argv:
        libraries = find_all_libraries()
        print(f"Found {len(libraries)} libraries to process")
    else:
        libraries = args

    total_tagged = 0
    total_unique = 0
    for lib_path in libraries:
        if not os.path.exists(lib_path):
            print(f"File not found: {lib_path}")
            continue
        tagged, unique = process_library(lib_path, dry_run)
        total_tagged += tagged
        total_unique = max(total_unique, unique)

    print(f"\n{'=' * 60}")
    print(f"Total chapters {'would be ' if dry_run else ''}tagged: {total_tagged}")
    print(f"Maximum unique tags in a single library: {total_unique}")

if __name__ == "__main__":
    main()
