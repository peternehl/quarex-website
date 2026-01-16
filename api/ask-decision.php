<?php
/**
 * ask-decision.php — Quarex Decision Helper API
 * Uses Gemini to analyze decisions through multiple facets
 */

// Load local config if exists (for development)
if (file_exists(__DIR__ . '/config.php')) {
    require_once __DIR__ . '/config.php';
}

// ------------------------ CORS / Origin Validation ------------------------
$ALLOWED_ORIGINS = [
  'https://quarex.org',
  'https://www.quarex.org',
  'http://quarex.org',
  'http://www.quarex.org',
  'http://localhost',
  'http://127.0.0.1',
];

function is_allowed_origin(string $origin, array $allowedOrigins): bool {
  if (in_array($origin, $allowedOrigins)) {
    return true;
  }
  if (preg_match('/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/', $origin)) {
    return true;
  }
  return false;
}

$requestOrigin = $_SERVER['HTTP_ORIGIN'] ?? '';
$isAllowedOrigin = is_allowed_origin($requestOrigin, $ALLOWED_ORIGINS);

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
  if ($isAllowedOrigin) {
    header("Access-Control-Allow-Origin: $requestOrigin");
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, X-Requested-With');
    header('Access-Control-Allow-Credentials: true');
  }
  http_response_code(204);
  exit;
}

// Validate origin
if ($requestOrigin && !$isAllowedOrigin) {
  http_response_code(403);
  echo json_encode(['error' => 'Forbidden']);
  exit;
}

// Set headers
if ($isAllowedOrigin) {
  header("Access-Control-Allow-Origin: $requestOrigin");
  header('Access-Control-Allow-Credentials: true');
}
header('Content-Type: application/json; charset=UTF-8');

// ------------------------ Config ------------------------
$API_KEY = getenv('GEMINI_API_KEY');
if (!$API_KEY) {
  fail(500, 'GEMINI_API_KEY environment variable not set');
}
$MODEL = getenv('GEMINI_MODEL') ?: 'gemini-2.5-flash-lite';
$TIMEOUT = 60;

// ------------------------ Utilities ------------------------
function fail($code, $msg) {
  http_response_code($code);
  echo json_encode(['error' => $msg]);
  exit;
}

function read_json_body() {
  $ct = $_SERVER['CONTENT_TYPE'] ?? '';
  if (stripos($ct, 'application/json') !== false) {
    $raw = file_get_contents('php://input');
    if ($raw !== false && strlen($raw)) {
      $j = json_decode($raw, true);
      if (is_array($j)) return $j;
    }
  }
  return null;
}

function gemini_call(string $model, string $apiKey, array $body, int $timeout = 60): array {
  $url = "https://generativelanguage.googleapis.com/v1beta/models/$model:generateContent";

  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_HTTPHEADER => [
      "Content-Type: application/json",
      "x-goog-api-key: $apiKey",
    ],
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($body, JSON_UNESCAPED_SLASHES),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => $timeout,
  ]);
  $resp = curl_exec($ch);
  if ($resp === false) {
    $err = curl_error($ch);
    curl_close($ch);
    throw new Exception("cURL error: $err");
  }
  $code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
  curl_close($ch);

  if ($code < 200 || $code >= 300) {
    throw new Exception("Gemini HTTP $code: $resp");
  }
  $json = json_decode($resp, true);
  if (!is_array($json)) {
    throw new Exception("Gemini returned non-JSON response");
  }
  return $json;
}

function gemini_extract_text(array $resp): string {
  $cand = $resp['candidates'][0] ?? null;
  if (!$cand) return '';
  $parts = $cand['content']['parts'] ?? [];
  $buf = '';
  foreach ($parts as $p) {
    if (isset($p['text']) && is_string($p['text'])) $buf .= $p['text'];
  }
  return $buf;
}

