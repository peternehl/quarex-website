<?php
// File: public_html/api/politician_enrich.php
header('Content-Type: application/json; charset=utf-8');

function jfail($msg){ http_response_code(200); echo json_encode(['ok'=>false,'error'=>$msg]); exit; }
function jok($payload){ echo json_encode($payload, JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE); exit; }

$name     = trim($_POST['name'] ?? $_GET['name'] ?? '');
$office   = trim($_POST['office'] ?? $_GET['office'] ?? '');
$state    = trim($_POST['state'] ?? $_GET['state'] ?? '');
$district = trim($_POST['district'] ?? $_GET['district'] ?? '');

if ($name === '') jfail('name required');

$cacheKey = '/tmp/ta_enrich_' . md5(strtolower("$name|$office|$state|$district")) . '.json';
if (file_exists($cacheKey) && (time() - filemtime($cacheKey) < 86400)) {
  $cached = file_get_contents($cacheKey);
  if ($cached) { echo $cached; exit; }
}

function curl_json($url){
  $ch = curl_init($url);
  curl_setopt_array($ch, [
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_USERAGENT => 'TruthAngel/1.0 (+contact@yourdomain)',
    CURLOPT_CONNECTTIMEOUT => 8,
    CURLOPT_TIMEOUT => 15
  ]);
  $res = curl_exec($ch);
  $code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
  curl_close($ch);
  if($code>=200 && $code<300 && $res) return json_decode($res,true);
  return null;
}

// --- Wikipedia + Wikidata helpers ---
function find_wiki_title($name, $state){
  $q = urlencode("$name $state");
  $r = curl_json("https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&utf8=1&srsearch=$q&srlimit=1");
  if($r && !empty($r['query']['search'][0]['title'])) return $r['query']['search'][0]['title'];
  $q = urlencode($name);
  $r = curl_json("https://en.wikipedia.org/w/api.php?action=query&list=search&format=json&utf8=1&srsearch=$q&srlimit=1");
  if($r && !empty($r['query']['search'][0]['title'])) return $r['query']['search'][0]['title'];
  return null;
}

function wiki_to_wikidata_qid($title){
  $t = urlencode($title);
  $r = curl_json("https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&format=json&utf8=1&titles=$t");
  if(!$r || empty($r['query']['pages'])) return null;
  foreach($r['query']['pages'] as $p){
    if(isset($p['pageprops']['wikibase_item'])) return $p['pageprops']['wikibase_item'];
  }
  return null;
}

function fetch_entity($qid){ return curl_json("https://www.wikidata.org/wiki/Special:EntityData/$qid.json"); }
function claim_val($entity, $pid){
  if(empty($entity['entities'])) return null;
  $E = reset($entity['entities']);
  $claims = $E['claims'] ?? [];
  if(empty($claims[$pid][0]['mainsnak'])) return null;
  $snak = $claims[$pid][0]['mainsnak'];
  $dt = $snak['datatype'] ?? '';
  $v = $snak['datavalue']['value'] ?? null;
  if(!$v) return null;
  if($dt==='time') return substr($v['time'],1,10);
  if($dt==='url' || $dt==='string' || $dt==='external-id') return $v;
  if($dt==='wikibase-item') return $v['id'] ?? null;
  if($dt==='monolingualtext') return $v['text'] ?? null;
  return null;
}
function label_of_q($qid){
  if(!$qid) return null;
  $r = curl_json("https://www.wikidata.org/wiki/Special:EntityData/$qid.json");
  return $r['entities'][$qid]['labels']['en']['value'] ?? $qid;
}
function compute_age($yyyy_mm_dd){
  if(!$yyyy_mm_dd) return null;
  $d = new DateTime($yyyy_mm_dd); $now = new DateTime('now');
  return $d->diff($now)->y;
}
function ballotpedia_url($name){ return "https://ballotpedia.org/" . str_replace(' ','_',$name); }

