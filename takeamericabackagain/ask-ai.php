<?php
header("Content-Type: application/json");

$apiKey = getenv("OPENAI_API_KEY"); // from .htaccess
$input = json_decode(file_get_contents("php://input"), true);
$prompt = $input["prompt"] ?? "";

if (!$prompt) {
  echo json_encode(["error" => "No prompt provided"]);
  exit;
}

$ch = curl_init("https://api.openai.com/v1/responses");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
  "Content-Type: application/json",
  "Authorization: Bearer $apiKey"
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
  "model" => "gpt-4o-mini",
  "input" => $prompt,
  "max_output_tokens" => 3000
]));

$response = curl_exec($ch);

if (curl_errno($ch)) {
  echo json_encode(["error" => curl_error($ch)]);
  exit;
}
curl_close($ch);

echo $response;
