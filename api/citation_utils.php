<?php
// Shared utility functions for cURL network requests.

// Constants needed for the cURL function (pulled from citation.php)
const HTTP_TIMEOUT_SEC = 15;
const MAX_REDIRECTS    = 10;

// Core HTTP function: Performs GET request, follows redirects, and returns 4 values.
function http_get_follow($url, $timeout = HTTP_TIMEOUT_SEC){
    $ch = curl_init($url);
    $headers = [
        'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language: en',
    ];
    curl_setopt_array($ch, [
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS      => MAX_REDIRECTS,
        CURLOPT_CONNECTTIMEOUT => $timeout,
        CURLOPT_TIMEOUT        => $timeout,
        CURLOPT_USERAGENT      => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        CURLOPT_HTTPHEADER     => $headers,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
    ]);
    $body = curl_exec($ch);
    $finalUrl = curl_getinfo($ch, CURLINFO_EFFECTIVE_URL);
    $err      = curl_error($ch);
    $code     = curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);

    if ($body === false && !empty($err)) {
        // Return 4 values: URL, empty body, 0 code, error string
        return [ $url, '', $code ?: 0, $err ]; 
    }
    // Return 4 values: Final URL, Body, HTTP Code, empty error string
    return [ $finalUrl ?: $url, $body ?: '', $code ?: 0, '' ];
}

// Function to handle relative URLs (pulled from vertex_unwrap.php)
function url_to_abs($rel, $base){
    $baseParts = parse_url($base);
    if (!$baseParts || empty($baseParts['scheme']) || empty($baseParts['host'])) return $rel;
    if (parse_url($rel, PHP_URL_SCHEME)) return $rel;

    $root = $baseParts['scheme'].'://'.$baseParts['host'].(isset($baseParts['port'])?':'.$baseParts['port']:'');
    if ($rel !== '' && $rel[0] === '/') return $root.$rel;

    $dir = isset($baseParts['path']) ? preg_replace('~/[^/]*$~','/',$baseParts['path']) : '/';
    return $root.$dir.$rel;
}