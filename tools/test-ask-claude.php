<?php
/**
 * Direct test of Claude API with web search (standalone, not using ask-claude.php)
 * Run: php tools/test-ask-claude.php
 */

// Load API key
$envFile = 'E:/projects/websites/API Keys/.env-master';
if (file_exists($envFile)) {
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        if (strpos($line, '=') !== false && $line[0] !== '#') {
            list($key, $value) = explode('=', $line, 2);
            putenv(trim($key) . '=' . trim($value));
        }
    }
}

$apiKey = getenv('ANTHROPIC_API_KEY');
if (!$apiKey) {
    die("ANTHROPIC_API_KEY not found\n");
}

$question = "How did Merrick Garland's 22-month delay in appointing a special counsel guarantee that the Trump trials would become an election-year spectacle?";
$category = "Democratic Party strategy from 2020-2026";

echo "Testing Claude API with web search...\n";
echo "Question: $question\n\n";

$systemPrompt = "You are a knowledgeable, direct subject-matter expert. " .
    "EXPERTISE LEVEL: Intermediate. Write for an educated general audience. " .
    "Explain technical terms briefly when first used. Balance accessibility with substance. " .
    "Keep each numbered point to 4-5 sentences. " .
    "Each point must name specific people and dates. " .
    "TONE: State claims directly with analytical confidence. " .
    "Hedging is acceptable ONLY when presenting genuinely contested evidence, not as a stylistic default. " .
    "BANNED PATTERNS: Do not use any of the following: " .
    "'it could be argued', 'potentially', 'arguably', 'can be seen as', " .
    "'while [concession]' clauses that soften a point before making it. " .
    "Do not restate the question or add a preamble. Do not add a closing summary paragraph. " .
    "This question is in the context of: $category. " .
    "IMPORTANT: At the end of every answer, provide exactly 3 follow-up questions.";

$body = [
    'model' => 'claude-sonnet-4-5-20250929',
    'max_tokens' => 2048,
    'system' => $systemPrompt,
    'messages' => [
        ['role' => 'user', 'content' => $question]
    ],
    'tools' => [
        [
            'type' => 'web_search_20250305',
            'name' => 'web_search',
            'max_uses' => 5
        ]
    ]
];

$ch = curl_init('https://api.anthropic.com/v1/messages');
curl_setopt_array($ch, [
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'x-api-key: ' . $apiKey,
        'anthropic-version: 2023-06-01',
    ],
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($body),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 120,
]);

$resp = curl_exec($ch);
$code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
curl_close($ch);

echo "HTTP $code\n\n";

if ($code < 200 || $code >= 300) {
    echo "Error: $resp\n";
    exit(1);
}

$json = json_decode($resp, true);

// Extract text
$text = '';
$sources = [];
foreach ($json['content'] ?? [] as $block) {
    if ($block['type'] === 'text') {
        $text .= $block['text'];
        // Extract citations
        if (isset($block['citations'])) {
            foreach ($block['citations'] as $cite) {
                if (isset($cite['url'])) {
                    $sources[$cite['url']] = $cite['title'] ?? '';
                }
            }
        }
    }
}

// Check web search usage
$usage = $json['usage'] ?? [];
$searches = $usage['server_tool_use']['web_search_requests'] ?? 0;

echo str_repeat("=", 70) . "\n";
echo "RESPONSE (web searches: $searches):\n";
echo str_repeat("=", 70) . "\n\n";
echo wordwrap($text, 90) . "\n";

if (!empty($sources)) {
    echo "\n" . str_repeat("-", 70) . "\n";
    echo "SOURCES (" . count($sources) . "):\n";
    foreach ($sources as $url => $title) {
        echo "  - $title: $url\n";
    }
}

echo "\n" . str_repeat("-", 70) . "\n";
echo "USAGE:\n";
echo "  Input tokens: " . ($usage['input_tokens'] ?? 0) . "\n";
echo "  Output tokens: " . ($usage['output_tokens'] ?? 0) . "\n";
echo "  Web searches: $searches\n";
