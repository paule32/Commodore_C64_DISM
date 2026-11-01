<?php

declare(strict_types=1);

const WEBHOOK_SECRET = 'db74302cd31287b746b557b5257e7b977b7cf24b22485bfc43b85d05f71df33c';

$token = $_SERVER['HTTP_X_WEBHOOK_TOKEN'] ?? '';

if (!hash_equals(WEBHOOK_SECRET, $token)) {
    http_response_code(403);
    exit('Forbidden');
}

$raw = file_get_contents('php://input');

if ($raw === false) {
    http_response_code(400);
    exit('No input');
}

$data = json_decode($raw, true);

if (!is_array($data)) {
    http_response_code(400);
    exit('Invalid JSON');
}

$repository = trim((string)($data['repository'] ?? 'unknown'));
$branch     = trim((string)($data['branch'] ?? 'unknown'));
$actor      = trim((string)($data['actor'] ?? 'unknown'));
$commit     = trim((string)($data['commit'] ?? ''));
$message    = trim((string)($data['message'] ?? ''));
$url        = trim((string)($data['url'] ?? ''));

$shortCommit = substr($commit, 0, 8);

/*
 * IRC erlaubt keine beliebigen CR/LF-Zeichen in einer Nachricht.
 */
$message = str_replace(
    ["\r", "\n", "\0"],
    [' ', ' ', ''],
    $message
);

$ircMessage =
    "[GitHub] {$repository} / {$branch} - " .
    "{$actor} pushed {$shortCommit}: {$message} {$url}";

sendToIRC($ircMessage);

http_response_code(200);
echo "OK";


function sendToIRC(string $message): void
{
    $server  = 'irc.libera.chat';
    $port    = 6697;
    $nick    = 'dBaseBot';
    $user    = 'dBaseBot';
    $channel = '#DBase';

    $context = stream_context_create([
        'ssl' => [
            'verify_peer'       => true,
            'verify_peer_name'  => true,
            'SNI_enabled'       => true,
            'peer_name'         => $server,
        ]
    ]);

    $socket = stream_socket_client(
        "tls://{$server}:{$port}",
        $errno,
        $errstr,
        10,
        STREAM_CLIENT_CONNECT,
        $context
    );

    if (!$socket) {
        throw new RuntimeException(
            "IRC connection failed: {$errno} {$errstr}"
        );
    }

    stream_set_timeout($socket, 10);

    ircWrite($socket, "NICK {$nick}");
    ircWrite($socket, "USER {$user} 0 * :GitHub notification bot");

    $registered = false;

    while (!feof($socket)) {
        $line = fgets($socket);

        if ($line === false) {
            break;
        }

        if (str_starts_with($line, 'PING ')) {
            ircWrite(
                $socket,
                'PONG ' . substr($line, 5)
            );

            continue;
        }

        /*
         * 001 = RPL_WELCOME
         */
        if (preg_match('/^:[^ ]+ 001 /', $line)) {
            $registered = true;
            break;
        }
    }

    if (!$registered) {
        fclose($socket);
        throw new RuntimeException(
            'IRC registration failed'
        );
    }

    ircWrite($socket, "JOIN {$channel}");

    /*
     * Kurze Pause, bis JOIN verarbeitet wurde.
     */
    usleep(500000);

    ircWrite(
        $socket,
        "PRIVMSG {$channel} :" . sanitizeIrc($message)
    );

    ircWrite($socket, 'QUIT :GitHub notification sent');

    fclose($socket);
}


function ircWrite($socket, string $line): void
{
    fwrite($socket, $line . "\r\n");
}


function sanitizeIrc(string $text): string
{
    $text = str_replace(
        ["\r", "\n", "\0"],
        [' ', ' ', ''],
        $text
    );

    /*
     * IRC-Zeilen sollten kurz bleiben.
     */
    return mb_substr($text, 0, 400);
}
