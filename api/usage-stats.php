<?php
/**
 * Usage Statistics Dashboard
 * View Claude API usage and costs
 *
 * Access: /api/usage-stats.php
 * Add ?key=YOUR_SECRET to restrict access
 */

// Optional: Add a simple access key for security
$ACCESS_KEY = getenv('USAGE_STATS_KEY') ?: '';
if ($ACCESS_KEY && ($_GET['key'] ?? '') !== $ACCESS_KEY) {
  http_response_code(403);
  die('Access denied. Add ?key=YOUR_KEY to URL.');
}

$dbPath = __DIR__ . '/logs/usage.sqlite';

if (!file_exists($dbPath)) {
  die('No usage data yet. Database will be created on first API call.');
}

try {
  $db = new PDO('sqlite:' . $dbPath);
  $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (Exception $e) {
  die('Database error: ' . $e->getMessage());
}

// Get summary stats
$summary = $db->query("
  SELECT
    COUNT(*) as total_queries,
    SUM(input_tokens) as total_input,
    SUM(output_tokens) as total_output,
    SUM(cache_creation_tokens) as total_cache_create,
    SUM(cache_read_tokens) as total_cache_read,
    SUM(web_search_requests) as total_searches,
    SUM(estimated_cost) as total_cost,
    AVG(estimated_cost) as avg_cost,
    MIN(timestamp) as first_query,
    MAX(timestamp) as last_query
  FROM api_usage
")->fetch(PDO::FETCH_ASSOC);

// Daily breakdown (last 30 days)
$daily = $db->query("
  SELECT
    DATE(timestamp) as date,
    COUNT(*) as queries,
    SUM(estimated_cost) as cost,
    SUM(output_tokens) as output_tokens,
    SUM(web_search_requests) as searches
  FROM api_usage
  WHERE timestamp >= DATE('now', '-30 days')
  GROUP BY DATE(timestamp)
  ORDER BY date DESC
")->fetchAll(PDO::FETCH_ASSOC);

// By expertise level
$byExpertise = $db->query("
  SELECT
    expertise,
    COUNT(*) as queries,
    SUM(estimated_cost) as cost,
    AVG(output_tokens) as avg_output
  FROM api_usage
  GROUP BY expertise
  ORDER BY queries DESC
")->fetchAll(PDO::FETCH_ASSOC);

// Recent queries (last 20)
$recent = $db->query("
  SELECT
    timestamp,
    expertise,
    input_tokens,
    output_tokens,
    cache_read_tokens,
    web_search_requests,
    estimated_cost,
    SUBSTR(category, 1, 50) as category_short
  FROM api_usage
  ORDER BY timestamp DESC
  LIMIT 20
")->fetchAll(PDO::FETCH_ASSOC);

// Monthly totals
$monthly = $db->query("
  SELECT
    STRFTIME('%Y-%m', timestamp) as month,
    COUNT(*) as queries,
    SUM(estimated_cost) as cost
  FROM api_usage
  GROUP BY STRFTIME('%Y-%m', timestamp)
  ORDER BY month DESC
  LIMIT 12
")->fetchAll(PDO::FETCH_ASSOC);

?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Claude API Usage Stats</title>
  <style>
    :root {
      --bg: #0a0f1a;
      --panel: #0f1726;
      --ink: #e6eefc;
      --muted: #8a9bb8;
      --brand: #7aa7ff;
      --green: #10b981;
      --yellow: #fbbf24;
      --red: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: var(--bg);
      color: var(--ink);
      padding: 20px;
      line-height: 1.5;
    }
    h1 { color: var(--brand); margin-bottom: 8px; }
    h2 { color: var(--brand); font-size: 1.1rem; margin: 24px 0 12px; border-bottom: 1px solid rgba(122,167,255,.2); padding-bottom: 8px; }
    .subtitle { color: var(--muted); margin-bottom: 24px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }
    .card {
      background: var(--panel);
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 12px;
      padding: 16px;
    }
    .card-label { font-size: 0.8rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .card-value { font-size: 1.8rem; font-weight: 700; color: var(--ink); margin-top: 4px; }
    .card-value.cost { color: var(--green); }
    .card-value.warning { color: var(--yellow); }
    table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
    th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,.08); }
    th { color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }
    tr:hover { background: rgba(122,167,255,.05); }
    .num { text-align: right; font-family: 'SF Mono', Monaco, monospace; }
    .cost { color: var(--green); }
    .muted { color: var(--muted); }
    .refresh { position: fixed; top: 20px; right: 20px; background: var(--brand); color: #000; padding: 8px 16px; border-radius: 8px; text-decoration: none; font-weight: 600; }
    .refresh:hover { opacity: 0.9; }
  </style>
</head>
<body>
  <a href="?" class="refresh">Refresh</a>

  <h1>Claude API Usage</h1>
  <p class="subtitle">Quarex cost monitoring dashboard</p>

  <div class="grid">
    <div class="card">
      <div class="card-label">Total Queries</div>
      <div class="card-value"><?= number_format($summary['total_queries']) ?></div>
    </div>
    <div class="card">
      <div class="card-label">Total Cost</div>
      <div class="card-value cost">$<?= number_format($summary['total_cost'], 2) ?></div>
    </div>
    <div class="card">
      <div class="card-label">Avg Cost/Query</div>
      <div class="card-value">$<?= number_format($summary['avg_cost'], 4) ?></div>
    </div>
    <div class="card">
      <div class="card-label">Web Searches</div>
      <div class="card-value"><?= number_format($summary['total_searches']) ?></div>
    </div>
    <div class="card">
      <div class="card-label">Output Tokens</div>
      <div class="card-value"><?= number_format($summary['total_output']) ?></div>
    </div>
    <div class="card">
      <div class="card-label">Cache Reads</div>
      <div class="card-value"><?= number_format($summary['total_cache_read']) ?></div>
    </div>
  </div>

  <h2>Monthly Totals</h2>
  <table>
    <tr>
      <th>Month</th>
      <th class="num">Queries</th>
      <th class="num">Cost</th>
      <th class="num">Projected (30 days)</th>
    </tr>
    <?php foreach ($monthly as $m): ?>
    <tr>
      <td><?= htmlspecialchars($m['month']) ?></td>
      <td class="num"><?= number_format($m['queries']) ?></td>
      <td class="num cost">$<?= number_format($m['cost'], 2) ?></td>
      <td class="num muted">
        <?php
          // Calculate projected monthly if current month
          if ($m['month'] === date('Y-m')) {
            $dayOfMonth = date('j');
            $daysInMonth = date('t');
            $projected = ($m['cost'] / $dayOfMonth) * $daysInMonth;
            echo '$' . number_format($projected, 2);
          } else {
            echo '-';
          }
        ?>
      </td>
    </tr>
    <?php endforeach; ?>
  </table>

  <h2>Daily Breakdown (Last 30 Days)</h2>
  <table>
    <tr>
      <th>Date</th>
      <th class="num">Queries</th>
      <th class="num">Cost</th>
      <th class="num">Output Tokens</th>
      <th class="num">Searches</th>
    </tr>
    <?php foreach ($daily as $d): ?>
    <tr>
      <td><?= htmlspecialchars($d['date']) ?></td>
      <td class="num"><?= number_format($d['queries']) ?></td>
      <td class="num cost">$<?= number_format($d['cost'], 4) ?></td>
      <td class="num"><?= number_format($d['output_tokens']) ?></td>
      <td class="num"><?= number_format($d['searches']) ?></td>
    </tr>
    <?php endforeach; ?>
    <?php if (empty($daily)): ?>
    <tr><td colspan="5" class="muted">No data yet</td></tr>
    <?php endif; ?>
  </table>

  <h2>By Expertise Level</h2>
  <table>
    <tr>
      <th>Level</th>
      <th class="num">Queries</th>
      <th class="num">Total Cost</th>
      <th class="num">Avg Output Tokens</th>
    </tr>
    <?php foreach ($byExpertise as $e): ?>
    <tr>
      <td><?= htmlspecialchars($e['expertise'] ?: 'unknown') ?></td>
      <td class="num"><?= number_format($e['queries']) ?></td>
      <td class="num cost">$<?= number_format($e['cost'], 4) ?></td>
      <td class="num"><?= number_format($e['avg_output']) ?></td>
    </tr>
    <?php endforeach; ?>
  </table>

  <h2>Recent Queries</h2>
  <table>
    <tr>
      <th>Time</th>
      <th>Expertise</th>
      <th class="num">In</th>
      <th class="num">Out</th>
      <th class="num">Cache</th>
      <th class="num">Search</th>
      <th class="num">Cost</th>
    </tr>
    <?php foreach ($recent as $r): ?>
    <tr>
      <td class="muted"><?= htmlspecialchars($r['timestamp']) ?></td>
      <td><?= htmlspecialchars($r['expertise']) ?></td>
      <td class="num"><?= number_format($r['input_tokens']) ?></td>
      <td class="num"><?= number_format($r['output_tokens']) ?></td>
      <td class="num"><?= number_format($r['cache_read_tokens']) ?></td>
      <td class="num"><?= $r['web_search_requests'] ?></td>
      <td class="num cost">$<?= number_format($r['estimated_cost'], 4) ?></td>
    </tr>
    <?php endforeach; ?>
  </table>

  <p style="margin-top: 40px; color: var(--muted); font-size: 0.85rem;">
    First query: <?= htmlspecialchars($summary['first_query'] ?? 'N/A') ?> |
    Last query: <?= htmlspecialchars($summary['last_query'] ?? 'N/A') ?>
  </p>
</body>
</html>
