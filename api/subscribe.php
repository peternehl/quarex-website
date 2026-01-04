<?php
header('Content-Type: text/html; charset=utf-8');

$email = filter_var($_POST['email'] ?? '', FILTER_VALIDATE_EMAIL);

if (!$email) {
    header('Location: /?error=invalid_email');
    exit;
}

$to = 'peter.nehl@gmail.com';
$subject = 'New Quarex Newsletter Subscription';
$message = "New subscriber:\n\nEmail: $email\nDate: " . date('Y-m-d H:i:s') . "\nIP: " . ($_SERVER['REMOTE_ADDR'] ?? 'unknown');
$headers = "From: noreply@quarex.org\r\n";
$headers .= "Reply-To: $email\r\n";

if (mail($to, $subject, $message, $headers)) {
    header('Location: /?subscribed=1');
} else {
    header('Location: /?error=send_failed');
}
exit;
