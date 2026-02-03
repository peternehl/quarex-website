<?php
// ai-gateway.php — single endpoint for index.html + trump-lies.html + future *-lies.html
// Backward-compatible: no changes required to existing pages.
// Add ?m=ask or ?m=lies in the URL, or send {"module":"ask"|"lies"} if you want explicit routing.

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$raw = file_get_contents('php://input');
$in  = json_decode($raw, true) ?: [];

// ---- Helpers ----
function s($a,$k,$d=''){ return isset($a[$k]) ? trim((string)$a[$k]) : $d; }
function bad($code,$msg){ http_response_code($code); echo json_encode(['error'=>$msg]); exit; }

// Optional explicit module via query or body:
$module  = $_GET['m'] ?? s($in,'module','');   // "ask" | "lies" | ...
$subject = s($in,'subject','');                // e.g., "trump", "vance"

// Auto-detect if not provided:
$hasPrompt = isset($in['prompt']) && $in['prompt'] !== '';
$hasClaim  = isset($in['claim'])  && $in['claim']  !== '';

if ($module === '') {
  if     ($hasClaim)  $module = 'lies';
  elseif ($hasPrompt) $module = 'ask';
}

// ---- Stubbed model call (swap with real OpenAI later) ----
function call_llm($system, $user, $want='text') {
  // TODO: replace with real OpenAI call. Keep shapes below.
  $demo = "Placeholder answer based on:\n" . $user;
  return ($want === 'text') ? $demo : [
    'summary' => mb_strimwidth(strip_tags($user),0,200,'…'),
    'points'  => ['Demo point 1','Demo point 2'],
    'rating'  => 3,
    'sources' => [],
  ];
}

// ---- Handlers ----

// 1) Ask-AI (index.html) — expects { output:[{content:[{text}]}] }
function handle_ask($in){
  $prompt = s($in,'prompt');
  if ($prompt==='') bad(400,'Missing "prompt".');
  $sys = "You are a helpful assistant. Keep answers concise and clear.";
  $txt = call_llm($sys, $prompt, 'text');
  return ['output' => [[ 'content' => [[ 'text' => $txt ]] ]]];
}

// 2) Lie analysis (trump-lies.html, vance-lies.html, etc.)
//    Expects/returns: { summary, points[], rating(1-5), sources[] }
function handle_lies($in){
  // Accept the current fields used by trump-lies.html
  $payload = [
    'claim'      => s($in,'claim'),
    'context'    => s($in,'context'),
    'category'   => s($in,'category'),
    'date'       => s($in,'date'),
    'source_url' => s($in,'source_url'),
    'verdict'    => s($in,'verdict'),
    'notes'      => s($in,'notes'),
    'subject'    => s($in,'subject'), // optional: "trump", "vance", etc.
  ];
  if ($payload['claim']==='') bad(400,'Missing "claim".');

  $sys = "You fact-check political claims. Return a short summary, 2-6 bullet points, a deception rating 1-5, and sources if known.";
  $user = json_encode($payload, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE);
  $ans  = call_llm($sys, $user, 'analysis');

  // Ensure shape for the frontend:
  $rating = 3;
  $v = strtolower($payload['verdict']);
  if ($v) {
    if (preg_match('/pants on fire|fabrication|\bfalse\b/',$v)) $rating = 5;
    elseif (preg_match('/mostly false|misleading/',$v)) $rating = 4;
    elseif (preg_match('/half true|mixed|cherry/',$v)) $rating = 3;
    elseif (preg_match('/mostly true/',$v)) $rating = 2;
    elseif (preg_match('/\btrue\b/',$v)) $rating = 1;
  }
  // Merge model output with deterministic rating & source passthrough
  $ans['rating']  = $ans['rating']  ?? $rating;
  $ans['sources'] = $ans['sources'] ?? ($payload['source_url'] ? [$payload['source_url']] : []);

  return $ans;
}

// ---- Router ----
try {
  switch ($module) {
    case 'ask':  echo json_encode(handle_ask($in),  JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE); break;
    case 'lies': echo json_encode(handle_lies($in), JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE); break;
    default:
      // Backstop: keep current behavior working by inferring shapes
      if ($hasClaim)  { echo json_encode(handle_lies($in), JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE); }
      elseif ($hasPrompt) { echo json_encode(handle_ask($in), JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE); }
      else bad(400,'Send either {"prompt": "..."} or lie fields like {"claim": "..."} (optionally include {"module": "ask"|"lies"}).');
  }
} catch (Throwable $e) {
  http_response_code(500);
  echo json_encode(['error'=>'Server error','detail'=>$e->getMessage()]);
}