// Extract follow-up questions from response
function extract_followups(string $text): array {
  $followups = [];

  // Look for FOLLOWUPS: section
  if (preg_match('/FOLLOWUPS:\s*(.*?)$/is', $text, $match)) {
    $section = $match[1];

    // Extract numbered questions
    if (preg_match_all('/\d+\.\s*(.+?)(?=\n\d+\.|\n*$)/s', $section, $matches)) {
      foreach ($matches[1] as $q) {
        $q = trim($q);
        if (!empty($q)) {
          $followups[] = $q;
        }
      }
    }
  }

  return array_slice($followups, 0, 5);
}

// Remove FOLLOWUPS section from text for display
function remove_followups_section(string $text): string {
  return trim(preg_replace('/\n*FOLLOWUPS:.*$/is', '', $text));
}

// ------------------------ Decision Facets ------------------------
$DECISION_FACETS = [
  'initial' => [
    ['id' => 'pros', 'label' => 'Explore the potential benefits and advantages'],
    ['id' => 'cons', 'label' => 'Explore the potential drawbacks and disadvantages'],
    ['id' => 'risks', 'label' => 'Identify risks and uncertainties'],
    ['id' => 'alternatives', 'label' => 'Consider alternative options'],
    ['id' => 'values', 'label' => 'How does this align with my values?'],
    ['id' => 'stakeholders', 'label' => 'Who else is affected by this decision?'],
  ],
  'pros' => [
    ['id' => 'pros-short', 'label' => 'Short-term benefits'],
    ['id' => 'pros-long', 'label' => 'Long-term benefits'],
    ['id' => 'pros-hidden', 'label' => 'Hidden or indirect benefits'],
    ['id' => 'bestcase', 'label' => 'Best case scenario'],
  ],
  'cons' => [
    ['id' => 'cons-short', 'label' => 'Short-term drawbacks'],
    ['id' => 'cons-long', 'label' => 'Long-term drawbacks'],
    ['id' => 'cons-hidden', 'label' => 'Hidden or indirect costs'],
    ['id' => 'worstcase', 'label' => 'Worst case scenario'],
  ],
  'risks' => [
    ['id' => 'risks-financial', 'label' => 'Financial risks'],
    ['id' => 'risks-personal', 'label' => 'Personal/emotional risks'],
    ['id' => 'risks-professional', 'label' => 'Professional/career risks'],
    ['id' => 'risks-mitigation', 'label' => 'How can I mitigate these risks?'],
  ],
  'alternatives' => [
    ['id' => 'alt-similar', 'label' => 'Similar but different options'],
    ['id' => 'alt-opposite', 'label' => 'The opposite choice'],
    ['id' => 'alt-delay', 'label' => 'Delaying the decision'],
    ['id' => 'alt-hybrid', 'label' => 'A hybrid or compromise approach'],
  ],
  'values' => [
    ['id' => 'values-priorities', 'label' => 'What are my core priorities?'],
    ['id' => 'values-future', 'label' => 'What would future me think?'],
    ['id' => 'values-regret', 'label' => 'Which choice would I regret more?'],
    ['id' => 'values-authentic', 'label' => 'What feels most authentic to me?'],
  ],
  'stakeholders' => [
    ['id' => 'stake-family', 'label' => 'Impact on family'],
    ['id' => 'stake-work', 'label' => 'Impact on colleagues/employer'],
    ['id' => 'stake-community', 'label' => 'Impact on community'],
    ['id' => 'stake-self', 'label' => 'Impact on my own wellbeing'],
  ],
  // Political/Policy decision facets
  'political-initial' => [
    ['id' => 'pol-stakeholders', 'label' => 'Which groups are affected and how?'],
    ['id' => 'pol-legal', 'label' => 'Constitutional/legal constraints'],
    ['id' => 'pol-precedent', 'label' => 'What precedent does this set?'],
    ['id' => 'pol-implementation', 'label' => 'Implementation feasibility'],
    ['id' => 'pol-coalition', 'label' => 'Coalition/vote requirements'],
    ['id' => 'pol-secondorder', 'label' => 'Second-order effects'],
  ],
  'pol-stakeholders' => [
    ['id' => 'pol-stake-voters', 'label' => 'Impact on constituents/voters'],
    ['id' => 'pol-stake-business', 'label' => 'Impact on businesses/economy'],
    ['id' => 'pol-stake-vulnerable', 'label' => 'Impact on vulnerable populations'],
    ['id' => 'pol-stake-future', 'label' => 'Impact on future generations'],
  ],
  'pol-legal' => [
    ['id' => 'pol-legal-const', 'label' => 'Constitutional issues'],
    ['id' => 'pol-legal-existing', 'label' => 'Conflicts with existing law'],
    ['id' => 'pol-legal-challenge', 'label' => 'Likelihood of legal challenge'],
    ['id' => 'pol-legal-jurisdiction', 'label' => 'Jurisdictional boundaries'],
  ],
  'pol-precedent' => [
    ['id' => 'pol-prec-similar', 'label' => 'Similar past decisions and outcomes'],
    ['id' => 'pol-prec-future', 'label' => 'How this constrains future options'],
    ['id' => 'pol-prec-other', 'label' => 'How other jurisdictions handled this'],
    ['id' => 'pol-prec-reversal', 'label' => 'Difficulty of reversing this decision'],
  ],
  'pol-implementation' => [
    ['id' => 'pol-impl-cost', 'label' => 'Budget and resource requirements'],
    ['id' => 'pol-impl-timeline', 'label' => 'Realistic implementation timeline'],
    ['id' => 'pol-impl-agencies', 'label' => 'Which agencies/departments involved'],
    ['id' => 'pol-impl-enforcement', 'label' => 'Enforcement mechanisms'],
  ],
  'pol-coalition' => [
    ['id' => 'pol-coal-support', 'label' => 'Who supports this and why'],
    ['id' => 'pol-coal-oppose', 'label' => 'Who opposes this and why'],
    ['id' => 'pol-coal-swing', 'label' => 'Persuadable stakeholders'],
    ['id' => 'pol-coal-compromise', 'label' => 'Possible compromises to build support'],
  ],
  'pol-secondorder' => [
    ['id' => 'pol-second-unintended', 'label' => 'Unintended consequences'],
    ['id' => 'pol-second-cascade', 'label' => 'Cascade effects on other policies'],
    ['id' => 'pol-second-behavior', 'label' => 'How people will adapt/respond'],
    ['id' => 'pol-second-gaming', 'label' => 'How this could be gamed or exploited'],
  ],
];

