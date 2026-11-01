<?php
function debug_log(string $text): void
{
    $file = '/home/webpages/lima-city/paule32/logs/github-irc.log';

    file_put_contents(
        $file,
        date('Y-m-d H:i:s') . ' ' . $text . PHP_EOL,
        FILE_APPEND | LOCK_EX
    );
}

error_reporting(E_ALL);
ini_set('display_errors', '1');

debug_log('Webhook gestartet');

$errno  = 0;
$errstr = '';

$fp = stream_socket_client(
    'tls://irc.libera.chat:6697',
    $errno,
    $errstr,
    10
);

if (!$fp) {
    echo "VERBINDUNG FEHLGESCHLAGEN<br>";
    echo "errno = " . htmlspecialchars((string)$errno) . "<br>";
    echo "error = " . htmlspecialchars($errstr);
    exit;
}

echo "VERBINDUNG ZU LIBERA.CHAT ERFOLGREICH";

fclose($fp);
