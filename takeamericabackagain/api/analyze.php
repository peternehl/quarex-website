<?php
// File: public_html/api/analyze.php

// --- Headers & CORS ---
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

// --- Load API key from environment (.htaccess -> SetEnv OPENAI_API_KEY <value>) ---
$apiKey = getenv('OPENAI_API_KEY');
if (!$apiKey) {
    echo json_encode([
        'summary' => 'Error: missing API key',
        'points'  => [],
        'rating'  => null,
        'sources' => [],
    ]);
    exit;
}

// --- Read JSON input ---
$in = json_decode(file_get_contents('php://input'), true) ?: [];
$claim      = $in['claim']      ?? '';
$context    = $in['context']    ?? '';
$category   = $in['category']   ?? '';
$date       = $in['date']       ?? '';
$source_url = $in['source_url'] ?? '';
$verdict    = $in['verdict']    ?? '';
$notes      = $in['notes']      ?? '';

// --- Build payload for GPT-5 ---
$payload = [
//    'model'       => 'gpt-5',
//    'temperature' => 1,

    'model'       => 'gpt-4o-mini',
    'temperature' => 0.7,

  'messages'    => [
    [
      'role'    => 'system',
      'content' => 'You are a meticulous, non-partisan fact analyst. Provide a short summary, 3–5 bullet points, and explicitly end with "Deception Score: X/5". Keep under 220 words. After the score, always include this reference scale:

1 = Completely truthful
2 = Mostly true with minor exaggeration
3 = Mixed or misleading
4 = Mostly false or deceptive
5 = Completely false or fabricated'
    ],
    [
      'role'    => 'user',
      'content' => "Claim: {$claim}\nContext: {$context}\nCategory: {$category}\nDate: {$date}\nSource: {$source_url}\nVerdict: {$verdict}\nNotes: {$notes}"
    ]
  ]
];

// --- cURL request ---
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

$res = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
if ($res === false) {
    echo json_encode([
        'summary' => 'Error contacting API',
        'points'  => [curl_error($ch)],
        'rating'  => null,
        'sources' => []
    ]);
    exit;
}
curl_close($ch);

// --- Decode API response ---
$j = json_decode($res, true);
if (!is_array($j)) {
    echo json_encode([
        'summary' => 'Invalid response from API',
        'points'  => [substr($res, 0, 300)],
        'rating'  => null,
        'sources' => []
    ]);
    exit;
}
if (isset($j['error'])) {
    echo json_encode([
        'summary' => 'OpenAI error',
        'points'  => [$j['error']['message'] ?? 'Unknown error'],
        'rating'  => null,
        'sources' => []
    ]);
    exit;
}

// --- Extract model text ---
$text = $j['choices'][0]['message']['content'] ?? '';
$text = trim($text);

// --- Parse summary (first line, strip "Summary:" if present) ---
$lines = preg_split('/\r?\n/', $text);
$lines = array_values(array_filter(array_map('trim', $lines), fn($l) => $l !== ''));
$summary = $lines[0] ?? '';
$summary = preg_replace('/^summary\s*:\s*/i', '', $summary);

// --- Parse bullets ---
$bullets = [];
foreach ($lines as $i => $ln) {
    if (preg_match('/^(?:[-*•]\s+|\d+\.\s+)/u', $ln)) {
        $bullets[] = preg_replace('/^(?:[-*•]\s+|\d+\.\s+)/u', '', $ln);
    }
}
if (!$bullets && count($lines) > 1) {
    $bullets = array_slice($lines, 1);
}

// --- Parse deception score "X/5" ---
$rating = null;
if (preg_match('/(?:deception\s*score|score|rating)\D*([1-5])\s*\/\s*5/i', $text, $m)) {
    $rating = (int)$m[1];
} elseif (preg_match('/\b([1-5])\s*\/\s*5\b/', $text, $m)) {
    $rating = (int)$m[1];
}

// --- Build final response ---
echo json_encode([
  'summary' => $summary,
  'points'  => array_values($bullets),
  'rating'  => $rating,
  'sources' => $source_url ? [$source_url] : []
], JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