// Default facets for deep-dive topics
$DEFAULT_DEEP_FACETS = [
  ['id' => 'deeper', 'label' => 'Go deeper on this aspect'],
  ['id' => 'practical', 'label' => 'What practical steps can I take?'],
  ['id' => 'emotions', 'label' => 'How do I feel about this?'],
  ['id' => 'summary', 'label' => 'Summarize my exploration so far'],
];

// ------------------------ Read Input ------------------------
$body = read_json_body();
if (!$body) {
  fail(400, 'Invalid JSON body');
}

$decision = $body['decision'] ?? null;
$facet = $body['facet'] ?? 'initial';
$choice = $body['choice'] ?? null;
$history = $body['history'] ?? [];

if (!$decision || empty($decision['text'])) {
  fail(400, 'Missing decision information');
}

// Use political-specific initial facet for political decisions
$decisionType = $decision['type'] ?? '';
$isPolitical = ($decisionType === 'political');
if ($facet === 'initial' && $isPolitical) {
  $facet = 'political-initial';
}

// ------------------------ Build Prompt ------------------------
$decisionContext = sprintf(
  "Decision Type: %s\nTimeframe: %s\nDecision: %s",
  $decision['typeName'] ?? $decision['type'] ?? 'General',
  $decision['timeframeName'] ?? $decision['timeframe'] ?? 'Unspecified',
  $decision['text']
);

