<?php
// Load local config if exists (for development)
if (file_exists(__DIR__ . '/config.php')) {
    require_once __DIR__ . '/config.php';
}

/**
 * ask-claude.php — Claude Sonnet 4.5 with web search
 *
 * Features:
 * - Streaming responses (Server-Sent Events)
 * - Prompt caching for reduced latency/cost
 * - Dynamic max_tokens based on expertise level
 *
 * Returns streamed JSON events or single JSON response
 */

// ------------------------ CORS / Origin Validation ------------------------
$ALLOWED_ORIGINS = [
  'https://quarex.org',
  'https://www.quarex.org',
  'http://quarex.org',
  'http://www.quarex.org',
  'https://truthangel.org',
  'https://www.truthangel.org',
  'http://truthangel.org',
  'http://www.truthangel.org',
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
  log_security_event('BLOCKED_ORIGIN', "Request from unauthorized origin", ['origin' => $requestOrigin]);
  http_response_code(403);
  echo json_encode(['error' => 'Forbidden']);
  exit;
}

// Validate referer
$referer = $_SERVER['HTTP_REFERER'] ?? '';
if ($referer) {
  $refererValid = false;
  foreach ($ALLOWED_ORIGINS as $allowed) {
    if (strpos($referer, $allowed) === 0) {
      $refererValid = true;
      break;
    }
  }
  if (!$refererValid && preg_match('/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?\//', $referer)) {
    $refererValid = true;
  }
  if (!$refererValid) {
    log_security_event('BLOCKED_REFERER', "Request with unauthorized referer", ['referer' => substr($referer, 0, 200)]);
    http_response_code(403);
    echo json_encode(['error' => 'Forbidden']);
    exit;
  }
}

// Set CORS headers
if ($isAllowedOrigin) {
  header("Access-Control-Allow-Origin: $requestOrigin");
  header('Access-Control-Allow-Credentials: true');
}

// ------------------------ Config ------------------------
$API_KEY = getenv('ANTHROPIC_API_KEY');
if (!$API_KEY) {
  fail(500, 'ANTHROPIC_API_KEY environment variable not set');
}
$MODEL   = getenv('CLAUDE_MODEL') ?: 'claude-sonnet-4-5-20250929';
$TIMEOUT = 90; // Longer timeout for streaming

