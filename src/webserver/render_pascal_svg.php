<?php
declare(strict_types=1);

/*
 * Demo-Endpunkt für den CHM Viewer.
 * Erwartet POST application/json:
 * {
 *   "language": "pascal",
 *   "output": "svg",
 *   "source": "...",
 *   "options": {"operation":"render-svg"}
 * }
 *
 * Der CHM Viewer ruft diesen Endpunkt serverseitig über Python/urllib auf;
 * deshalb sind für diesen Weg keine CORS-Header erforderlich.
 */

header('Content-Type: image/svg+xml; charset=UTF-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo errorSvg('Nur POST ist erlaubt.');
    exit;
}

$raw = file_get_contents('php://input');
if ($raw === false || strlen($raw) > 600000) {
    http_response_code(413);
    echo errorSvg('Anfrage ist zu groß.');
    exit;
}

$data = json_decode($raw, true);
if (!is_array($data)) {
    http_response_code(400);
    echo errorSvg('Ungültiges JSON.');
    exit;
}

$language = strtolower(trim((string)($data['language'] ?? '')));
$output   = strtolower(trim((string)($data['output'] ?? '')));
$source   = (string)($data['source'] ?? '');
$options  = is_array($data['options'] ?? null) ? $data['options'] : [];
$operation = (string)($options['operation'] ?? 'render-svg');

if ($language !== 'pascal' || $output !== 'svg') {
    http_response_code(400);
    echo errorSvg('Erwartet werden language=pascal und output=svg.');
    exit;
}

if ($source === '') {
    http_response_code(400);
    echo errorSvg('Kein Pascal-Quelltext übergeben.');
    exit;
}

/*
 * Hier kommt deine eigentliche Pascal-Verarbeitung hinein.
 * Du kannst z.B. Parser-/Compiler-Daten erzeugen und daraus ein Diagramm bauen.
 * Der Demo-Code liefert zunächst einige analysierte Werte als SVG zurück.
 */
$lines      = preg_split('/\R/u', $source) ?: [];
$lineCount  = count($lines);
$charCount  = function_exists('mb_strlen') ? mb_strlen($source, 'UTF-8') : strlen($source);
$procedures = preg_match_all('/\bprocedure\b/iu', $source, $dummy);
$functions  = preg_match_all('/\bfunction\b/iu', $source, $dummy2);
$classes    = preg_match_all('/\bclass\b/iu', $source, $dummy3);

$title = 'Pascal → SVG';
$items = [
    'Operation'  => $operation,
    'Zeilen'     => (string)$lineCount,
    'Zeichen'    => (string)$charCount,
    'Procedures' => (string)$procedures,
    'Functions'  => (string)$functions,
    'Classes'    => (string)$classes,
];

echo statsSvg($title, $items);

function xml(string $text): string
{
    return htmlspecialchars($text, ENT_QUOTES | ENT_XML1, 'UTF-8');
}

function errorSvg(string $message): string
{
    $msg = xml($message);
    return <<<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="760" height="100" viewBox="0 0 760 100">
  <rect x="0" y="0" width="760" height="100" rx="8" fill="#2b1111" stroke="#b84a4a"/>
  <text x="24" y="42" fill="#ffb3b3" font-family="Segoe UI,Arial,sans-serif" font-size="20">Serverfehler</text>
  <text x="24" y="72" fill="#ffffff" font-family="Consolas,monospace" font-size="14">{$msg}</text>
</svg>
SVG;
}

function statsSvg(string $title, array $items): string
{
    $width = 760;
    $rowHeight = 34;
    $top = 70;
    $height = $top + count($items) * $rowHeight + 24;
    $safeTitle = xml($title);

    $rows = '';
    $y = $top;
    foreach ($items as $name => $value) {
        $safeName = xml((string)$name);
        $safeValue = xml((string)$value);
        $rows .= '<text x="28" y="' . $y . '" fill="#9ecbff" font-family="Segoe UI,Arial,sans-serif" font-size="15">' . $safeName . '</text>';
        $rows .= '<text x="220" y="' . $y . '" fill="#ffffff" font-family="Consolas,monospace" font-size="15">' . $safeValue . '</text>';
        $y += $rowHeight;
    }

    return '<svg xmlns="http://www.w3.org/2000/svg" width="' . $width . '" height="' . $height . '" viewBox="0 0 ' . $width . ' ' . $height . '">' .
           '<rect x="0" y="0" width="' . $width . '" height="' . $height . '" rx="10" fill="#15171a" stroke="#4a4f57"/>' .
           '<text x="28" y="38" fill="#ffffff" font-family="Segoe UI,Arial,sans-serif" font-size="24" font-weight="600">' . $safeTitle . '</text>' .
           $rows .
           '</svg>';
}