function next_federal_election($office, $state, $district){
  $now=new DateTime('now'); $year=(int)$now->format('Y'); $even=($year%2==0)?$year:$year+1;
  $d=new DateTime("$even-11-01");
  while($d->format('N')!=1) $d->modify('+1 day'); $d->modify('+1 day');
  $fmt=$d->format('F j, Y');
  $note='Computed as general federal election day.';
  if(preg_match('/House|Rep/i',$office)) $note='All U.S. House seats are up every even year.';
  elseif(preg_match('/Senate|Senator/i',$office)) $note='Senate terms are staggered; check Ballotpedia for the class.';
  return ['date'=>$fmt,'note'=>$note];
}

// ---- Main logic ----
$title = find_wiki_title($name,$state);
$qid   = $title ? wiki_to_wikidata_qid($title) : null;
$entity= $qid ? fetch_entity($qid) : null;

$birth = $entity ? claim_val($entity,'P569') : null;
$birthPlaceQ = $entity ? claim_val($entity,'P19') : null;
$birthPlace = $birthPlaceQ ? label_of_q($birthPlaceQ) : null;
$netWorth = $entity ? claim_val($entity,'P2218') : null;
$partyQ = $entity ? claim_val($entity,'P102') : null;
$partyLbl = $partyQ ? label_of_q($partyQ) : null;

// tenure
$tenureSince=null;
if($entity && !empty($entity['entities'])){
  $E=reset($entity['entities']); $claims=$E['claims']??[];
  if(!empty($claims['P39'])){
    foreach($claims['P39'] as $pos){
      $isCurrent=empty($pos['qualifiers']['P582']);
      if($isCurrent && !empty($pos['qualifiers']['P580'][0]['datavalue']['value']['time'])){
        $t=$pos['qualifiers']['P580'][0]['datavalue']['value']['time'];
        $tenureSince=substr($t,1,10); break;
      }
    }
  }
}
$tenureYears=$tenureSince ? (new DateTime($tenureSince))->diff(new DateTime('now'))->y : null;

$officialSite=$entity ? claim_val($entity,'P856') : null;
$twitter=$entity ? claim_val($entity,'P2002') : null;
$facebook=$entity ? claim_val($entity,'P2013') : null;
$instagram=$entity ? claim_val($entity,'P2003') : null;
$youtube=$entity ? claim_val($entity,'P2397') : null;
$tiktok=$entity ? claim_val($entity,'P7085') : null;

$socials=[
  'twitter'=>$twitter?('https://x.com/'.$twitter):null,
  'facebook'=>$facebook?('https://facebook.com/'.$facebook):null,
  'instagram'=>$instagram?('https://instagram.com/'.$instagram):null,
  'youtube'=>$youtube?('https://youtube.com/channel/'.$youtube):null,
  'tiktok'=>$tiktok?('https://www.tiktok.com/@'.$tiktok):null
];

$wikiUrl=$title?'https://en.wikipedia.org/wiki/'.rawurlencode(str_replace(' ','_',$title)):null;
$bpUrl=ballotpedia_url($name);
$e=next_federal_election($office,$state,$district);

$out=[
  'ok'=>true,
  'name'=>$name,
  'office'=>$office?:null,
  'party'=>$partyLbl?:null,
  'personal'=>[
    'birth_date'=>$birth,
    'birth_place'=>$birthPlace,
    'age'=>compute_age($birth),
    'net_worth'=>$netWorth
  ],
  'tenure'=>[
    'since'=>$tenureSince,
    'years'=>$tenureYears
  ],
  'election'=>$e,
  'links'=>[
    'wikipedia'=>$wikiUrl,
    'official'=>$officialSite,
    'ballotpedia'=>$bpUrl
  ],
  'socials'=>$socials
];
file_put_contents($cacheKey,json_encode($out,JSON_UNESCAPED_SLASHES|JSON_UNESCAPED_UNICODE));
jok($out);
