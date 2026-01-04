# TruthAngel/Quarex Tag Rules

Use this document when assigning tags to chapters in Quarex book JSON files.

## Core Rules

1. **Exactly 4 tags per chapter** - No more, no less
2. **Tags must come from the vocabulary** - Never invent new tags
3. **Tags are lowercase with hyphens** - e.g., `ai-ml`, `us-politics`, `climate-change`
4. **Diversity is key** - Choose tags from different tiers when possible

## Tag Tiers (choose from each tier strategically)

### Tier 1: Broad (Domain Anchor)
High-level knowledge domains. Pick ONE that best represents the primary field.

**Available broad tags:**
- `science` - Natural sciences (physics, chemistry, biology)
- `technology` - Computing, engineering, digital systems
- `arts` - Visual, performing, literary arts
- `history` - Historical events and periods
- `politics` - Government, policy, political systems
- `economics` - Markets, trade, finance
- `ethics` - Moral philosophy and values
- `society` - Social structures and culture
- `geography` - Regions, countries, spatial topics
- `health` - Medicine, wellness, healthcare
- `education` - Learning and pedagogy
- `law` - Legal systems and courts
- `conflict` - War, military, armed confrontation
- `environment` - Ecology, climate, nature
- `media` - Journalism and communications
- `philosophy` - Philosophical traditions
- `religion` - Faith and spirituality
- `psychology` - Mind, behavior, cognition

### Tier 2: Medium (Conceptual Lens)
How we're approaching the topic. Pick ONE or TWO.

**Common medium tags:**
- `critical-thinking` - Logic and reasoning
- `democracy` - Democratic governance and voting
- `governance` - Regulation and oversight
- `human-rights` - Civil liberties and rights
- `identity` - Cultural belonging and self
- `sustainability` - Long-term viability
- `innovation` - New developments and breakthroughs
- `systems-thinking` - Interconnected analysis
- `mental-health` - Psychology and wellbeing
- `digital-life` - Online behavior and culture
- `energy` - Power and electricity
- `security` - Safety and defense
- `accountability` - Responsibility and consequences
- `regulation` - Rules and standards
- `finance` - Money and investment
- `methodology` - Systematic approaches
- `analysis` - Detailed examination
- `communication` - Information exchange
- `cognition` - Mental processes
- `engineering` - Design and building
- `development` - Growth and progress
- `federalism` - National/state power division
- `interpersonal-dynamics` - Relationships and bonds
- `cultural-heritage` - Traditions and legacy

### Tier 3: Specific (Subject Identifier)
Concrete subject categories. Pick ONE or TWO.

**Science specifics:**
- `physics`, `chemistry`, `biology`, `neuroscience`, `genetics`, `ecology`
- `quantum-mechanics`, `thermodynamics`, `electromagnetism`, `mechanics`
- `astronomy`, `cosmology`, `geology`, `meteorology`, `oceanography`

**Technology specifics:**
- `ai-ml`, `computer-science`, `software-engineering`, `data-science`
- `robotics`, `cybersecurity`, `web-development`, `cloud-computing`
- `databases`, `version-control`, `encryption`

**Energy specifics:**
- `solar-power`, `wind-power`, `hydropower`, `geothermal`, `nuclear-energy`
- `fossil-fuels`, `grid-systems`, `power-generation`, `transmission`
- `energy-storage`, `smart-grid`

**Politics specifics:**
- `us-politics`, `elections`, `federalism`, `civil-rights`
- `immigration`, `policing`, `journalism`
- `trump`, `congress`, `supreme-court`, `executive-power`

**Geography specifics:**
- `americas`, `europe`, `asia`, `africa`, `middle-east`, `oceania`
- `russia-ukraine`, `israel-palestine`, `china-taiwan`

**Arts specifics:**
- `visual-arts`, `performing-arts`, `literary-arts`
- `painting`, `sculpture`, `photography`, `film`, `theater`, `music`, `dance`
- `impressionism`, `surrealism`, `baroque`, `renaissance`, `contemporary`

**Health specifics:**
- `medicine`, `public-health`, `nutrition`

## Tag Assignment Strategy

**Step 1:** Read the chapter name and topics carefully

**Step 2:** Select Tag 1 (Broad)
- What primary knowledge domain does this chapter belong to?
- Example: A chapter about battery technology → `technology`

**Step 3:** Select Tag 2 (Medium)
- What lens or approach characterizes this content?
- Example: Battery chapter covering systems → `systems-thinking` or `energy`

**Step 4:** Select Tag 3 (Specific or Medium)
- What specific subject is covered?
- Example: Battery storage → `energy-storage` or `chemistry`

**Step 5:** Select Tag 4 (Specific - Cross-library connector)
- What other library might link to this content?
- Example: Battery technology connects to → `physics` or `engineering`

## Examples

### Example 1: Off-Grid Solar Chapter
```json
{
  "name": "Solar Power Fundamentals",
  "topics": [
    "How do photovoltaic cells convert sunlight into usable electricity?",
    "What's the real difference between monocrystalline and polycrystalline panels?"
  ],
  "tags": ["technology", "energy", "solar-power", "physics"]
}
```

**Reasoning:**
- Tag 1 (Broad): `technology` - This is about tech systems
- Tag 2 (Medium): `energy` - The conceptual domain
- Tag 3 (Specific): `solar-power` - The exact subject
- Tag 4 (Specific): `physics` - Cross-links to science content

### Example 2: Loneliness Psychology Chapter
```json
{
  "name": "Understanding Loneliness",
  "topics": [
    "What is the difference between loneliness and simply being alone?",
    "How does chronic loneliness affect the brain and body?"
  ],
  "tags": ["psychology", "mental-health", "neuroscience", "health"]
}
```

**Reasoning:**
- Tag 1 (Broad): `psychology` - Primary domain
- Tag 2 (Medium): `mental-health` - The conceptual lens
- Tag 3 (Specific): `neuroscience` - Brain/body aspects
- Tag 4 (Broad): `health` - Cross-links to health content

### Example 3: US Politics Chapter
```json
{
  "name": "Washington DC",
  "topics": [
    "What major actions has the Executive Branch taken this week?",
    "What legislation is moving through Congress right now?"
  ],
  "tags": ["politics", "governance", "us-politics", "federalism"]
}
```

**Reasoning:**
- Tag 1 (Broad): `politics` - Primary domain
- Tag 2 (Medium): `governance` - About governing institutions
- Tag 3 (Specific): `us-politics` - US-specific content
- Tag 4 (Specific): `federalism` - Federal system focus

## Common Mistakes to Avoid

1. **Inventing tags** - Only use tags from the vocabulary
2. **Too many from same tier** - Mix broad, medium, and specific
3. **Generic fallbacks** - Be specific when possible
4. **Duplicate tags** - All 4 tags must be different
5. **Wrong tier** - Don't use `physics` as a broad tag (it's specific)

## Quick Reference: Most Used Tags

**Broad (pick 1):**
`technology`, `science`, `politics`, `arts`, `history`, `society`, `health`, `psychology`

**Medium (pick 1-2):**
`governance`, `systems-thinking`, `innovation`, `energy`, `mental-health`, `identity`, `methodology`, `analysis`, `sustainability`, `security`

**Specific (pick 1-2):**
`us-politics`, `ai-ml`, `physics`, `chemistry`, `elections`, `journalism`, `neuroscience`, `solar-power`, `americas`, `engineering`
