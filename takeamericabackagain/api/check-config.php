<?php
header('Content-Type: application/json');
$cfg = __DIR__ . '/../config.php';
$ok  = is_file($cfg);
if ($ok) {
  require $cfg;
  $hasVar = isset($OPENAI_API_KEY) && is_string($OPENAI_API_KEY) && str_starts_with($OPENAI_API_KEY, 'sk-');
} else {
  $hasVar = false;
}
echo json_encode(['config_found'=>$ok, 'var_present'=>$hasVar, 'path'=>$cfg]);
