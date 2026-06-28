<?php
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

$vorname   = htmlspecialchars(trim($data['vorname']   ?? ''));
$nachname  = htmlspecialchars(trim($data['nachname']  ?? ''));
$email     = filter_var(trim($data['email'] ?? ''), FILTER_SANITIZE_EMAIL);
$telefon   = htmlspecialchars(trim($data['telefon']   ?? ''));
$alter     = intval($data['alter'] ?? 0);
$interesse = htmlspecialchars(trim($data['interesse'] ?? ''));

if (!$vorname || !$nachname || !filter_var($email, FILTER_VALIDATE_EMAIL) || $alter < 18) {
    http_response_code(422);
    echo json_encode(['error' => 'Pflichtfelder fehlen']);
    exit;
}

$to      = 'finanzierung@bloemecke-partner.de';
$subject = "Neue Beratungsanfrage: $interesse";

$body  = "Neue Anfrage über krankenzusatz-vergleich.de\n";
$body .= "=========================================\n\n";
$body .= "Name:      $vorname $nachname\n";
$body .= "Alter:     $alter\n";
$body .= "E-Mail:    $email\n";
$body .= "Telefon:   $telefon\n";
$body .= "Interesse: $interesse\n";
$body .= "\nEingegangen: " . date('d.m.Y H:i') . " Uhr\n";

$headers  = "From: noreply@krankenzusatz-vergleich.de\r\n";
$headers .= "Reply-To: $email\r\n";
$headers .= "X-Mailer: PHP/" . phpversion() . "\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";

$sent = mail($to, $subject, $body, $headers);

if ($sent) {
    echo json_encode(['success' => true]);
} else {
    http_response_code(500);
    echo json_encode(['error' => 'Mail konnte nicht gesendet werden']);
}
