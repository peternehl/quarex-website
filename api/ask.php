<?php
// Load local config if exists (for development)
if (file_exists(__DIR__ . '/config.php')) {
    require_once __DIR__ . '/config.php';
}

/**
 * ask.php — Gemini 2.5 Flash-Lite (search-first, fallback to model knowledge)
 * Returns JSON:
 * {
 *   "mode": "web-grounded" | "web-first-no-metadata" | "model-fallback",
 *   "text": "<plain text>",
 *   "html": "<text with <br> breaks>",
 *   "sources": ["https://...", ...]  // only when grounded
 * }
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

// For local development, allow any localhost port
function is_allowed_origin(string $origin, array $allowedOrigins): bool {
  if (in_array($origin, $allowedOrigins)) {
    return true;
  }
  // Allow localhost with any port for development
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

// Validate origin for actual requests
if ($requestOrigin && !$isAllowedOrigin) {
  log_security_event('BLOCKED_ORIGIN', "Request from unauthorized origin", ['origin' => $requestOrigin]);
  http_response_code(403);
  echo json_encode(['error' => 'Forbidden']);
  exit;
}

// Validate referer as secondary check (if present)
$referer = $_SERVER['HTTP_REFERER'] ?? '';
if ($referer) {
  $refererValid = false;
  foreach ($ALLOWED_ORIGINS as $allowed) {
    if (strpos($referer, $allowed) === 0) {
      $refererValid = true;
      break;
    }
  }
  // Also allow localhost referers
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

// Set CORS headers for valid requests
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
$MODEL   = getenv('GEMINI_MODEL') ?: 'gemini-2.5-flash-lite';
$TIMEOUT = 60; // seconds

// Auto-cleanup PHP error_log (7 days or 10MB limit)
$phpErrorLog = __DIR__ . '/error_log';
if (file_exists($phpErrorLog)) {
  // Size check - truncate if over 10MB
  if (filesize($phpErrorLog) > 10 * 1024 * 1024) {
    $lines = @file($phpErrorLog);
    if ($lines && count($lines) > 2000) {
      $lines = array_slice($lines, -2000); // Keep last 2000 lines
      @file_put_contents($phpErrorLog, implode('', $lines), LOCK_EX);
    }
  }
  // Age check - clean old entries occasionally (1% of requests)
  elseif (mt_rand(1, 100) === 1) {
    $cutoff = strtotime('-7 days');
    $lines = @file($phpErrorLog, FILE_IGNORE_NEW_LINES);
    if ($lines) {
      $newLines = [];
      foreach ($lines as $line) {
        // PHP error_log format: [DD-Mon-YYYY HH:MM:SS timezone] message
        if (preg_match('/^\[(\d{2}-\w{3}-\d{4} \d{2}:\d{2}:\d{2})/', $line, $m)) {
          $logTime = strtotime($m[1]);
          if ($logTime && $logTime >= $cutoff) {
            $newLines[] = $line;
          }
        } else {
          $newLines[] = $line; // Keep lines without timestamp
        }
      }
      if (count($newLines) < count($lines)) {
        @file_put_contents($phpErrorLog, implode("\n", $newLines) . "\n", LOCK_EX);
      }
    }
  }
}

// ------------------------ Security: Content Filter ------------------------
function load_blocked_patterns(): array {
  static $cached_patterns = null;

  // Return cached patterns if already loaded
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
    // Skip comments and empty lines
    if ($line === '' || $line[0] === '#') {
      continue;
    }
    // Add word boundaries and case-insensitive flag
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

// Log security events
function log_security_event(string $type, string $message, array $context = []) {
  $logDir = __DIR__ . '/logs';
  if (!is_dir($logDir)) {
    @mkdir($logDir, 0755, true);
  }

  $logFile = $logDir . '/security.log';

  // Auto-cleanup: Remove entries older than 7 days OR if file exceeds 10MB
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

// Cleanup log files - remove old entries or truncate if too large
function cleanup_log_file(string $logFile, int $maxDays = 7, int $maxBytes = 10485760) {
  if (!file_exists($logFile)) {
    return;
  }

  // Check size first - if over limit, truncate immediately
  if (filesize($logFile) > $maxBytes) {
    // Keep only last 1000 lines before truncating
    $lines = file($logFile);
    if ($lines && count($lines) > 1000) {
      $lines = array_slice($lines, -1000);
      @file_put_contents($logFile, implode('', $lines), LOCK_EX);
    } else {
      @file_put_contents($logFile, '', LOCK_EX); // Clear if can't read
    }
    return;
  }

  // Check age - remove entries older than maxDays (run occasionally, not every request)
  // Only run cleanup 1% of the time to reduce overhead
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
      // Keep non-JSON lines (shouldn't happen, but be safe)
      $newLines[] = $line;
    }
  }

  if (count($newLines) < count($lines)) {
    @file_put_contents($logFile, implode("\n", $newLines) . "\n", LOCK_EX);
  }
}

// Rate limiting
function check_rate_limit(string $ip, int $maxRequests = 20, int $windowSeconds = 60): bool {
  $logDir = __DIR__ . '/logs';
  if (!is_dir($logDir)) {
    @mkdir($logDir, 0755, true);
  }

  $rateFile = $logDir . '/rate_limits.json';
  $now = time();

  // Load existing data
  $data = [];
  if (file_exists($rateFile)) {
    $content = @file_get_contents($rateFile);
    if ($content) {
      $data = json_decode($content, true) ?: [];
    }
  }

  // Clean old entries (older than window)
  foreach ($data as $key => $timestamps) {
    $data[$key] = array_filter($timestamps, fn($t) => ($now - $t) < $windowSeconds);
    if (empty($data[$key])) {
      unset($data[$key]);
    }
  }

  // Check current IP
  $ipKey = md5($ip); // Hash IP for privacy
  $requests = $data[$ipKey] ?? [];

  if (count($requests) >= $maxRequests) {
    return false; // Rate limit exceeded
  }

  // Add current request
  $requests[] = $now;
  $data[$ipKey] = $requests;

  // Save
  @file_put_contents($rateFile, json_encode($data), LOCK_EX);

  return true; // OK to proceed
}

// ------------------------ Utilities ------------------------
function fail($code, $msg, $extra = []) {
  http_response_code($code);
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

// Single non-streaming Gemini call
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

// Extract plain text from Gemini response
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

// Extract source URLs from groundingMetadata (best-effort)
function gemini_extract_sources(array $resp): array {
  $cand = $resp['candidates'][0] ?? null;
  if (!$cand) return [];
  $gm = $cand['groundingMetadata'] ?? null;
  if (!$gm) return [];

  $urls = [];
  // Search entry point URL (often present)
  if (!empty($gm['searchEntryPoint']['url'])) {
    $urls[] = $gm['searchEntryPoint']['url'];
  }
  // Common buckets where URLs appear
  $buckets = [
    $gm['groundingChunks'] ?? [],
    $gm['supportingEvidence'] ?? [],
    $gm['sources'] ?? [],
  ];
  foreach ($buckets as $group) {
    if (!is_array($group)) continue;
    foreach ($group as $item) {
      if (isset($item['web']['uri']) && is_string($item['web']['uri']))      $urls[] = $item['web']['uri'];
      if (isset($item['sourceUrl']) && is_string($item['sourceUrl']))        $urls[] = $item['sourceUrl'];
      if (isset($item['metadata']['url']) && is_string($item['metadata']['url'])) $urls[] = $item['metadata']['url'];
      if (isset($item['url']) && is_string($item['url']))                    $urls[] = $item['url'];
    }
  }
  // Deduplicate + keep only http(s)
  $urls = array_values(array_unique(array_filter($urls, fn($u) => is_string($u) && preg_match('#^https?://#i', $u))));
  return $urls;
}

// Extract follow-up questions from response text
function extract_followup_questions(string $text): array {
  $questions = [];
  
  // Look for the follow-up questions section
  if (preg_match('/Follow-up questions?:?\s*(.*?)(?:\n\n|$)/is', $text, $match)) {
    $section = $match[1];
    
    // Extract numbered questions (1. Question text)
    if (preg_match_all('/\d+\.\s*(.+?)(?=\n\d+\.|\n*$)/s', $section, $matches)) {
      foreach ($matches[1] as $q) {
        $q = trim($q);
        if (!empty($q)) {
          $questions[] = $q;
        }
      }
    }
  }
  
  // Return exactly 3 questions (pad with empty if needed)
  return array_slice(array_pad($questions, 3, ''), 0, 3);
}

// Helper function to get markdown links from citation.php
function get_markdown_links(array $sources): array {
  if (empty($sources)) return [];
  
  $protocol = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
  $host = $_SERVER['HTTP_HOST'] ?? 'localhost';
  $scriptDir = dirname($_SERVER['SCRIPT_NAME'] ?? '');
  $endpoint = rtrim("$protocol://$host$scriptDir", '/') . '/citation.php';
  
  $ch = curl_init($endpoint);
  curl_setopt_array($ch, [
    CURLOPT_POST           => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
    CURLOPT_POSTFIELDS     => json_encode(['links' => $sources], JSON_UNESCAPED_SLASHES),
    CURLOPT_TIMEOUT        => 30,
    CURLOPT_CONNECTTIMEOUT => 10,
  ]);
  $respCit = curl_exec($ch);
  $info    = curl_getinfo($ch);
  
  $markdownLinks = [];
  if ($respCit === false) {
    error_log("citation POST failed: " . curl_error($ch));
  } else {
    error_log("citation POST {$info['http_code']} to $endpoint");
    
    // Parse the citation.php response
    $citationData = json_decode($respCit, true);
    if ($citationData && isset($citationData['ok']) && $citationData['ok']) {
      // Extract markdown links from items
      foreach ($citationData['items'] as $item) {
        if (isset($item['markdown'])) {
          $markdownLinks[] = $item['markdown'];
        }
      }
      error_log("Extracted " . count($markdownLinks) . " markdown links");
    }
  }
  curl_close($ch);
  
  return $markdownLinks;
}

// ------------------------ Read input ------------------------
$bodyJson = read_json_body();
$q = null;

// Accept prompt from JSON { "q": "..." } or form/query param ?q=...
if ($bodyJson && isset($bodyJson['q'])) {
  $q = trim(strval($bodyJson['q']));
} else {
  $q = trim(strval($_REQUEST['q'] ?? ''));
}

if ($q === '') {
  fail(400, "Missing 'q' parameter. Provide your question as JSON {\"q\":\"...\"} or ?q=...");
}

// ------------------------ Security Checks ------------------------
// 1. Rate limiting
$clientIP = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
if (!check_rate_limit($clientIP)) {
  log_security_event('RATE_LIMITED', "Rate limit exceeded", ['query' => substr($q, 0, 100)]);
  fail(429, 'Too many requests. Please wait before trying again.');
}

// 2. Content filtering - BLOCK harmful queries BEFORE they reach Gemini
if (is_harmful_query($q)) {
  log_security_event('BLOCKED_CONTENT', "Harmful query blocked", ['query' => substr($q, 0, 200)]);
  fail(403, 'Your request cannot be processed.');
}

// 3. Log all requests (for monitoring)
log_security_event('REQUEST', "API request", ['query' => substr($q, 0, 200)]);

// Capture category (subject area) from request
$category = '';
if ($bodyJson && isset($bodyJson['category'])) {
  $category = trim(strval($bodyJson['category']));
} else {
  $category = trim(strval($_REQUEST['category'] ?? ''));
}

// Optional controls from client (safe defaults/clamps)
$temperature = clamp($_REQUEST['temperature'] ?? ($bodyJson['temperature'] ?? null), 0.0, 2.0, 0.4);
$topP        = clamp($_REQUEST['top_p'] ?? ($bodyJson['top_p'] ?? null),           0.0, 1.0, 0.9);
$topK        = intval(clamp($_REQUEST['top_k'] ?? ($bodyJson['top_k'] ?? null),    1,  100,  40));
$maxTokens   = intval(clamp($_REQUEST['max_tokens'] ?? ($bodyJson['max_tokens'] ?? null), 64, 20000, 8000));
$forceJson   = !!($_REQUEST['force_json'] ?? ($bodyJson['force_json'] ?? false)); // true/false

// ------------------------ Build base Gemini payload ------------------------

// Quarex definition - included when context mentions Quarex
$quarexDefinition = "";
if ($category && stripos($category, 'quarex') !== false) {
  $quarexDefinition = "IMPORTANT CONTEXT - Quarex Definition: A quarex is a dynamically generated, recursively structured knowledge artifact that evolves through iterative inquiry. It is a new medium for organizing knowledge—neither a traditional book nor a dataset, but a living system that reorganizes itself as new questions emerge. Key principles: (1) Living Evolution - continuously grows based on new inquiries, (2) Flexible Navigation - users can enter at any point without losing coherence, (3) Guided Expansion - AI generates content while human architects maintain creative control, (4) Exploration-Focused - designed for deep inquiry rather than linear consumption. Quarex represents a post-book paradigm for knowledge organization. See quarex.org for more. ";
}

$baseBody = [
  "contents" => [[
    "role"  => "user",
    "parts" => [["text" => $q]]
  ]],
  "systemInstruction" => [
    "role"  => "system",
    "parts" => [["text" =>
      "You are an expert academic assistant. Write at a clear 12th-grade level. " .
      "RECENCY: Always prioritize the most current and up-to-date information available. When discussing facts, statistics, " .
      "policies, or events, use the latest data from 2024-2025 whenever possible. If information may have changed recently, " .
      "explicitly note the date or timeframe of your sources. Avoid presenting outdated information as current. " .
      "LANGUAGE: If the user's message begins with 'Please respond in [language]', you MUST write your ENTIRE response " .
      "in that language, including the follow-up questions. This applies to all languages including Japanese (日本語), " .
      "Korean (한국어), Simplified Chinese (简体中文), Traditional Chinese (繁體中文), and all others. " .
      $quarexDefinition .
      ($category ? "This question is in the context of: $category. Provide answers relevant to this subject area. " : "") .
      "SAFETY: If a query requests information about illegal activities, violence, exploitation, self-harm, " .
      "or other harmful content, begin your response with exactly [FLAGGED:SAFETY] followed by a polite " .
      "refusal explaining you cannot assist with that topic. " .
      "IMPORTANT: At the end of every answer, you MUST provide exactly 3 contextual follow-up questions " .
      "that help the user explore the topic deeper. Format them clearly as:\n\n" .
      "Follow-up questions:\n1. [First question]\n2. [Second question]\n3. [Third question]"
    ]]
  ],
  "generationConfig" => array_filter([
    "temperature"     => $temperature,
    "topP"            => $topP,
    "topK"            => $topK,
    "maxOutputTokens" => (int)$maxTokens,
  ], fn($v) => $v !== null),
];

// Optional: force model to return structured JSON (schema example)
if ($forceJson) {
  $baseBody["generationConfig"]["responseMimeType"] = "application/json";
  $baseBody["generationConfig"]["responseJsonSchema"] = [
    "type" => "object",
    "properties" => [
      "answer"  => ["type" => "string"],
      "sources" => ["type" => "array", "items" => ["type" => "string"]],
    ],
    "required" => ["answer"]
  ];
}

// ------------------------ 1) Search-first attempt ------------------------
$searchFirst = $baseBody;
$searchFirst["tools"] = [["google_search" => new stdClass()]];

try {
  $resp1 = gemini_call($MODEL, $API_KEY, $searchFirst, $TIMEOUT);
  $text1 = gemini_extract_text($resp1);
  $sources1 = gemini_extract_sources($resp1);

  // Check for Gemini safety flag
  if (strpos($text1, '[FLAGGED:SAFETY]') !== false) {
    log_security_event('GEMINI_SAFETY_FLAG', "Gemini flagged query as unsafe", ['query' => substr($q, 0, 200)]);
    echo json_encode([
      'mode'    => 'blocked',
      'text'    => 'I cannot assist with that request.',
      'html'    => 'I cannot assist with that request.',
      'markdown_links' => [],
      'followup_questions' => []
    ], JSON_UNESCAPED_SLASHES);
    exit;
  }

  // Get markdown links from citation.php
  $markdownLinks = get_markdown_links($sources1);

  if ($text1 !== '') {
    // Extract follow-up questions
    $followupQuestions = extract_followup_questions($text1);

    // Sometimes the model used the tool but metadata is sparse; still return what we have.
    echo json_encode([
      'mode'    => 'web-first-no-metadata',
      'text'    => $text1,
      'html'    => nl2br(htmlentities($text1, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')),
      'markdown_links' => $markdownLinks, // Only markdown links, no raw sources
      'followup_questions' => $followupQuestions, // Add follow-up questions
    ], JSON_UNESCAPED_SLASHES);
    exit;
  }

} catch (Exception $e) {
  // Fall through to fallback; log the search failure
  error_log("Search-first failed: " . $e->getMessage());
}

// ------------------------ 2) Fallback: model-only ------------------------
try {
  $resp2 = gemini_call($MODEL, $API_KEY, $baseBody, $TIMEOUT);
  $text2 = gemini_extract_text($resp2);
  if ($text2 === '') throw new Exception("Empty response from model fallback");

  // Check for Gemini safety flag
  if (strpos($text2, '[FLAGGED:SAFETY]') !== false) {
    log_security_event('GEMINI_SAFETY_FLAG', "Gemini flagged query as unsafe (fallback)", ['query' => substr($q, 0, 200)]);
    echo json_encode([
      'mode'    => 'blocked',
      'text'    => 'I cannot assist with that request.',
      'html'    => 'I cannot assist with that request.',
      'markdown_links' => [],
      'followup_questions' => []
    ], JSON_UNESCAPED_SLASHES);
    exit;
  }

  // Extract follow-up questions
  $followupQuestions = extract_followup_questions($text2);

  echo json_encode([
    'mode'    => 'model-fallback',
    'text'    => $text2,
    'html'    => nl2br(htmlentities($text2, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')),
    'markdown_links' => [], // No sources in fallback mode
    'followup_questions' => $followupQuestions, // Add follow-up questions
  ], JSON_UNESCAPED_SLASHES);
  exit;

} catch (Exception $e) {
  fail(502, 'Gemini fallback failed', ['detail' => $e->getMessage()]);
}