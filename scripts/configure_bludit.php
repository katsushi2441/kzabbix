<?php
declare(strict_types=1);
if ($argc < 6) { fwrite(STDERR, "usage: configure_bludit.php build api-token auth-token gate-token admin-password\n"); exit(2); }
$root = realpath($argv[1]);
if ($root === false) { exit(3); }
function readDb(string $path): array {
    $raw = file_get_contents($path);
    $json = preg_replace('/^<\?php[^\n]*\n?/', '', (string)$raw);
    return json_decode((string)$json, true) ?: [];
}
function writeDb(string $path, array $data): void {
    file_put_contents($path, "<?php defined('BLUDIT') or die('Bludit CMS.'); ?>\n" . json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), LOCK_EX);
}
$sitePath = $root . '/bl-content/databases/site.php';
$site = readDb($sitePath);
$site['title'] = 'Kurage Zabbix';
$site['slogan'] = 'AI障害調査レポート';
$site['description'] = 'ZabbixとGemma4による限定障害調査ブログ';
$site['language'] = 'ja_JP';
$site['locale'] = 'ja_JP';
$site['timezone'] = 'Asia/Tokyo';
$site['theme'] = 'kzabbix';
$site['itemsPerPage'] = 10;
$site['url'] = 'https://kurage.exbridge.jp/zabbix/';
$site['twitter'] = 'https://x.com/xb_bittensor';
writeDb($sitePath, $site);
$usersPath = $root . '/bl-content/databases/users.php';
$users = readDb($usersPath);
$salt = bin2hex(random_bytes(8));
$users['admin']['salt'] = $salt;
$users['admin']['password'] = sha1($argv[5] . $salt);
$users['admin']['tokenAuth'] = $argv[3];
$users['admin']['tokenAuthTTL'] = '2099-12-31 23:59';
$users['admin']['email'] = 'katsushi2441@gmail.com';
writeDb($usersPath, $users);
$apiDir = $root . '/bl-content/databases/plugins/api';
@mkdir($apiDir, 0755, true);
writeDb($apiDir . '/db.php', ['token' => $argv[2], 'numberOfItems' => 50, 'position' => 1]);
$gate = "<?php\nreturn ['token' => " . var_export($argv[4], true) . "];\n";
file_put_contents($root . '/bl-content/kzabbix_gate.php', $gate, LOCK_EX);
@mkdir($root . '/bl-themes/kzabbix', 0755, true);
