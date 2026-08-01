<?php
declare(strict_types=1);
header('X-Robots-Tag: noindex, nofollow', true);
header('Cache-Control: private, no-store, max-age=0', true);

$root = dirname(__DIR__);
$gateConfig = __DIR__ . '/bl-content/kzabbix_gate.php';
$apiAllowed = false;
if (is_file($gateConfig)) {
    $gate = require $gateConfig;
    $provided = isset($_SERVER['HTTP_X_KZABBIX_GATE_TOKEN']) ? (string)$_SERVER['HTTP_X_KZABBIX_GATE_TOKEN'] : '';
    $expected = is_array($gate) && isset($gate['token']) ? (string)$gate['token'] : '';
    $apiAllowed = $expected !== '' && hash_equals($expected, $provided);
}

if (!$apiAllowed) {
    $sharedConfig = $root . '/config.php';
    $sharedAuth = $root . '/auth_common.php';
    if (!is_file($sharedConfig) || !is_file($sharedAuth)) {
        http_response_code(503);
        exit('Shared X authentication is not available.');
    }
    require_once $sharedConfig;
    require_once $sharedAuth;
    $auth = url2ai_auth_bootstrap();
    if (empty($auth['is_admin']) || ($auth['session_user'] ?? '') !== 'xb_bittensor') {
        $login = htmlspecialchars(url2ai_auth_login_url('/zabbix/'), ENT_QUOTES, 'UTF-8');
        ?><!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Kurage Zabbix</title><style>:root{--ink:#163b50;--muted:#66808d;--line:#cfe8ec;--aqua:#18b7cf;--deep:#0799b4}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:linear-gradient(160deg,#fbffff 0,#eaf9fc 58%,#edfaf6 100%);font-family:-apple-system,BlinkMacSystemFont,"Yu Gothic",sans-serif;color:var(--ink)}header{height:72px;padding:0 max(20px,calc((100% - 1060px)/2));background:rgba(255,255,255,.9);border-bottom:1px solid #dceff1;display:flex;align-items:center}.brand{display:flex;align-items:center;gap:11px}.mark{width:39px;height:39px;border-radius:13px;background:linear-gradient(145deg,#2bc8d7,var(--deep));display:grid;place-items:center;color:#fff;font-size:12px;font-weight:900}.brand strong,.brand small{display:block}.brand strong{font-size:15px}.brand small{margin-top:2px;color:var(--muted);font-size:9px}main{min-height:calc(100vh - 72px);display:grid;place-items:center;padding:40px 20px}.box{width:min(900px,100%);display:grid;grid-template-columns:1.2fr .8fr;background:#fff;border:1px solid var(--line);border-radius:25px;box-shadow:0 22px 60px rgba(34,116,132,.12);overflow:hidden}.copy{padding:55px}.eyebrow{display:inline-block;padding:7px 10px;border:1px solid #bde8ed;border-radius:999px;color:#078fa8;font-size:9px;font-weight:900;letter-spacing:.08em}.copy h1{margin:20px 0 13px;font-size:36px;line-height:1.35;letter-spacing:-.03em}.copy h1 em{display:block;color:var(--deep);font-style:normal}.copy p{margin:0;color:var(--muted);line-height:1.9;font-size:13px}.copy a{display:inline-block;margin-top:24px;padding:13px 22px;border-radius:999px;background:linear-gradient(135deg,var(--aqua),var(--deep));box-shadow:0 10px 22px rgba(13,166,188,.2);color:#fff;text-decoration:none;font-size:12px;font-weight:900}.copy small{display:block;margin-top:15px;color:#8aa0a7;font-size:9px}.agent{padding:34px;background:linear-gradient(150deg,#eefbfc,#e8f8f4);display:grid;place-items:center;text-align:center}.agent img{width:190px;height:190px;object-fit:contain}.agent strong{display:block;font-size:14px}.agent p{max-width:260px;margin:8px auto 0;color:var(--muted);font-size:10px;line-height:1.75}.live{display:inline-block;margin-top:13px;padding:6px 9px;border-radius:999px;background:#fff;color:#168b69;font-size:8px;font-weight:900}@media(max-width:700px){header{height:64px;padding:0 15px}.brand small{display:none}main{padding:20px 13px}.box{grid-template-columns:1fr}.copy{padding:34px 25px}.copy h1{font-size:27px}.agent{padding:20px}.agent img{width:120px;height:120px}}</style></head><body><header><div class="brand"><div class="mark">KZ</div><span><strong>Kurage Zabbix</strong><small>障害調査・通知レポート</small></span></div></header><main><section class="box"><div class="copy"><span class="eyebrow">● PRIVATE INCIDENT INTELLIGENCE</span><h1>Kurageさんが障害を見つけ、<em>調べて、レポートします。</em></h1><p>Zabbixが検知した障害をGemma4が調査し、管理者専用の障害調査レポートとして記録します。</p><a href="<?= $login ?>">Xでログインしてレポートを見る</a><small>閲覧できるのは X の @xb_bittensor のみです。</small></div><aside class="agent"><div><img src="https://kurage.exbridge.jp/blog/bl-themes/kurage/img/kurage_avatar_face.webp" alt="Kurageさん" width="190" height="190"><strong>Kurageさんが監視中</strong><p>障害検知・証拠収集・AI解析・メール通知・レポート発行を自動で進めます。</p><span class="live">● 24 / 7 MONITORING</span></div></aside></section></main></body></html><?php
        exit;
    }
}

require __DIR__ . '/bludit.php';
