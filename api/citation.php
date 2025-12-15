<?php
// TruthAngel – citation echo v2: processes links and returns markdown format
// For Apache/web usage

// Extract title from HTML with fallback chain
function extract_title_from_html($html) {
    // Try <title> tag first
    if (preg_match('/<title[^>]*>(.*?)<\/title>/is', $html, $matches)) {
        $title = html_entity_decode(trim($matches[1]), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        if (!empty($title)) {
            return $title;
        }
    }
    
    // Fallback to first <h1> tag
    if (preg_match('/<h1[^>]*>(.*?)<\/h1>/is', $html, $matches)) {
        $h1 = strip_tags($matches[1]);
        $h1 = html_entity_decode(trim($h1), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        if (!empty($h1)) {
            return $h1;
        }
    }
    
    return null;
}

// Convert URLs to markdown links with descriptive titles
function convert_to_markdown($url) {
    // Follow redirects and fetch HTML
    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 10,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_USERAGENT => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    ]);
    
    $html = curl_exec($ch);
    $finalUrl = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);
    
    // Use original URL if redirect failed
    if (!$finalUrl || $httpCode >= 400 || $error) {
        error_log("Citation failed for $url: HTTP $httpCode, Error: $error");
        $finalUrl = $url;
        $html = '';
    }
    
    // Extract link text (title → h1 → domain)
    $linkText = null;
    
    if ($html && $httpCode === 200) {
        $linkText = extract_title_from_html($html);
    }
    
    // Fallback to domain if no title found
    if (!$linkText) {
        $parsed = parse_url($finalUrl);
        $linkText = $parsed['host'] ?? 'Source';
        $linkText = preg_replace('/^www\./', '', $linkText);
        $linkText = ucfirst($linkText);
    }
    
    // Clean up and truncate title
    $linkText = preg_replace('/\s+/', ' ', $linkText); // Normalize whitespace
    $linkText = trim($linkText);
    
    if (mb_strlen($linkText) > 100) {
        $linkText = mb_substr($linkText, 0, 97) . '...';
    }
    
    return "[{$linkText}]({$finalUrl})";
}

function main() {
    try {
        // Set JSON response header
        header('Content-Type: application/json');
        
        // Read raw POST data
        $raw = file_get_contents('php://input');
        $data = $raw ? json_decode($raw, true) : [];
        
        if (json_last_error() !== JSON_ERROR_NONE && $raw) {
            throw new Exception("Invalid JSON input");
        }
        
        // Get links from either 'links' or 'urls' key
        $links = $data['links'] ?? $data['urls'] ?? [];
        
        if (!is_array($links)) {
            throw new Exception("`links` must be an array");
        }
        
        // items: object form (compatible with your earlier consumer)
        $items = [];
        foreach ($links as $url) {
            // Check if already in markdown format [text](url)
            if (preg_match('/^\[([^\]]+)\]\(([^)]+)\)$/', $url, $matches)) {
                // Already markdown, pass through
                $markdown = $url;
                $actualUrl = $matches[2]; // Extract the URL from markdown
            } else {
                // Raw URL, convert to markdown
                $markdown = convert_to_markdown($url);
                // Extract actual URL from generated markdown
                preg_match('/\(([^)]+)\)$/', $markdown, $urlMatch);
                $actualUrl = $urlMatch[1] ?? $url;
            }
            
            // Skip if URL is still a failed Vertex redirect (starts with vertexaisearch and matches original input)
            if (strpos($actualUrl, 'vertexaisearch.cloud.google.com/grounding-api-redirect/') !== false 
                && $actualUrl === $url) {
                // This means the redirect failed - skip this URL entirely
                continue;
            }
            
            $items[] = [
                'input' => $url,
                'url' => $actualUrl,
                'markdown' => $markdown,
                'status' => 'ok'
            ];
        }
        
        // ask_links: resolved URLs
        $ask_links = array_column($items, 'url');
        
        $out = [
            'ok' => true,
            'items' => $items,
            'ask_links' => $ask_links
        ];
        
        echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        
    } catch (Exception $e) {
        http_response_code(400);
        echo json_encode([
            'ok' => false,
            'error' => $e->getMessage()
        ]);
    }
}

main();
?>
