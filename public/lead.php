<?php
// Lead-Formular: Versand per SMTP über das All-Inkl-Postfach (PHP mail() ist auf dem Server nicht für
// diese Domain eingerichtet). Zugangsdaten außerhalb des Webroots: /etc/krankenzusatz-vergleich/smtp.env
// (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, optional LEAD_TO für Tests).
require __DIR__ . '/smtp_mailer.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://krankenzusatz-vergleich.de');
header('Access-Control-Allow-Methods: POST');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

$raw = file_get_contents('php://input');
$data = json_decode($raw, true);

if (!$data) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON']);
    exit;
}

// Header-Injection verhindern (Werte landen teils im Betreff)
$line = fn($v) => str_replace(["\r", "\n"], ' ', trim((string) $v));

$vorname   = htmlspecialchars($line($data['vorname']   ?? ''));
$nachname  = htmlspecialchars($line($data['nachname']  ?? ''));
$email     = filter_var($line($data['email'] ?? ''), FILTER_SANITIZE_EMAIL);
$telefon   = htmlspecialchars($line($data['telefon']   ?? ''));
$alter     = intval($data['alter'] ?? 0);
$interesse = htmlspecialchars($line($data['interesse'] ?? ''));

if (!$vorname || !$nachname || !filter_var($email, FILTER_VALIDATE_EMAIL) || $alter < 18) {
    http_response_code(422);
    echo json_encode(['error' => 'Pflichtfelder fehlen']);
    exit;
}

$envPath = '/etc/krankenzusatz-vergleich/smtp.env';
$env = is_readable($envPath) ? parse_ini_file($envPath) : false;
if (!$env || empty($env['SMTP_PASS'])) {
    http_response_code(500);
    echo json_encode(['error' => 'Mail nicht konfiguriert']);
    exit;
}

$to      = !empty($env['LEAD_TO']) ? $env['LEAD_TO'] : 'a.bloemecke@bloemecke-partner.de';
$subject = "Neue Beratungsanfrage: $interesse";

$body  = "Neue Anfrage über krankenzusatz-vergleich.de\n";
$body .= "=========================================\n\n";
$body .= "Name:      $vorname $nachname\n";
$body .= "Alter:     $alter\n";
$body .= "E-Mail:    $email\n";
$body .= "Telefon:   $telefon\n";
$body .= "Interesse: $interesse\n";
$body .= "\nEingegangen: " . date('d.m.Y H:i') . " Uhr\n";

try {
    $mailer = new SmtpMailer($env['SMTP_HOST'], (int) ($env['SMTP_PORT'] ?? 587), $env['SMTP_USER'], $env['SMTP_PASS']);
    $mailer->send(
        from: $env['SMTP_FROM'],
        fromName: 'krankenzusatz-vergleich.de',
        to: $to,
        replyTo: $email,
        subject: $subject,
        body: $body
    );
    echo json_encode(['success' => true]);
} catch (Throwable $e) {
    error_log('lead.php SMTP-Fehler: ' . $e->getMessage());
    http_response_code(500);
    echo json_encode(['error' => 'Mail konnte nicht gesendet werden']);
}
