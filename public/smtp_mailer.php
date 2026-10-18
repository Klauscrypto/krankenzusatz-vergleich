<?php
/**
 * Minimaler SMTP-Client (STARTTLS + AUTH LOGIN), ohne externe Abhängigkeiten.
 * Übernommen aus lkw-ladepartner.de / pilsner-digital.de. Nur für den internen Gebrauch durch lead.php gedacht.
 */

if (basename($_SERVER['SCRIPT_FILENAME'] ?? '') === basename(__FILE__)) {
    http_response_code(403);
    exit;
}

class SmtpMailer
{
    private string $host;
    private int $port;
    private string $user;
    private string $pass;

    public function __construct(string $host, int $port, string $user, string $pass)
    {
        $this->host = $host;
        $this->port = $port;
        $this->user = $user;
        $this->pass = $pass;
    }

    /** @throws RuntimeException */
    public function send(string $from, string $fromName, string $to, string $replyTo, string $subject, string $body): void
    {
        $socket = @stream_socket_client(
            "tcp://{$this->host}:{$this->port}",
            $errno,
            $errstr,
            10
        );
        if (!$socket) {
            throw new RuntimeException("Verbindung fehlgeschlagen: {$errstr}");
        }

        try {
            $this->expect($socket, 220);
            $this->command($socket, "EHLO krankenzusatz-vergleich.de", 250);
            $this->command($socket, "STARTTLS", 220);

            if (!stream_socket_enable_crypto($socket, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
                throw new RuntimeException("TLS-Handshake fehlgeschlagen");
            }

            $this->command($socket, "EHLO krankenzusatz-vergleich.de", 250);
            $this->command($socket, "AUTH LOGIN", 334);
            $this->command($socket, base64_encode($this->user), 334);
            $this->command($socket, base64_encode($this->pass), 235);

            $this->command($socket, "MAIL FROM:<{$from}>", 250);
            $this->command($socket, "RCPT TO:<{$to}>", 250);
            $this->command($socket, "DATA", 354);

            $headers  = "From: =?UTF-8?B?" . base64_encode($fromName) . "?= <{$from}>\r\n";
            $headers .= "To: <{$to}>\r\n";
            $headers .= "Reply-To: {$replyTo}\r\n";
            $headers .= "Subject: =?UTF-8?B?" . base64_encode($subject) . "?=\r\n";
            $headers .= "Date: " . date(DATE_RFC2822) . "\r\n";
            $headers .= "Message-ID: <" . bin2hex(random_bytes(12)) . "@krankenzusatz-vergleich.de>\r\n";
            $headers .= "MIME-Version: 1.0\r\n";
            $headers .= "Content-Type: text/plain; charset=utf-8\r\n";
            $headers .= "Content-Transfer-Encoding: 8bit\r\n";
            $headers .= "X-Mailer: krankenzusatz-lead-form\r\n";

            // Zeilen, die mit "." beginnen, escapen (SMTP-DATA-Terminator)
            $escapedBody = preg_replace('/^\./m', '..', $body);

            $this->command($socket, $headers . "\r\n" . $escapedBody . "\r\n.", 250);
            $this->command($socket, "QUIT", 221);
        } finally {
            fclose($socket);
        }
    }

    /** @param resource $socket */
    private function command($socket, string $line, int $expectedCode): void
    {
        fwrite($socket, $line . "\r\n");
        $this->expect($socket, $expectedCode);
    }

    /** @param resource $socket */
    private function expect($socket, int $expectedCode): void
    {
        $response = '';
        while (($line = fgets($socket, 512)) !== false) {
            $response .= $line;
            // Letzte Zeile einer Multiline-Antwort hat ein Leerzeichen statt "-" nach dem Code
            if (preg_match('/^\d{3} /', $line)) {
                break;
            }
        }
        $code = (int) substr($response, 0, 3);
        if ($code !== $expectedCode) {
            throw new RuntimeException("Unerwartete SMTP-Antwort (erwartet {$expectedCode}): {$response}");
        }
    }
}
