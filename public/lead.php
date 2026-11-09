<?php
// Lead-Formular: Versand per SMTP über das All-Inkl-Postfach (PHP mail() ist auf dem Server nicht für
// diese Domain eingerichtet). Zugangsdaten außerhalb des Webroots: /etc/krankenzusatz-vergleich/smtp.env
// (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM, optional LEAD_TO für Tests).
//
// Felder (JSON): vorname*, nachname*, email*, telefon, alter (optional, 18–99), interesse, nachricht,
// source (Herkunftsseite), einwilligung* ("ja", Art. 9 Abs. 2 lit. a DSGVO), website (Honeypot, muss leer
// sein), fs (Sekunden zwischen Seitenaufruf und Absenden, gesetzt per JS).
// Es wird nichts gespeichert außer einem gehashten IP-Zähler für das Rate-Limit (max. 1 Stunde).
require __DIR__ . '/smtp_mailer.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://krankenzusatz-vergleich.de');
header('Access-Control-Allow-Methods: POST');

const RATE_LIMIT_MAX    = 5;     // Anfragen pro IP …
const RATE_LIMIT_WINDOW = 3600;  // … pro Stunde
const MIN_FILL_SECONDS  = 2;     // schneller füllt kein Mensch das Formular aus

function respond(int $code, array $payload): never
{
    http_response_code($code);
    echo json_encode($payload);
    exit;
}

/**
 * Einfaches Rate-Limit pro IP. Gespeichert wird nur ein Hash der IP mit den Zeitstempeln der letzten Stunde.
 * Gibt false zurück, wenn das Limit erreicht ist; sonst wird der Versuch gezählt.
 */
function rate_limit_ok(string $ip): bool
{
    $dir = sys_get_temp_dir() . '/kzv-lead-ratelimit';
    if (!is_dir($dir) && !@mkdir($dir, 0700, true) && !is_dir($dir)) {
        return true; // Ohne Verzeichnis lieber Leads annehmen als alle abweisen
    }
    $now  = time();
    $file = $dir . '/' . hash('sha256', 'kzv-lead|' . $ip) . '.json';
    $fh   = @fopen($file, 'c+');
    if (!$fh) {
        return true;
    }
    try {
        flock($fh, LOCK_EX);
        $hits = json_decode(stream_get_contents($fh) ?: '[]', true);
        $hits = array_values(array_filter(is_array($hits) ? $hits : [], fn($t) => is_int($t) && $t > $now - RATE_LIMIT_WINDOW));
        if (count($hits) >= RATE_LIMIT_MAX) {
            return false;
        }
        $hits[] = $now;
        ftruncate($fh, 0);
        rewind($fh);
        fwrite($fh, json_encode($hits));
        return true;
    } finally {
        flock($fh, LOCK_UN);
        fclose($fh);
        // Gelegentlich alte Zähler aufräumen
        if (random_int(1, 50) === 1) {
            foreach (glob($dir . '/*.json') ?: [] as $old) {
                if (@filemtime($old) < $now - RATE_LIMIT_WINDOW) {
                    @unlink($old);
                }
            }
        }
    }
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    respond(405, ['error' => 'Method not allowed']);
}

$raw = file_get_contents('php://input', false, null, 0, 20000);
$data = json_decode((string) $raw, true);

if (!is_array($data)) {
    respond(400, ['error' => 'Ungültige Anfrage']);
}

