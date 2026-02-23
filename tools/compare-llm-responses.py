#!/usr/bin/env python3
"""
Compare Gemini vs Claude responses on the same question.
Tests whether Claude handles sharp political framing better than Gemini.

Usage:
  python compare-llm-responses.py

Requires:
  pip install anthropic google-generativeai

Set environment variables:
  ANTHROPIC_API_KEY=your-claude-key
  GEMINI_API_KEY=your-gemini-key
"""

import os
import sys
from pathlib import Path

# Load .env-master file with API keys
env_path = Path("E:/projects/websites/API Keys/.env-master")
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())
    # Map GOOGLE_API_KEY to GEMINI_API_KEY if needed
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]

# Test question - sharp political framing
TEST_QUESTION = """
Context: This question is about Democratic Party strategy from 2020-2026.

Question: How did Merrick Garland's 22-month delay in appointing a special counsel guarantee that the Trump trials would become an election-year spectacle?
"""

SYSTEM_PROMPT = """You are a knowledgeable, direct subject-matter expert.

EXPERTISE LEVEL: Intermediate. Write for an educated general audience.
Explain technical terms briefly when first used. Balance accessibility with substance.
Keep your response to 3-4 paragraphs.
Each point must name specific people and dates.

TONE: State claims directly with analytical confidence.
Hedging is acceptable ONLY when presenting genuinely contested evidence, not as a stylistic default.

BANNED PATTERNS: Do not use any of the following:
'it could be argued', 'potentially', 'arguably', 'can be seen as',
'while [concession]' clauses that soften a point before making it.

Do not restate the question or add a preamble. Do not add a closing summary paragraph."""


def test_gemini(question: str) -> str:
    """Send question to Gemini and return response."""
    try:
        import google.generativeai as genai
    except ImportError:
        return "ERROR: google-generativeai not installed. Run: pip install google-generativeai"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "ERROR: GEMINI_API_KEY environment variable not set"

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT
    )

    response = model.generate_content(question)
    return response.text


def test_claude(question: str) -> str:
    """Send question to Claude and return response."""
    try:
        import anthropic
    except ImportError:
        return "ERROR: anthropic not installed. Run: pip install anthropic"

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return "ERROR: ANTHROPIC_API_KEY environment variable not set"

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": question}
        ]
    )

    return response.content[0].text


def main():
    print("=" * 70)
    print("LLM COMPARISON TEST: Sharp Political Framing")
    print("=" * 70)
    print()
    print("QUESTION:")
    print(TEST_QUESTION.strip())
    print()
    print("=" * 70)
    print("GEMINI RESPONSE:")
    print("=" * 70)
    print()

    gemini_response = test_gemini(TEST_QUESTION)
    print(gemini_response)

    print()
    print("=" * 70)
    print("CLAUDE RESPONSE:")
    print("=" * 70)
    print()

    claude_response = test_claude(TEST_QUESTION)
    print(claude_response)

    print()
    print("=" * 70)
    print("COMPARISON NOTES:")
    print("=" * 70)
    print("""
Look for:
1. Does Gemini reframe the question defensively? (e.g., "did not cause a delay")
2. Does Claude engage with the critical premise directly?
3. Which response names more specific dates, people, events?
4. Which uses hedging language despite the BANNED PATTERNS?
""")


if __name__ == "__main__":
    main()