// Build history context
$historyContext = '';
if (!empty($history)) {
  $historyContext = "\n\nPrevious exploration:\n";
  foreach ($history as $h) {
    $historyContext .= "- " . ($h['choice'] ?? $h['facet']) . "\n";
  }
}

// Determine what to analyze based on facet
$facetPrompts = [
  'initial' => "Provide an initial overview of this decision. Identify the key considerations and frame the main question clearly. Be concise but insightful.",
  'pros' => "Analyze the potential benefits and advantages of this decision. Consider both obvious and subtle positives.",
  'cons' => "Analyze the potential drawbacks and disadvantages. Be honest about challenges without being discouraging.",
  'risks' => "Identify the key risks and uncertainties. Consider what could go wrong and what is unknown.",
  'alternatives' => "Explore alternative options to this decision. What other paths could achieve similar goals?",
  'values' => "Help explore how this decision aligns with personal values and long-term goals.",
  'stakeholders' => "Identify who else is affected by this decision and how they might be impacted.",
  'pros-short' => "Focus on the immediate, short-term benefits of this decision.",
  'pros-long' => "Focus on the long-term benefits that may take time to materialize.",
  'pros-hidden' => "Explore hidden, indirect, or unexpected benefits that might not be immediately obvious.",
  'cons-short' => "Focus on the immediate, short-term drawbacks or challenges.",
  'cons-long' => "Focus on long-term disadvantages or problems that may emerge over time.",
  'cons-hidden' => "Explore hidden costs, indirect drawbacks, or unexpected negative consequences.",
  'bestcase' => "Paint a picture of the best possible outcome if this decision goes well.",
  'worstcase' => "Consider the worst case scenario. What would happen if everything went wrong?",
  'risks-financial' => "Focus specifically on financial risks and monetary implications.",
  'risks-personal' => "Focus on personal and emotional risks - impact on wellbeing, relationships, stress.",
  'risks-professional' => "Focus on career and professional risks - reputation, opportunities, growth.",
  'risks-mitigation' => "Suggest concrete strategies to mitigate the identified risks.",
  'alt-similar' => "Explore similar alternatives that might achieve the same goals differently.",
  'alt-opposite' => "Consider the opposite choice - what would that look like?",
  'alt-delay' => "Analyze the option of delaying this decision. What are the trade-offs?",
  'alt-hybrid' => "Explore compromise or hybrid approaches that combine elements of different options.",
  'values-priorities' => "Help clarify core priorities and what matters most in this situation.",
  'values-future' => "Consider how future-you might view this decision looking back.",
  'values-regret' => "Explore which choice might lead to more regret and why.",
  'values-authentic' => "Help identify which path feels most true to authentic self.",
  'stake-family' => "Analyze how this decision impacts family members.",
  'stake-work' => "Analyze how this decision impacts professional relationships and work.",
  'stake-community' => "Consider the broader community impact of this decision.",
  'stake-self' => "Focus on impact on personal wellbeing, growth, and happiness.",
  'deeper' => "Go deeper on the previously explored aspect. Provide more nuanced analysis.",
  'practical' => "Provide concrete, actionable steps related to this aspect of the decision.",
  'emotions' => "Help explore the emotional dimensions - fears, hopes, intuitions.",
  'summary' => "Summarize the key insights from the exploration so far.",
  'custom' => "The user has a custom follow-up question. Answer it thoughtfully in the context of their decision.",
  // Political/Policy facet prompts
  'political-initial' => "Provide an initial policy analysis of this decision. Frame the core policy question, identify the key stakeholders affected, and outline the major trade-offs involved. Consider constitutional/legal constraints, implementation challenges, and political feasibility.",
  'pol-stakeholders' => "Identify all stakeholder groups affected by this policy decision. Analyze how each group would be impacted - positively and negatively - and estimate relative magnitudes.",
  'pol-legal' => "Analyze the legal and constitutional dimensions. What existing laws apply? Are there constitutional constraints? What's the likelihood of legal challenge?",
  'pol-precedent' => "Examine what precedent this decision sets. How have similar decisions played out historically? How does this constrain or enable future policy options?",
  'pol-implementation' => "Analyze implementation feasibility. What resources are required? Which agencies/departments are involved? What's a realistic timeline? What could go wrong during implementation?",
  'pol-coalition' => "Map the political landscape. Who supports this and why? Who opposes it? Who's persuadable? What compromises might build broader support?",
  'pol-secondorder' => "Identify second-order effects. What unintended consequences might arise? How will people adapt their behavior? What cascade effects on other policies?",
  'pol-stake-voters' => "Focus on impact to constituents and voters. Which voter segments benefit or suffer? How might this affect electoral outcomes?",
  'pol-stake-business' => "Focus on economic and business impacts. How does this affect different industries, employment, and economic activity?",
  'pol-stake-vulnerable' => "Focus on impact to vulnerable populations. How are low-income, elderly, disabled, or marginalized groups affected?",
  'pol-stake-future' => "Focus on intergenerational impact. How does this affect future generations? What long-term obligations or benefits does it create?",
  'pol-legal-const' => "Analyze constitutional issues in depth. What constitutional provisions apply? How have courts ruled on similar matters?",
  'pol-legal-existing' => "Identify conflicts with existing law. What statutes would need to change? What regulatory frameworks are affected?",
  'pol-legal-challenge' => "Assess litigation risk. Who would have standing to sue? What legal theories would challengers use? How likely is a successful challenge?",
  'pol-legal-jurisdiction' => "Analyze jurisdictional issues. Federal vs state authority? Preemption issues? Interstate commerce implications?",
  'pol-prec-similar' => "Examine similar past decisions. What worked? What failed? What lessons apply here?",
  'pol-prec-future' => "Analyze how this decision constrains future options. What path dependencies does it create?",
  'pol-prec-other' => "How have other states, countries, or jurisdictions handled similar issues? What can we learn from their experience?",
  'pol-prec-reversal' => "How difficult would it be to reverse this decision? What lock-in effects exist?",
  'pol-impl-cost' => "Detail budget and resource requirements. Direct costs, indirect costs, ongoing costs, opportunity costs.",
  'pol-impl-timeline' => "Provide a realistic implementation timeline. What are the critical path items? Where are delays likely?",
  'pol-impl-agencies' => "Which agencies and departments are involved? What coordination challenges exist? Who has authority over what?",
  'pol-impl-enforcement' => "How will this be enforced? What compliance mechanisms exist? What are the penalties for non-compliance?",
  'pol-coal-support' => "Who supports this policy and why? What are their motivations and what do they expect to gain?",
  'pol-coal-oppose' => "Who opposes this policy and why? What are their specific objections? How strong is their opposition?",
  'pol-coal-swing' => "Who is persuadable? What would it take to move them? What concerns could be addressed?",
  'pol-coal-compromise' => "What compromises might build broader support while preserving core policy goals?",
  'pol-second-unintended' => "What unintended consequences might arise? Consider behavioral changes, market responses, and perverse incentives.",
  'pol-second-cascade' => "How does this affect other policies? What ripple effects through the regulatory/legal system?",
  'pol-second-behavior' => "How will people and organizations adapt their behavior in response? What workarounds might emerge?",
  'pol-second-gaming' => "How could this policy be gamed or exploited? Where are the loopholes?",
];

