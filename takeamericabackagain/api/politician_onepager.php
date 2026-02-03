<?php
// File: public_html/api/politician_onepager.php
$name   = $_GET['name'] ?? '';
$office = $_GET['office'] ?? '';
$state  = $_GET['state'] ?? '';
$district = $_GET['district'] ?? '';
if(!$name){ http_response_code(400); echo "name required"; exit; }

function post($url,$data){
  $ch=curl_init($url);
  curl_setopt_array($ch,[
    CURLOPT_POST=>true,
    CURLOPT_POSTFIELDS=>http_build_query($data),
    CURLOPT_RETURNTRANSFER=>true,
    CURLOPT_TIMEOUT=>15
  ]);
  $res=curl_exec($ch);
  curl_close($ch);
  return $res;
}
$base=(isset($_SERVER['HTTPS'])?'https://':'http://').$_SERVER['HTTP_HOST'];
$json=post($base.'/api/politician_enrich.php',compact('name','office','state','district'));
$data=json_decode($json,true);

header('Content-Type:text/html; charset=utf-8');
?>
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title><?=htmlspecialchars($name)?> — One-Pager</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px;}
h1{margin:0 0 4px;}
.sub{color:#555;margin:0 0 18px;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;}
.card{border:1px solid #ddd;border-radius:10px;padding:12px;}
.kv{display:grid;grid-template-columns:150px 1fr;gap:6px 12px;}
.k{color:#666}
.v{font-weight:600}
@media print{.noprint{display:none}}
</style>
</head>
<body>
<div class="noprint" style="text-align:right">
  <button onclick="window.print()">Print</button>
</div>
<h1><?=htmlspecialchars($data['name']??$name)?></h1>
<p class="sub"><?=htmlspecialchars(($data['office']??$office).' • '.($data['party']??''))?></p>

<div class="grid">
  <div class="card">
    <h3>Personal</h3>
    <div class="kv">
      <div class="k">Age</div><div class="v"><?=htmlspecialchars($data['personal']['age']??'—')?></div>
      <div class="k">Birth date</div><div class="v"><?=htmlspecialchars($data['personal']['birth_date']??'—')?></div>
      <div class="k">Birth place</div><div class="v"><?=htmlspecialchars($data['personal']['birth_place']??'—')?></div>
      <div class="k">Net worth</div><div class="v"><?=htmlspecialchars($data['personal']['net_worth']??'—')?></div>
    </div>
  </div>

  <div class="card">
    <h3>Party & Tenure</h3>
    <div class="kv">
      <div class="k">Party</div><div class="v"><?=htmlspecialchars($data['party']??'—')?></div>
      <div class="k">In office since</div><div class="v"><?=htmlspecialchars($data['tenure']['since']??'—')?></div>
      <div class="k">Years</div><div class="v"><?=htmlspecialchars($data['tenure']['years']??'—')?></div>
    </div>
  </div>

  <div class="card">
    <h3>Upcoming election</h3>
    <div class="kv">
      <div class="k">Next election</div><div class="v"><?=htmlspecialchars($data['election']['date']??'—')?></div>
      <div class="k">Notes</div><div class="v"><?=htmlspecialchars($data['election']['note']??'—')?></div>
    </div>
  </div>

  <div class="card">
    <h3>Links</h3>
    <div class="kv">
      <div class="k">Wikipedia</div><div class="v"><?=!empty($data['links']['wikipedia'])?'<a href="'.htmlspecialchars($data['links']['wikipedia']).'">'.htmlspecialchars($data['links']['wikipedia']).'</a>':'—'?></div>
      <div class="k">Official site</div><div class="v"><?=!empty($data['links']['official'])?'<a href="'.htmlspecialchars($data['links']['official']).'">'.htmlspecialchars($data['links']['official']).'</a>':'—'?></div>
      <div class="k">Ballotpedia</div><div class="v"><?=!empty($data['links']['ballotpedia'])?'<a href="'.htmlspecialchars($data['links']['ballotpedia']).'">'.htmlspecialchars($data['links']['ballotpedia']).'</a>':'—'?></div>
      <div class="k">X</div><div class="v"><?=!empty($data['socials']['twitter'])?'<a href="'.htmlspecialchars($data['socials']['twitter']).'">'.htmlspecialchars($data['socials']['twitter']).'</a>':'—'?></div>
      <div class="k">Facebook</div><div class="v"><?=!empty($data['socials']['facebook'])?'<a href="'.htmlspecialchars($data['socials']['facebook']).'">'.htmlspecialchars($data['socials']['facebook']).'</a>':'—'?></div>
      <div class="k">Instagram</div><div class="v"><?=!empty($data['socials']['instagram'])?'<a href="'.htmlspecialchars($data['socials']['instagram']).'">'.htmlspecialchars($data['socials']['instagram']).'</a>':'—'?></div>
      <div class="k">YouTube</div><div class="v"><?=!empty($data['socials']['youtube'])?'<a href="'.htmlspecialchars($data['socials']['youtube']).'">'.htmlspecialchars($data['socials']['youtube']).'</a>':'—'?></div>
      <div class="k">TikTok</div><div class="v"><?=!empty($data['socials']['tiktok'])?'<a href="'.htmlspecialchars($data['socials']['tiktok']).'">'.htmlspecialchars($data['socials']['tiktok']).'</a>':'—'?></div>
    </div>
  </div>
</div>
</body>
</html>
