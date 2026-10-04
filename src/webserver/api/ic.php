<?php
declare(strict_types=1);

/*
 * IC SVG API
 *
 * Beispiele:
 *   api/ic.php?action=list
 *   api/ic.php?id=74ls00
 *   api/ic.php?id=74ls00&rotation=90
 */

$dataFile = realpath(__DIR__ . '/../data/ic.json');
if ($dataFile === false || !is_file($dataFile)) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'IC-Datenbank nicht gefunden.']);
    exit;
}

$db = json_decode((string)file_get_contents($dataFile), true);
if (!is_array($db) || !isset($db['components']) || !is_array($db['components'])) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'Ungültige IC-Datenbank.']);
    exit;
}

$components = $db['components'];

function findComponent(array $components, string $requestedId): ?array {
    $id = strtolower(trim($requestedId));

    if (isset($components[$id])) {
        return ['id' => $id, 'component' => $components[$id]];
    }

    foreach ($components as $canonicalId => $component) {
        $aliases = $component['aliases'] ?? [];
        foreach ($aliases as $alias) {
            if (strtolower((string)$alias) === $id) {
                return ['id' => $canonicalId, 'component' => $component];
            }
        }
    }

    return null;
}

$action = strtolower((string)($_GET['action'] ?? ''));

if ($action === 'list') {
    $result = [];

    foreach ($components as $id => $component) {
        $result[] = [
            'id' => $id,
            'name' => (string)($component['name'] ?? $id),
            'description' => (string)($component['description'] ?? ''),
            'rotations' => array_map('strval', array_keys($component['rotations'] ?? ['0' => '']))
        ];
    }

    header('Content-Type: application/json; charset=utf-8');
    header('Cache-Control: no-cache');
    echo json_encode(['components' => $result], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
    exit;
}

$id = (string)($_GET['id'] ?? '74ls00');
$rotation = (string)($_GET['rotation'] ?? $_GET['rot'] ?? '0');

if (!in_array($rotation, ['0', '90', '180', '270'], true)) {
    http_response_code(400);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'Ungültige Rotation. Erlaubt: 0, 90, 180, 270.']);
    exit;
}

$found = findComponent($components, $id);
if ($found === null) {
    http_response_code(404);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'Unbekannte IC-ID.', 'id' => $id]);
    exit;
}

$component = $found['component'];
$rotations = $component['rotations'] ?? [];

if (!isset($rotations[$rotation])) {
    http_response_code(404);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['error' => 'Rotation für diese Komponente nicht vorhanden.']);
    exit;
}

$vectorRoot = realpath(__DIR__ . '/../vectors');
if ($vectorRoot === false) {
    http_response_code(500);
    exit('Vector-Verzeichnis fehlt.');
}

$relative = basename((string)$rotations[$rotation]);
$svgFile = realpath($vectorRoot . DIRECTORY_SEPARATOR . $relative);

if ($svgFile === false || !is_file($svgFile) || strncmp($svgFile, $vectorRoot, strlen($vectorRoot)) !== 0) {
    http_response_code(404);
    exit('SVG-Datei nicht gefunden.');
}

$mtime = filemtime($svgFile) ?: time();
$etag = '"' . sha1($svgFile . '|' . $mtime . '|' . filesize($svgFile)) . '"';

header('Content-Type: image/svg+xml; charset=utf-8');
header('Cache-Control: public, max-age=3600');
header('ETag: ' . $etag);

if (isset($_SERVER['HTTP_IF_NONE_MATCH']) && trim((string)$_SERVER['HTTP_IF_NONE_MATCH']) === $etag) {
    http_response_code(304);
    exit;
}

readfile($svgFile);