// For custom questions, use the choice as the prompt focus
if ($facet === 'custom' && $choice) {
  $facetPrompt = "The user asks: \"" . $choice . "\"\n\nAnswer this question thoughtfully in the context of their decision.";
} else {
  $facetPrompt = $facetPrompts[$facet] ?? "Analyze this aspect of the decision: " . ($choice ?? $facet);
}

$fullPrompt = <<<PROMPT
You are a direct, analytical decision-making assistant. Help users systematically examine their decisions by presenting facts, trade-offs, and considerations clearly.

{$decisionContext}
{$historyContext}

Current focus: {$facetPrompt}

Guidelines:
- Be direct and matter-of-fact - avoid emotional language or excessive reassurance
- Present concrete information, not feelings or platitudes
- Use bullet points for lists of factors, risks, or considerations
- State trade-offs plainly without softening them
- Skip phrases like "I understand this is difficult" or "It's important to consider your feelings"
- If something is a risk, say so directly; if something is a benefit, state it clearly
- 2-4 paragraphs max, focused on substance
- Format with HTML: use <p> tags for paragraphs, <strong> for emphasis, <ul>/<li> for lists

IMPORTANT: At the end of your response, you MUST provide exactly 5 follow-up options. Use a MIX of formats:
- 2-3 should be DECISION CHOICES formatted as "A vs B" or "A / B / C" - concrete trade-offs the user must weigh
- 2-3 should be EXPLORATION QUESTIONS - deeper dives into specific aspects

