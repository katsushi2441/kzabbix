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
        ?><!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Kurage Zabbix</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:linear-gradient(135deg,#f8faf7,#eaf6f5);font-family:-apple-system,BlinkMacSystemFont,"Yu Gothic",sans-serif;color:#16343d}.box{width:min(440px,calc(100% - 40px));background:#fff;border:1px solid #d8e7e4;border-radius:18px;padding:34px;box-shadow:0 18px 50px rgba(22,66,72,.1);text-align:center}.mark{width:52px;height:52px;margin:auto;border-radius:15px;background:linear-gradient(145deg,#008da3,#153f55);display:grid;place-items:center;color:#fff;font-weight:900}.box h1{font-size:23px;margin:18px 0 8px}.box p{color:#60777d;line-height:1.8;font-size:14px}.box a{display:inline-block;margin-top:14px;padding:11px 22px;border-radius:10px;background:#153f55;color:#fff;text-decoration:none;font-weight:800}</style></head><body><main class="box"><div class="mark">KZ</div><h1>Kurage Zabbix</h1><p>障害調査レポートは管理者専用です。<br>Xの <strong>@xb_bittensor</strong> でログインしてください。</p><a href="<?= $login ?>">Xでログイン</a></main></body></html><?php
        exit;
    }
}

require __DIR__ . '/bludit.php';

