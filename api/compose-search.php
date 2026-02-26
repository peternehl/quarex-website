<?php
/**
 * compose-search.php — Topic Search API for Quarex Compose
 *
 * Searches quarex-catalog.db using FTS5 full-text search on topics.
 * Returns topics with full lineage (chapter → book → shelf → library → type).
 *
 * POST JSON: {"q": "search terms", "limit": 30}
 * Returns JSON: {"results": [...], "count": N}
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
    if (in_array($origin, $allowedOrigins)) return true;
    if (preg_match('/^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/', $origin)) return true;
    return false;
}

$requestOrigin = $_SERVER['HTTP_ORIGIN'] ?? '';
$isAllowedOrigin = is_allowed_origin($requestOrigin, $ALLOWED_ORIGINS);

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    if ($isAllowedOrigin) {
        header("Access-Control-Allow-Origin: $requestOrigin");
        header('Access-Control-Allow-Methods: POST, OPTIONS');
        header('Access-Control-Allow-Headers: Content-Type');
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

// Set CORS headers
if ($isAllowedOrigin) {
    header("Access-Control-Allow-Origin: $requestOrigin");
}

header('Content-Type: application/json; charset=utf-8');

// ------------------------ Rate Limiting ------------------------
function check_rate_limit(string $ip, int $maxRequests = 30, int $windowSeconds = 60): bool {
    $logDir = __DIR__ . '/logs';
    if (!is_dir($logDir)) @mkdir($logDir, 0755, true);

    $rateLimitFile = $logDir . '/rate_limits_compose.json';
    $ipHash = md5($ip);
    $now = time();

    $data = [];
    if (file_exists($rateLimitFile)) {
        $raw = @file_get_contents($rateLimitFile);
        if ($raw) $data = json_decode($raw, true) ?: [];
    }

    // Clean old entries
    if (isset($data[$ipHash])) {
        $data[$ipHash] = array_filter($data[$ipHash], fn($t) => $t > ($now - $windowSeconds));
    }

    $requestCount = count($data[$ipHash] ?? []);
    if ($requestCount >= $maxRequests) return false;

    $data[$ipHash][] = $now;
    @file_put_contents($rateLimitFile, json_encode($data), LOCK_EX);
    return true;
}

$clientIp = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
if (!check_rate_limit($clientIp)) {
    http_response_code(429);
    echo json_encode(['error' => 'Rate limit exceeded. Please wait a moment.']);
    exit;
}

// ------------------------ Parse Input ------------------------
$rawInput = file_get_contents('php://input');
$input = json_decode($rawInput, true);

if (!$input || empty($input['q'])) {
    // Try query params as fallback
    $input = [
        'q' => $_GET['q'] ?? $_POST['q'] ?? '',
        'limit' => (int)($_GET['limit'] ?? $_POST['limit'] ?? 30),
    ];
}

$query = trim($input['q'] ?? '');
$limit = min(max((int)($input['limit'] ?? 30), 1), 100);

// Sanitize: strip HTML, limit length
$query = strip_tags($query);
$query = mb_substr($query, 0, 500);
$query = trim($query);

if (strlen($query) < 2) {
    echo json_encode(['results' => [], 'count' => 0]);
    exit;
}

// ------------------------ Database Search ------------------------
$dbPath = __DIR__ . '/../database/quarex-catalog.db';

if (!file_exists($dbPath)) {
    http_response_code(500);
    echo json_encode(['error' => 'Database not available']);
    exit;
}

try {
    $db = new PDO('sqlite:' . $dbPath, null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);

    // Build FTS5 match expression — individual words with prefix matching
    // Strip punctuation, split into words, drop short/stop words
    $stopWords = ['a','an','the','is','are','was','were','how','what','why','when','where',
                  'do','does','did','has','have','had','be','been','being','of','in','to',
                  'for','on','at','by','with','and','or','but','not','its','it','this','that'];
    $words = preg_split('/[^a-zA-Z0-9]+/', strtolower($query), -1, PREG_SPLIT_NO_EMPTY);
    $words = array_filter($words, fn($w) => strlen($w) >= 3 && !in_array($w, $stopWords));
    $words = array_values(array_slice($words, 0, 10)); // Cap at 10 terms

    if (empty($words)) {
        echo json_encode(['results' => [], 'count' => 0]);
        exit;
    }

    // FTS5: each word with prefix match
    // Try AND first (all terms must appear) for precise results
    // Fall back to OR if AND returns fewer than 5 results
    $wordExpressions = array_map(fn($w) => '"' . $w . '"*', $words);
    $ftsQueryAnd = implode(' AND ', $wordExpressions);
    $ftsQueryOr = implode(' OR ', $wordExpressions);

    $sql = "
        SELECT
            tp.id as topic_id,
            tp.question,
            c.name as chapter,
            c.id as chapter_id,
            b.name as book,
            b.id as book_id,
            s.name as shelf,
            s.slug as shelf_slug,
            l.name as library,
            l.slug as library_slug,
            lt.name as library_type
        FROM topics_fts
        JOIN topics tp ON topics_fts.rowid = tp.id
        JOIN chapters c ON tp.chapter_id = c.id
        JOIN books b ON c.book_id = b.id
        JOIN shelves s ON b.shelf_id = s.id
        JOIN libraries l ON s.library_id = l.id
        JOIN library_types lt ON l.library_type_id = lt.id
        WHERE topics_fts MATCH :query
        ORDER BY bm25(topics_fts, 1.0, 10.0, 5.0)
        LIMIT :overfetch
    ";

    $maxPerBook = 3;
    $maxPerBookAnd = 10;
    $overfetch = $limit * 6; // Fetch extra so we can still fill $limit after per-book cap

    // Try AND first
    $stmt = $db->prepare($sql);
    $stmt->bindValue(':query', $ftsQueryAnd, PDO::PARAM_STR);
    $stmt->bindValue(':overfetch', $overfetch, PDO::PARAM_INT);
    $stmt->execute();
    $andResults = $stmt->fetchAll();

    // Collect AND results with relaxed per-book cap (10)
    $bookCounts = [];
    $results = [];
    $seenTopicIds = [];
    foreach ($andResults as $row) {
        $bookId = $row['book_id'];
        $bookCounts[$bookId] = ($bookCounts[$bookId] ?? 0) + 1;
        if ($bookCounts[$bookId] <= $maxPerBookAnd) {
            $results[] = $row;
            $seenTopicIds[$row['topic_id']] = true;
            if (count($results) >= $limit) break;
        }
    }

    // Supplement with OR results if AND didn't fill the limit
    if (count($results) < $limit && count($words) > 1) {
        $stmt = $db->prepare($sql);
        $stmt->bindValue(':query', $ftsQueryOr, PDO::PARAM_STR);
        $stmt->bindValue(':overfetch', $overfetch, PDO::PARAM_INT);
        $stmt->execute();
        $orResults = $stmt->fetchAll();

        $orBookCounts = [];
        foreach ($results as $row) {
            $orBookCounts[$row['book_id']] = ($orBookCounts[$row['book_id']] ?? 0) + 1;
        }

        foreach ($orResults as $row) {
            if (count($results) >= $limit) break;
            if (isset($seenTopicIds[$row['topic_id']])) continue;
            $bookId = $row['book_id'];
            $orBookCounts[$bookId] = ($orBookCounts[$bookId] ?? 0) + 1;
            if ($orBookCounts[$bookId] <= $maxPerBook) {
                $results[] = $row;
                $seenTopicIds[$row['topic_id']] = true;
            }
        }
    }

    // Map library type names to URL abbreviations
    $typeAbbrevMap = [
        'Knowledge' => 'k',
        'Practical Skills' => 'pr',
        'Events' => 'e',
        'Event' => 'e',
        'Perspectives' => 'pe',
        'Politicians' => 'c',
        'Politician' => 'c',
        'Geography' => 'g',
        'Infrastructure' => 'i',
    ];

    // Add type abbreviation and book slug to each result
    foreach ($results as &$row) {
        $row['type_abbrev'] = $typeAbbrevMap[$row['library_type']] ?? 'k';

        // Generate book slug from book name
        $row['book_slug'] = strtolower(preg_replace('/[^a-z0-9]+/i', '-', $row['book']));
        $row['book_slug'] = trim($row['book_slug'], '-');
    }
    unset($row);

    echo json_encode([
        'results' => $results,
        'count' => count($results),
        'query' => $query,
    ]);

} catch (PDOException $e) {
    error_log("compose-search.php PDO error: " . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Search failed']);
}
