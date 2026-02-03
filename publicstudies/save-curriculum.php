<?php
// Local-only utility: saves curriculum-index.json from the admin page.
// Do NOT upload this to the server.

header('Content-Type: application/json');

// Only allow POST
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'POST only']);
    exit;
}

$input = file_get_contents('php://input');
$data = json_decode($input);

if ($data === null) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// Pretty-print and save
$json = json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
$path = __DIR__ . '/curriculum-index.json';

if (file_put_contents($path, $json . "\n") !== false) {
    echo json_encode(['success' => true, 'path' => $path]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Could not write file']);
}