// Einzeilige Werte: Zeilenumbrüche entfernen (Header-Injection verhindern, Werte landen teils im Betreff),
// Steuerzeichen entfernen und Länge begrenzen
$line = fn($v, int $max = 100) => mb_substr(
    trim(preg_replace('/[\x00-\x1F\x7F]+/u', ' ', (string) (is_scalar($v) ? $v : '')) ?? ''),
    0,
    $max
);
// Mehrzeiliger Freitext: Zeilenumbrüche behalten, sonstige Steuerzeichen entfernen
$text = fn($v, int $max = 2000) => mb_substr(
    trim(preg_replace('/[\x00-\x09\x0B-\x1F\x7F]+/u', ' ', str_replace(["\r\n", "\r"], "\n", (string) (is_scalar($v) ? $v : ''))) ?? ''),
    0,
    $max
);
$esc = fn(string $v) => htmlspecialchars($v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');

// Spam-Schutz 1: Honeypot. Bots bekommen eine Erfolgsmeldung, damit sie nicht weiterprobieren.
if ($line($data['website'] ?? '') !== '') {
    respond(200, ['success' => true]);
}

// Spam-Schutz 2: Mindest-Ausfüllzeit
$fillSeconds = filter_var($data['fs'] ?? null, FILTER_VALIDATE_INT);
if ($fillSeconds === false || $fillSeconds < MIN_FILL_SECONDS) {
    respond(422, ['error' => 'Bitte prüfen Sie Ihre Angaben und senden Sie das Formular erneut.']);
}

$vorname   = $esc($line($data['vorname']  ?? ''));
$nachname  = $esc($line($data['nachname'] ?? ''));
$emailRaw  = $line($data['email'] ?? '', 254);
$email     = filter_var($emailRaw, FILTER_VALIDATE_EMAIL) ? $emailRaw : '';
$telefon   = $esc($line($data['telefon']   ?? '', 50));
$interesse = $esc($line($data['interesse'] ?? ''));
$source    = $esc($line($data['source']    ?? ''));
$nachricht = $esc($text($data['nachricht'] ?? ''));

// Alter ist optional; wenn angegeben, muss es eine ganze Zahl von 18 bis 99 sein
$alterRaw = $line($data['alter'] ?? '', 10);
$alter    = '';
if ($alterRaw !== '') {
    $alterInt = filter_var($alterRaw, FILTER_VALIDATE_INT, ['options' => ['min_range' => 18, 'max_range' => 99]]);
    if ($alterInt === false) {
        respond(422, ['error' => 'Bitte geben Sie ein Alter zwischen 18 und 99 an oder lassen Sie das Feld leer.']);
    }
    $alter = (string) $alterInt;
}

if ($vorname === '' || $nachname === '' || $email === '') {
    respond(422, ['error' => 'Pflichtfelder fehlen']);
}

// Ausdrückliche Einwilligung in die Verarbeitung von Gesundheitsdaten (Art. 9 Abs. 2 lit. a DSGVO)
if (($data['einwilligung'] ?? '') !== 'ja') {
    respond(422, ['error' => 'Bitte bestätigen Sie die Einwilligung zur Verarbeitung Ihrer Angaben.']);
}

// Spam-Schutz 3: Rate-Limit pro IP (erst nach der Prüfung, damit Tippfehler nicht mitzählen)
if (!rate_limit_ok($_SERVER['REMOTE_ADDR'] ?? '')) {
    respond(429, ['error' => 'Zu viele Anfragen. Bitte versuchen Sie es später erneut oder rufen Sie uns an.']);
}

$envPath = '/etc/krankenzusatz-vergleich/smtp.env';
$env = is_readable($envPath) ? parse_ini_file($envPath) : false;
if (!$env || empty($env['SMTP_PASS'])) {
    error_log('lead.php: smtp.env fehlt oder unvollständig');
    respond(500, ['error' => 'Die Anfrage konnte nicht gesendet werden.']);
}

$to      = !empty($env['LEAD_TO']) ? $env['LEAD_TO'] : 'a.bloemecke@bloemecke-partner.de';
$subject = 'Neue Beratungsanfrage: ' . ($interesse !== '' ? $interesse : 'ohne Auswahl')
         . ($source !== '' ? " ($source)" : '');

$body  = "Neue Anfrage über krankenzusatz-vergleich.de\n";
$body .= "=========================================\n\n";
$body .= "Name:      $vorname $nachname\n";
$body .= "Alter:     " . ($alter !== '' ? $alter : '(nicht angegeben)') . "\n";
$body .= "E-Mail:    $email\n";
$body .= "Telefon:   " . ($telefon !== '' ? $telefon : '(nicht angegeben)') . "\n";
$body .= "Interesse: " . ($interesse !== '' ? $interesse : '(nicht angegeben)') . "\n";
$body .= "Herkunft:  " . ($source !== '' ? $source : '(unbekannt)') . "\n";
$body .= "\nNachricht:\n" . ($nachricht !== '' ? $nachricht : '(keine)') . "\n";
$body .= "\nEinwilligung: Die ausdrückliche Einwilligung in die Verarbeitung der Angaben einschließlich\n";
$body .= "Gesundheitsangaben (Art. 9 Abs. 2 lit. a DSGVO) wurde im Formular per Checkbox erteilt.\n";
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
    respond(500, ['error' => 'Die Anfrage konnte nicht gesendet werden.']);
}
