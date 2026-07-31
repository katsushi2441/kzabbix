<?php
declare(strict_types=1);
header('X-Robots-Tag: noindex, nofollow', true);
$root = dirname(__DIR__);
require_once $root . '/config.php';
require_once $root . '/auth_common.php';
$auth = url2ai_auth_bootstrap();
if (empty($auth['is_admin']) || ($auth['session_user'] ?? '') !== 'xb_bittensor') {
    http_response_code(403);
    exit('Forbidden');
}
require __DIR__ . '/bludit-install.php';