// ------------------------ Security Functions ------------------------
function load_blocked_patterns(): array {
  static $cached_patterns = null;
  if ($cached_patterns !== null) {
    return $cached_patterns;
  }

  $patterns = [];
  $patternFile = __DIR__ . '/blocked_patterns.txt';

  if (!file_exists($patternFile)) {
    error_log("Warning: blocked_patterns.txt not found at $patternFile");
    return $patterns;
  }

  $lines = file($patternFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
  if ($lines === false) {
    error_log("Warning: Could not read blocked_patterns.txt");
    return $patterns;
  }

  foreach ($lines as $line) {
    $line = trim($line);
    if ($line === '' || $line[0] === '#') {
      continue;
    }
    $patterns[] = '/\b' . $line . '/i';
  }

  $cached_patterns = $patterns;
  return $patterns;
}

function is_harmful_query(string $query): bool {
  $harmful_patterns = load_blocked_patterns();
  foreach ($harmful_patterns as $pattern) {
    if (preg_match($pattern, $query)) {
      return true;
    }
  }
  return false;
}

function log_security_event(string $type, string $message, array $context = []) {
  $logDir = __DIR__ . '/logs';
  if (!is_dir($logDir)) {
    @mkdir($logDir, 0755, true);
  }

  $logFile = $logDir . '/security.log';
  cleanup_log_file($logFile, 7, 10 * 1024 * 1024);

  $entry = [
    'timestamp' => date('Y-m-d H:i:s'),
    'type' => $type,
    'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'user_agent' => substr($_SERVER['HTTP_USER_AGENT'] ?? 'unknown', 0, 200),
    'message' => $message,
    'context' => $context
  ];

  @file_put_contents($logFile, json_encode($entry) . "\n", FILE_APPEND | LOCK_EX);
}

function cleanup_log_file(string $logFile, int $maxDays = 7, int $maxBytes = 10485760) {
  if (!file_exists($logFile)) {
    return;
  }

  if (filesize($logFile) > $maxBytes) {
    $lines = file($logFile);
    if ($lines && count($lines) > 1000) {
      $lines = array_slice($lines, -1000);
      @file_put_contents($logFile, implode('', $lines), LOCK_EX);
    } else {
      @file_put_contents($logFile, '', LOCK_EX);
    }
    return;
  }

  if (mt_rand(1, 100) !== 1) {
    return;
  }

  $lines = @file($logFile, FILE_IGNORE_NEW_LINES);
  if (!$lines) {
    return;
  }

  $cutoffTime = strtotime("-{$maxDays} days");
  $newLines = [];

  foreach ($lines as $line) {
    $entry = json_decode($line, true);
    if ($entry && isset($entry['timestamp'])) {
      $entryTime = strtotime($entry['timestamp']);
      if ($entryTime >= $cutoffTime) {
        $newLines[] = $line;
      }
    } else {
      $newLines[] = $line;
    }
  }

  if (count($newLines) < count($lines)) {
    @file_put_contents($logFile, implode("\n", $newLines) . "\n", LOCK_EX);
  }
}

function check_rate_limit(string $ip, int $maxRequests = 20, int $windowSeconds = 60): bool {
  $logDir = __DIR__ . '/logs';
  if (!is_dir($logDir)) {
    @mkdir($logDir, 0755, true);
  }

  $rateFile = $logDir . '/rate_limits.json';
  $now = time();

  $data = [];
  if (file_exists($rateFile)) {
    $content = @file_get_contents($rateFile);
    if ($content) {
      $data = json_decode($content, true) ?: [];
    }
  }

  foreach ($data as $key => $timestamps) {
    $data[$key] = array_filter($timestamps, fn($t) => ($now - $t) < $windowSeconds);
    if (empty($data[$key])) {
      unset($data[$key]);
    }
  }

  $ipKey = md5($ip);
  $requests = $data[$ipKey] ?? [];

  if (count($requests) >= $maxRequests) {
    return false;
  }

  $requests[] = $now;
  $data[$ipKey] = $requests;

  @file_put_contents($rateFile, json_encode($data), LOCK_EX);

  return true;
}

// ------------------------ Utilities ------------------------
function fail($code, $msg, $extra = []) {
  http_response_code($code);
  header('Content-Type: application/json; charset=UTF-8');
  echo json_encode(array_merge([
    'error' => $msg,
  ], $extra), JSON_UNESCAPED_SLASHES);
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

function clamp($val, $min, $max, $default) {
  if ($val === null || $val === '') return $default;
  $n = floatval($val);
  if ($n < $min) $n = $min;
  if ($n > $max) $n = $max;
  return $n;
}

// Extract follow-up questions from response text
function extract_followup_questions(string $text): array {
  $questions = [];

  if (preg_match('/Follow-up questions?:?\s*(.*?)(?:\n\n|$)/is', $text, $match)) {
    $section = $match[1];

    if (preg_match_all('/\d+\.\s*(.+?)(?=\n\d+\.|\n*$)/s', $section, $matches)) {
      foreach ($matches[1] as $q) {
        $q = trim($q);
        if (!empty($q)) {
          $questions[] = $q;
        }
      }
    }
  }

  return array_slice(array_pad($questions, 3, ''), 0, 3);
}

// ------------------------ Read input ------------------------
$bodyJson = read_json_body();
$q = null;

if ($bodyJson && isset($bodyJson['q'])) {
  $q = trim(strval($bodyJson['q']));
} else {
  $q = trim(strval($_REQUEST['q'] ?? ''));
}

if ($q === '') {
  fail(400, "Missing 'q' parameter. Provide your question as JSON {\"q\":\"...\"} or ?q=...");
}

// ------------------------ Security Checks ------------------------
$clientIP = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
if (!check_rate_limit($clientIP)) {
  log_security_event('RATE_LIMITED', "Rate limit exceeded", ['query' => substr($q, 0, 100)]);
  fail(429, 'Too many requests. Please wait before trying again.');
}

if (is_harmful_query($q)) {
  log_security_event('BLOCKED_CONTENT', "Harmful query blocked", ['query' => substr($q, 0, 200)]);
  fail(403, 'Your request cannot be processed.');
}

log_security_event('REQUEST', "Claude API request", ['query' => substr($q, 0, 200)]);

// Capture options from request
$category = '';
if ($bodyJson && isset($bodyJson['category'])) {
  $category = trim(strval($bodyJson['category']));
} else {
  $category = trim(strval($_REQUEST['category'] ?? ''));
}

$temperature = clamp($_REQUEST['temperature'] ?? ($bodyJson['temperature'] ?? null), 0.0, 1.0, 0.4);
$podcastMode = !!($_REQUEST['podcast'] ?? ($bodyJson['podcast'] ?? false));
$streamMode  = !!($_REQUEST['stream'] ?? ($bodyJson['stream'] ?? true)); // Default to streaming (logging removed, should be stable now)

// Expertise level
$expertise = trim(strval($bodyJson['expertise'] ?? ($_REQUEST['expertise'] ?? 'intermediate')));
if (!in_array($expertise, ['introductory', 'intermediate', 'advanced'])) {
  $expertise = 'intermediate';
}

// ------------------------ Dynamic max_tokens ------------------------
if ($podcastMode) {
  $maxTokens = 1500;  // Short, punchy podcast responses
} else {
  $maxTokens = match($expertise) {
    'introductory' => 2048,   // Short, simple
    'intermediate' => 3072,   // Balanced
    'advanced'     => 4096,   // Comprehensive
    default        => 3072
  };
}

// ------------------------ Build System Prompt with Caching ------------------------

// STATIC part - cacheable (instructions that never change)
$staticSystemPrompt = <<<'PROMPT'
You are a knowledgeable, direct subject-matter expert.

TONE: State claims directly with analytical confidence — this is analytical framing, not advocacy. Hedging is acceptable ONLY when presenting genuinely contested evidence, not as a stylistic default.

BANNED PATTERNS: Do not use any of the following:
- 'it could be argued', 'some might say', 'potentially', 'arguably'
- 'can be seen as', 'while [concession]' clauses that soften a point before making it
- 'at the expense of', 'suggests a strategic decision'

Do not restate the question or add a preamble. Do not add a closing summary paragraph.

ANSWER PRECISION: When a question asks you to 'name', 'identify', or 'list' specific moments, instances, or examples, cite specific dated events involving specific named people — not ongoing trends, general strategies, or multi-year patterns. Each point must be a distinct, identifiable moment in time.

RECENCY: Always prioritize the most current and up-to-date information available. When discussing facts, statistics, policies, or events, use the latest data from 2024-2026 whenever possible.

LANGUAGE: If the user's message begins with 'Please respond in [language]', you MUST write your ENTIRE response in that language, including the follow-up questions.

IMPORTANT: At the end of every answer, you MUST provide exactly 3 contextual follow-up questions that help the user explore the topic deeper. Format them clearly as:

Follow-up questions:
1. [First question]
2. [Second question]
3. [Third question]
PROMPT;

// Podcast mode has different static prompt
$staticPodcastPrompt = <<<'PROMPT'
You are a confident expert being interviewed for a podcast. Write conversationally for SPOKEN DELIVERY.

TONE: State claims directly with analytical confidence. Hedging is acceptable ONLY when presenting genuinely contested evidence.

STYLE: Write as if you are speaking to an interviewer. Use natural, flowing sentences. Avoid bullet points, numbered lists, and markdown formatting. Do not use asterisks, headers, or special characters. Keep answers brief and punchy - aim for 2 short paragraphs, under 120 words total. Use verbal transitions like 'Well,', 'So,', 'The thing is,' etc.

BANNED PATTERNS: Do not use 'it could be argued', 'some might say', 'potentially', 'arguably', 'can be seen as'.

RECENCY: Prioritize current information from 2024-2026 when relevant.

LANGUAGE: If the user's message begins with 'Please respond in [language]', respond entirely in that language.

IMPORTANT: At the end of every answer, provide exactly 3 follow-up questions the interviewer might ask. Format them as:

Follow-up questions:
1. [First question]
2. [Second question]
3. [Third question]
PROMPT;

// DYNAMIC part - changes per request (not cached)
$dynamicParts = [];

// Expertise-specific instructions
$expertiseExtra = match($expertise) {
  'introductory' => "EXPERTISE LEVEL: Introductory. Write for someone new to this topic. Use plain language. If you must use a technical term, explain it briefly in parentheses. Use concrete examples from everyday life. Keep each numbered point to 3-4 sentences maximum. Be the shortest of all levels. Each point must name a specific person, event, or date.",
  'advanced' => "EXPERTISE LEVEL: Advanced. Write for a knowledgeable, professional audience. Use technical terminology freely. Cite specific events, names, dates, and data points in every point. Include counter-arguments and competing interpretations where they add substance — present these as separate observations, not as 'while' clauses cushioning the main claim. Keep each numbered point to 5-6 sentences maximum — prioritize density over length.",
  default => "EXPERTISE LEVEL: Intermediate. Write for an educated general audience. Explain technical terms briefly when first used. Balance accessibility with substance. Keep each numbered point to 4-5 sentences. Must be shorter than Advanced but more detailed than Introductory. Each point must name specific people and dates."
};
$dynamicParts[] = $expertiseExtra;

// Quarex context if relevant
if ($category && stripos($category, 'quarex') !== false) {
  $dynamicParts[] = "IMPORTANT CONTEXT - Quarex Definition: A quarex is a dynamically generated, recursively structured knowledge artifact that evolves through iterative inquiry. It is a new medium for organizing knowledge—neither a traditional book nor a dataset, but a living system that reorganizes itself as new questions emerge. See quarex.org for more.";
}

// Category context
if ($category) {
  $dynamicParts[] = "This question is in the context of: $category. Provide answers relevant to this subject area.";
}

$dynamicSystemPrompt = implode("\n\n", $dynamicParts);

// Build system array with cache_control
$systemBlocks = [
  [
    "type" => "text",
    "text" => $podcastMode ? $staticPodcastPrompt : $staticSystemPrompt,
    "cache_control" => ["type" => "ephemeral"]  // Cache this block
  ]
];

if (!empty($dynamicSystemPrompt)) {
  $systemBlocks[] = [
    "type" => "text",
    "text" => $dynamicSystemPrompt
  ];
}

// ------------------------ Build Request Body ------------------------
$requestBody = [
  "model" => $MODEL,
  "max_tokens" => $maxTokens,
  "system" => $systemBlocks,
  "messages" => [
    ["role" => "user", "content" => $q]
  ],
  "tools" => [
    [
      "type" => "web_search_20250305",
      "name" => "web_search",
      "max_uses" => 3
    ]
  ]
];

if ($temperature != 1.0) {
  $requestBody["temperature"] = $temperature;
}

// ------------------------ Streaming vs Non-Streaming ------------------------
if ($streamMode) {
  // Enable streaming
  $requestBody["stream"] = true;

  // Set headers for Server-Sent Events
  header('Content-Type: text/event-stream');
  header('Cache-Control: no-cache');
  header('Connection: keep-alive');
  header('X-Accel-Buffering: no'); // Disable nginx buffering

  // Disable PHP output buffering
  if (ob_get_level()) ob_end_flush();
  @ini_set('output_buffering', 'off');
  @ini_set('zlib.output_compression', false);

  // Accumulated response data
  $fullText = '';
  $sources = [];
  $searchUsed = false;
  $currentBlockType = '';

  // Stream callback function
  $streamCallback = function($ch, $data) use (&$fullText, &$sources, &$searchUsed, &$currentBlockType) {
    // Parse SSE data lines
    $lines = explode("\n", $data);

    foreach ($lines as $line) {
      $line = trim($line);
      if (empty($line)) continue;

      // Handle SSE format: "data: {...}" or "event: ..."
      if (strpos($line, 'data: ') === 0) {
        $jsonStr = substr($line, 6);
        if ($jsonStr === '[DONE]') continue;

        $event = json_decode($jsonStr, true);
        if (!$event) continue;

        $type = $event['type'] ?? '';

        // Handle message_start - may contain content array with tool results
        if ($type === 'message_start') {
          $message = $event['message'] ?? [];
          $content = $message['content'] ?? [];
          foreach ($content as $block) {
            $blockType = $block['type'] ?? '';
            if ($blockType === 'server_tool_result' || $blockType === 'tool_result') {
              $results = $block['content'] ?? [];
              foreach ($results as $item) {
                if (isset($item['url'])) {
                  $sources[$item['url']] = [
                    'url' => $item['url'],
                    'title' => $item['title'] ?? ''
                  ];
                }
              }
            }
          }
        }

        // Handle content_block_start - track what type of block we're in
        if ($type === 'content_block_start') {
          $contentBlock = $event['content_block'] ?? [];
          $currentBlockType = $contentBlock['type'] ?? '';

          // Track web search usage (server_tool_use is the search request)
          if ($currentBlockType === 'server_tool_use' || $currentBlockType === 'web_search_tool_use') {
            $searchUsed = true;
          }

          // Extract sources from server_tool_result (web search results)
          if ($currentBlockType === 'server_tool_result' || $currentBlockType === 'web_search_tool_result') {
            $content = $contentBlock['content'] ?? [];
            if (is_array($content)) {
              foreach ($content as $item) {
                if (isset($item['type']) && $item['type'] === 'web_search_result' && isset($item['url'])) {
                  $sources[$item['url']] = [
                    'url' => $item['url'],
                    'title' => $item['title'] ?? ''
                  ];
                }
                // Also handle direct url/title format
                if (isset($item['url'])) {
                  $sources[$item['url']] = [
                    'url' => $item['url'],
                    'title' => $item['title'] ?? ''
                  ];
                }
              }
            }
          }
        }

        // Handle content_block_delta events
        if ($type === 'content_block_delta') {
          $delta = $event['delta'] ?? [];
          $deltaType = $delta['type'] ?? '';

          // Handle text deltas
          if ($deltaType === 'text_delta' && isset($delta['text'])) {
            $text = $delta['text'];
            $fullText .= $text;

            // Send text chunk to client
            echo "data: " . json_encode(['type' => 'text', 'text' => $text]) . "\n\n";
            flush();
          }

          // Handle citations_delta - this is where web search sources come from
          if ($deltaType === 'citations_delta' && isset($delta['citation'])) {
            $citation = $delta['citation'];
            if (isset($citation['url'])) {
              $sources[$citation['url']] = [
                'url' => $citation['url'],
                'title' => $citation['title'] ?? ''
              ];
              $searchUsed = true;
            }
          }
        }

        // Handle message_delta for web search detection
        if ($type === 'message_delta') {
          $usage = $event['usage'] ?? [];
          if (isset($usage['server_tool_use']['web_search_requests']) && $usage['server_tool_use']['web_search_requests'] > 0) {
            $searchUsed = true;
          }
        }

        // Handle message_stop - send final metadata
        if ($type === 'message_stop') {
          // Extract follow-up questions
          $followups = extract_followup_questions($fullText);

          // Format sources
          $sourceList = array_values($sources);
          $sourceList = array_slice($sourceList, 0, 8); // Cap at 8

          $markdownLinks = [];
          foreach ($sourceList as $src) {
            if (!empty($src['url'])) {
              $title = !empty($src['title']) ? $src['title'] : parse_url($src['url'], PHP_URL_HOST);
              $markdownLinks[] = "[{$title}]({$src['url']})";
            }
          }

          // Send final metadata event
          echo "data: " . json_encode([
            'type' => 'done',
            'mode' => $searchUsed ? 'web-grounded' : 'model-fallback',
            'markdown_links' => $markdownLinks,
            'sources' => array_column($sourceList, 'url'),
            'followup_questions' => $followups,
            'llm' => 'claude'
          ]) . "\n\n";
          flush();
        }
      }
    }

    return strlen($data);
  };

  // Make streaming API call
  $ch = curl_init("https://api.anthropic.com/v1/messages");
  curl_setopt_array($ch, [
    CURLOPT_HTTPHEADER => [
      "Content-Type: application/json",
      "x-api-key: $API_KEY",
      "anthropic-version: 2023-06-01",
    ],
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($requestBody, JSON_UNESCAPED_SLASHES),
    CURLOPT_WRITEFUNCTION => $streamCallback,
    CURLOPT_TIMEOUT => $TIMEOUT,
  ]);

  $result = curl_exec($ch);

  if ($result === false) {
    $error = curl_error($ch);
    curl_close($ch);
    echo "data: " . json_encode(['type' => 'error', 'error' => "Connection error: $error"]) . "\n\n";
    flush();
    exit;
  }

  $httpCode = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
  curl_close($ch);

  if ($httpCode >= 400) {
    echo "data: " . json_encode(['type' => 'error', 'error' => "API error (HTTP $httpCode)"]) . "\n\n";
    flush();
  }

  exit;

} else {
  // Non-streaming mode (fallback)
  header('Content-Type: application/json; charset=UTF-8');

  $ch = curl_init("https://api.anthropic.com/v1/messages");
  curl_setopt_array($ch, [
    CURLOPT_HTTPHEADER => [
      "Content-Type: application/json",
      "x-api-key: $API_KEY",
      "anthropic-version: 2023-06-01",
    ],
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => json_encode($requestBody, JSON_UNESCAPED_SLASHES),
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => $TIMEOUT,
  ]);

  $resp = curl_exec($ch);

  if ($resp === false) {
    $err = curl_error($ch);
    curl_close($ch);
    fail(502, "Connection error: $err");
  }

  $code = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
  curl_close($ch);

  if ($code < 200 || $code >= 300) {
    fail(502, "Claude HTTP $code", ['detail' => $resp]);
  }

  $json = json_decode($resp, true);
  if (!is_array($json)) {
    fail(502, "Claude returned non-JSON response");
  }

  // Extract text
  $text = '';
  $content = $json['content'] ?? [];
  foreach ($content as $block) {
    if (isset($block['type']) && $block['type'] === 'text' && isset($block['text'])) {
      $text .= $block['text'];
    }
  }

  // Extract sources (prioritize cited over searched)
  $cited = [];
  $searched = [];
  foreach ($content as $block) {
    // Check for inline citations in text blocks
    if (isset($block['citations']) && is_array($block['citations'])) {
      foreach ($block['citations'] as $citation) {
        if (isset($citation['url'])) {
          $cited[$citation['url']] = [
            'url' => $citation['url'],
            'title' => $citation['title'] ?? ''
          ];
        }
      }
    }
    // Check for web search results (various type names Claude might use)
    $blockType = $block['type'] ?? '';
    if (in_array($blockType, ['web_search_tool_result', 'server_tool_result', 'tool_result'])) {
      $results = $block['content'] ?? [];
      if (is_array($results)) {
        foreach ($results as $result) {
          if (isset($result['url']) && !isset($cited[$result['url']])) {
            $searched[$result['url']] = [
              'url' => $result['url'],
              'title' => $result['title'] ?? ''
            ];
          }
        }
      }
    }
  }

  // Also check for citations at the message level (some API versions)
  if (isset($json['citations']) && is_array($json['citations'])) {
    foreach ($json['citations'] as $citation) {
      if (isset($citation['url']) && !isset($cited[$citation['url']])) {
        $cited[$citation['url']] = [
          'url' => $citation['url'],
          'title' => $citation['title'] ?? ''
        ];
      }
    }
  }

  $sources = array_merge(array_values($cited), array_slice(array_values($searched), 0, 8 - count($cited)));
  $sources = array_slice($sources, 0, 8);

  // Check if web search was used
  $searchUsed = false;
  $usage = $json['usage'] ?? [];
  if (isset($usage['server_tool_use']['web_search_requests']) && $usage['server_tool_use']['web_search_requests'] > 0) {
    $searchUsed = true;
  }

  // Format markdown links
  $markdownLinks = [];
  foreach ($sources as $src) {
    if (!empty($src['url'])) {
      $title = !empty($src['title']) ? $src['title'] : parse_url($src['url'], PHP_URL_HOST);
      $markdownLinks[] = "[{$title}]({$src['url']})";
    }
  }

  // Extract follow-ups
  $followupQuestions = extract_followup_questions($text);

  echo json_encode([
    'mode'    => $searchUsed ? 'web-grounded' : 'model-fallback',
    'text'    => $text,
    'html'    => nl2br(htmlentities($text, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')),
    'markdown_links' => $markdownLinks,
    'sources' => array_column($sources, 'url'),
    'followup_questions' => $followupQuestions,
    'llm' => 'claude'
  ], JSON_UNESCAPED_SLASHES);
  exit;
}
