<?php
// File: public_html/api/find_politician.php

// --- Headers & CORS (match analyze.php) ---
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

// Handle preflight quickly
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// --- Error display (off for production) ---
ini_set('display_errors', 0);
error_reporting(E_ALL);

// --- Load API key from environment ---
$apiKey = getenv('OPENAI_API_KEY');
if (!$apiKey) {
    echo json_encode(['error' => 'missing_api_key']);
    exit;
}

// --- Read JSON input ---
$in    = json_decode(file_get_contents('php://input'), true) ?: [];
$name  = trim($in['name']  ?? '');
$state = strtoupper(trim($in['state'] ?? ''));

// Basic validation (2-letter state)
if ($name === '' || $state === '' || strlen($state) !== 2) {
    http_response_code(400);
    echo json_encode(['error' => 'invalid_input', 'detail' => 'Provide name and 2-letter state code']);
    exit;
}

// --- Build payload (mirror your working analyze.php approach) ---
$payload = [
    // Use same family you already verified works:
    'model'       => 'gpt-4o-mini',
    'temperature' => 0.2,
    'messages'    => [
        [
            'role'    => 'system',
            'content' =>
                "You identify U.S. politicians by NAME and STATE.
Return STRICT JSON ONLY (no markdown, no prose), matching this schema:

{
  \"query_name\": string,
  \"query_state\": string,
  \"matches\": [
    {
      \"full_name\": string,
      \"office\": string,          // e.g., 'U.S. Senator', 'U.S. Representative', 'Governor', 'State Senator'
      \"level\": string,           // 'federal' | 'state' | 'local'
      \"party\": string|null,
      \"state\": string,           // 2-letter (e.g., 'VA')
      \"district\": string|null,   // e.g., 'VA-11' for House; null otherwise
      \"confidence\": number,      // 0..1
      \"notes\": string            // short disambiguation or reason
    }
  ]
}

Rules:
- If unsure or multiple plausible matches, include several with lower confidence and a brief note.
- Limit to at most 5 matches.
- If no plausible match, set matches: []."
        ],
        [
            'role'    => 'user',
            'content' => "Find politician(s) for:\nname: {$name}\nstate: {$state}"
        ]
    ]
];

// --- cURL request (same pattern as analyze.php) ---
$ch = curl_init('https://api.openai.com/v1/chat/completions');
curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER     => [
        'Authorization: Bearer ' . $apiKey,
        'Content-Type: application/json'
    ],
    CURLOPT_POST           => true,
    CURLOPT_POSTFIELDS     => json_encode($payload),
    CURLOPT_TIMEOUT        => 30,
]);

$res      = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
if ($res === false) {
    echo json_encode(['error' => 'api_transport', 'detail' => curl_error($ch)]);
    exit;
}
curl_close($ch);

// --- Decode API response & errors (same style as analyze.php) ---
$j = json_decode($res, true);
if (!is_array($j)) {
    echo json_encode(['error' => 'bad_api_json', 'detail' => substr($res, 0, 300)]);
    exit;
}
if (isset($j['error'])) {
    echo json_encode(['error' => 'openai_error', 'detail' => $j['error']]);
    exit;
}

// --- Extract model text (should be JSON only per instruction) ---
$text = trim($j['choices'][0]['message']['content'] ?? '');
$data = json_decode($text, true);

// If the model failed to return valid JSON, surface it plainly
if (!is_array($data) || !isset($data['matches'])) {
    echo json_encode(['error' => 'non_json_reply', 'raw' => $text]);
    exit;
}

// --- Final output (pass-through; front-end expects `matches`) ---
echo json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