Format at the very end like this:
FOLLOWUPS:
1. [Decision choice: "Option A vs Option B" - e.g., "Higher salary vs staying near family"]
2. [Exploration question about a specific aspect]
3. [Decision choice with 2-3 options]
4. [Exploration question]
5. [Decision choice or exploration question]

Requirements:
- Decision choices should use specific terms from THIS decision (not generic "Option A")
- Frame choices as real trade-offs the user faces
- Exploration questions should dig into angles you mentioned but didn't fully cover
- All options must be specific to this decision context
PROMPT;

// ------------------------ Call Gemini ------------------------
$geminiBody = [
  "contents" => [[
    "role" => "user",
    "parts" => [["text" => $fullPrompt]]
  ]],
  "generationConfig" => [
    "temperature" => 0.7,
    "maxOutputTokens" => 1500,
  ],
];

try {
  $resp = gemini_call($MODEL, $API_KEY, $geminiBody, $TIMEOUT);
  $text = gemini_extract_text($resp);

  if (empty($text)) {
    fail(502, 'Empty response from AI');
  }

  // Extract follow-up questions from the AI response
  $dynamicFollowups = extract_followups($text);

  // Clean the analysis text (remove FOLLOWUPS section)
  $cleanAnalysis = remove_followups_section($text);

  // Convert to HTML if not already formatted
  if (strpos($cleanAnalysis, '<p>') === false) {
    $cleanAnalysis = '<p>' . nl2br(htmlentities($cleanAnalysis, ENT_QUOTES, 'UTF-8')) . '</p>';
  }

  // Build facets from dynamic follow-ups if available, otherwise use predefined
  if (!empty($dynamicFollowups)) {
    $nextFacets = array_map(function($q, $i) {
      return [
        'id' => 'followup-' . $i,
        'label' => $q
      ];
    }, $dynamicFollowups, array_keys($dynamicFollowups));
  } else {
    // Fallback to predefined facets
    $nextFacets = $DECISION_FACETS[$facet] ?? $DEFAULT_DEEP_FACETS;
  }

  // If this was a summary request, offer to explore more or conclude
  if ($facet === 'summary') {
    $restartFacet = $isPolitical ? 'political-initial' : 'initial';
    $nextFacets = [
      ['id' => $restartFacet, 'label' => 'Start a fresh exploration'],
      ['id' => 'practical', 'label' => 'What concrete next steps should I take?'],
      ['id' => $isPolitical ? 'pol-coalition' : 'emotions', 'label' => $isPolitical ? 'Map the political coalition' : 'Check in with my feelings about this'],
    ];
  }

  // Build response
  $response = [
    'analysis' => $cleanAnalysis,
    'facets' => $nextFacets,
  ];

  // If summary, include a structured summary
  if ($facet === 'summary' && !empty($history)) {
    $response['summary'] = array_map(function($h) {
      return [
        'facet' => $h['facet'],
        'insight' => $h['choice'] ?? 'Explored'
      ];
    }, $history);
  }

  echo json_encode($response, JSON_UNESCAPED_SLASHES);

} catch (Exception $e) {
  error_log("Decision API error: " . $e->getMessage());
  fail(502, 'AI service error');
}
