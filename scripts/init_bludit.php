<?php
declare(strict_types=1);
if ($argc < 3) { exit(2); }
chdir($argv[1]);
$_SERVER['HTTP_HOST'] = 'kurage.exbridge.jp';
$_SERVER['HTTPS'] = 'on';
$_SERVER['DOCUMENT_ROOT'] = dirname($argv[1]);
$_SERVER['SCRIPT_NAME'] = '/zabbix/install.php';
$_SERVER['PHP_SELF'] = '/zabbix/install.php';
$_SERVER['REQUEST_URI'] = '/zabbix/install.php';
$_SERVER['REQUEST_METHOD'] = 'POST';
$_SERVER['HTTP_ACCEPT_LANGUAGE'] = 'ja-JP';
$_POST['password'] = $argv[2];
$_POST['timezone'] = 'Asia/Tokyo';
require $argv[1] . '/bludit-install.php';

