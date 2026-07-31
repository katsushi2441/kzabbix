<?php
declare(strict_types=1);
header('Content-Type: application/json; charset=utf-8');
header('X-Robots-Tag: noindex, nofollow', true);
header('Cache-Control: no-store', true);
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'method not allowed']);
    exit;
}
$gatePath = __DIR__ . '/bl-content/kzabbix_gate.php';
$gate = is_file($gatePath) ? require $gatePath : [];
$expected = is_array($gate) && isset($gate['token']) ? (string)$gate['token'] : '';
$provided = isset($_SERVER['HTTP_X_KZABBIX_GATE_TOKEN']) ? (string)$_SERVER['HTTP_X_KZABBIX_GATE_TOKEN'] : '';
if ($expected === '' || !hash_equals($expected, $provided)) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'forbidden']);
    exit;
}
$raw = file_get_contents('php://input');
if ($raw === false || strlen($raw) > 200000) {
    http_response_code(413);
    echo json_encode(['ok' => false, 'error' => 'payload too large']);
    exit;
}
$payload = json_decode($raw, true);
$subject = trim((string)($payload['subject'] ?? 'Kurage Zabbix incident'));
$body = trim((string)($payload['body'] ?? ''));
if ($body === '') {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'body is required']);
    exit;
}
$subject = mb_substr(str_replace(["\r", "\n"], ' ', $subject), 0, 180);
$headers = [
    'From: Kurage Zabbix <no-reply@kurage.exbridge.jp>',
    'Content-Type: text/plain; charset=UTF-8',
    'Content-Transfer-Encoding: 8bit',
];
$sent = mail('katsushi2441@gmail.com', mb_encode_mimeheader($subject, 'UTF-8'), $body, implode("\r\n", $headers));
if (!$sent) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => 'mail transport rejected message']);
    exit;
}
echo json_encode(['ok' => true]);
