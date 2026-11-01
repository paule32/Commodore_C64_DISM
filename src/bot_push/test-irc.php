<?php

declare(strict_types=1);

error_reporting(E_ALL);
ini_set('display_errors', '1');

header('Content-Type: text/plain; charset=utf-8');

$server  = 'irc.libera.chat';
$port    = 6697;

/*
 * Registrierter Libera.Chat Bot-Account
 */
$nick     = 'dBaseBot';
$account  = 'dBaseBot';

/*
 * WICHTIG:
 * Hier kommt das ECHTE NickServ/SASL-Passwort hinein.
 * KEIN SHA256-Hash!
 */
$password = 'db74302cd31287b746b557b5257e7b977b7cf24b22485bfc43b85d05f71df33c';
$channel  = '#DBase';
$message  = '[C64 DISM] new push on: ' . date('Y-m-d H:i:s');


function out(string $text): void
{
    echo $text . "\n";

    if (function_exists('ob_flush')) {
        @ob_flush();
    }

    flush();
}


function ircSend($socket, string $command): void
{
    /*
     * Passwort niemals ins Debug-Log schreiben.
     */
    if (str_starts_with($command, 'AUTHENTICATE ')
        && $command !== 'AUTHENTICATE PLAIN') {
        out('>> AUTHENTICATE <ausgeblendet>');
    } else {
        out('>> ' . $command);
    }

    fwrite($socket, $command . "\r\n");
}


$context = stream_context_create([
    'ssl' => [
        'verify_peer'       => true,
        'verify_peer_name'  => true,
        'SNI_enabled'       => true,
        'peer_name'         => $server
    ]
]);


out("Verbinde mit {$server}:{$port} ...");

$socket = @stream_socket_client(
    "tls://{$server}:{$port}",
    $errno,
    $errstr,
    15,
    STREAM_CLIENT_CONNECT,
    $context
);

if (!$socket) {
    http_response_code(500);

    out("FEHLER: {$errno} {$errstr}");
    exit;
}

stream_set_timeout($socket, 15);

out('TLS-Verbindung hergestellt');


/*
 * IRC-Registrierung mit SASL beginnen
 */
ircSend($socket, 'CAP LS 302');
ircSend($socket, "NICK {$nick}");
ircSend($socket, "USER {$nick} 0 * :GitHub Notification Bot");


$saslStarted       = false;
$saslDataSent      = false;
$saslAuthenticated = false;
$registered        = false;
$joined            = false;
$messageSent       = false;


while (!feof($socket)) {

    $line = fgets($socket);

    if ($line === false) {
        break;
    }

    $line = rtrim($line, "\r\n");

    out('<< ' . $line);


    /*
     * IRC Keep-Alive
     */
    if (str_starts_with($line, 'PING ')) {
        ircSend(
            $socket,
            'PONG ' . substr($line, 5)
        );

        continue;
    }


    /*
     * Server unterstützt SASL
     */
    if (
        str_contains($line, ' CAP ')
        && str_contains($line, 'sasl')
        && !$saslStarted
    ) {
        ircSend($socket, 'CAP REQ :sasl');

        $saslStarted = true;

        continue;
    }


    /*
     * CAP ACK :sasl
     */
    if (
        str_contains($line, ' ACK ')
        && str_contains($line, 'sasl')
    ) {
        ircSend($socket, 'AUTHENTICATE PLAIN');

        continue;
    }


    /*
     * Server fordert SASL-Daten an
     */
    if (
        str_starts_with($line, 'AUTHENTICATE +')
        && !$saslDataSent
    ) {
        $authString =
            $account . "\0" .
            $account . "\0" .
            $password;

        $encoded = base64_encode($authString);

        ircSend(
            $socket,
            'AUTHENTICATE ' . $encoded
        );

        $saslDataSent = true;

        continue;
    }


    /*
     * 903 = SASL erfolgreich
     */
    if (preg_match('/^:[^ ]+ 903 /', $line)) {

        $saslAuthenticated = true;

        out('*** SASL ERFOLGREICH ***');

        ircSend($socket, 'CAP END');

        continue;
    }


    /*
     * SASL Fehler
     */
    if (
        preg_match(
            '/^:[^ ]+ (904|905|906|907) /',
            $line,
            $matches
        )
    ) {
        out(
            '*** SASL FEHLER ' .
            $matches[1] .
            ' ***'
        );

        ircSend($socket, 'CAP END');
        ircSend($socket, 'QUIT :SASL failed');

        fclose($socket);
        exit;
    }


    /*
     * 001 = Registrierung abgeschlossen
     */
    if (preg_match('/^:[^ ]+ 001 /', $line) && !$registered) {
        $registered = true;

        out('*** IRC REGISTRIERUNG ERFOLGREICH ***');

        ircSend(
            $socket,
            "JOIN {$channel}"
        );

        continue;
    }


    /*
     * Unser eigener JOIN ist angekommen
     */
    if (
        preg_match(
            '/^:' . preg_quote($nick, '/') .
            '![^ ]+ JOIN :?' .
            preg_quote($channel, '/') .
            '$/i',
            $line
        )
    ) {
        $joined = true;

        out('*** CHANNEL BETRETEN ***');

        ircSend(
            $socket,
            "PRIVMSG {$channel} :{$message}"
        );

        $messageSent = true;

        out('*** NACHRICHT GESENDET ***');

        /*
         * Kurz warten, damit der Server
         * PRIVMSG verarbeiten kann.
         */
        usleep(500000);

        ircSend(
            $socket,
            'QUIT :GitHub notification complete'
        );

        break;
    }


    /*
     * JOIN-Fehler
     */
    if (
        preg_match(
            '/^:[^ ]+ (471|473|474|475) /',
            $line,
            $matches
        )
    ) {
        out(
            '*** CHANNEL JOIN FEHLER ' .
            $matches[1] .
            ' ***'
        );

        break;
    }
}

fclose($socket);

out('');
out('--- Ergebnis ---');
out('SASL:   ' . ($saslAuthenticated ? 'OK' : 'FEHLER'));
out('IRC:    ' . ($registered ? 'OK' : 'FEHLER'));
out('JOIN:   ' . ($joined ? 'OK' : 'FEHLER'));
out('MESSAGE:' . ($messageSent ? ' OK' : ' FEHLER'));
