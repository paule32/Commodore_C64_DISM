# -*- coding: utf-8 -*-
"""Agent 0003: konturbasierte 2D-Geometrie mit OpenCV und NumPy.

Die Erkennung folgt dem im Benutzerarchiv Bild_Recognition-main demonstrierten
Ansatz (findContours, approxPolyDP, Seitenverhaeltnis), ohne imutils oder
Globalausgabe. Sie ist heuristisch und keine semantische Objekterkennung.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import math

import cv2
import numpy as np


@dataclass(frozen=True)
class Figure:
    kind: str
    color: str
    x: int
    y: int
    width: int
    height: int
    points: tuple[tuple[int, int], ...]
    area: float

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)

    @property
    def label(self) -> str:
        names = {
            'kreis': 'Kreis', 'dreieck': 'Dreieck',
            'rechteck': 'Rechteck', 'quadrat': 'Quadrat',
            'polygon': 'Polygon',
        }
        return names.get(self.kind, self.kind.title())


def load_image(path: str | Path) -> np.ndarray:
    """Unicode-Pfade unter Windows korrekt lesen; Ergebnis im OpenCV-BGR-Format."""
    raw = np.fromfile(str(path), dtype=np.uint8)
    if raw.size == 0:
        raise ValueError('Die Bilddatei ist leer.')
    image = cv2.imdecode(raw, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError('Kein unterstütztes Bildformat oder defektes Bild.')
    if max(image.shape[:2]) > 12000 or image.shape[0] * image.shape[1] > 50_000_000:
        raise ValueError('Bild zu groß (maximal 50 Megapixel, Kante maximal 12000).')
    return image


def _figure_color(hsv_image: np.ndarray, filled_contour: np.ndarray) -> str:
    mask = np.zeros(hsv_image.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [filled_contour], -1, 255, cv2.FILLED)
    pixels = hsv_image[mask != 0]
    if len(pixels) == 0:
        return 'unbekannt'
    saturated = pixels[(pixels[:, 1] > 50) & (pixels[:, 2] > 50)]
    if len(saturated) < max(5, len(pixels) // 7):
        avg_v = float(np.median(pixels[:, 2]))
        return 'weiß' if avg_v > 185 else 'schwarz' if avg_v < 70 else 'grau'
    hue = float(np.median(saturated[:, 0]))
    if hue <= 9 or hue >= 171: return 'rot'
    if hue <= 21: return 'orange'
    if hue <= 39: return 'gelb'
    if hue <= 88: return 'grün'
    if hue <= 134: return 'blau'
    if hue <= 169: return 'violett'
    return 'rot'


def _classify_contour(cnt: np.ndarray) -> str:
    # Konvexe Huellen verhindern, dass Hintergrundrauschen die Ecken zaehlt
    # oder die Kreisfoermigkeit kastenartig abgeflachter Konturen zerstoert.
    contour = cv2.convexHull(cnt)
    perimeter = cv2.arcLength(contour, True)
    if perimeter < 15:
        return 'polygon'
    vertices = cv2.approxPolyDP(contour, 0.025 * perimeter, True)
    length = len(vertices)
    if length == 3:
        return 'dreieck'
    if length == 4:
        # near-rectangles only: other quadrilaterals belong to polygons
        pts = vertices.reshape(-1, 2).astype(np.float64)
        vec = np.roll(pts, -1, axis=0) - pts
        norms = np.linalg.norm(vec, axis=1)
        if np.min(norms) > 0:
            cosines = [abs(float(np.dot(vec[i-1], vec[i]) / (norms[i-1] * norms[i])))
                       for i in range(4)]
            if max(cosines) <= 0.25:
                side_ratio = float(max(norms) / min(norms))
                return 'quadrat' if side_ratio < 1.12 else 'rechteck'
        return 'polygon'
    area = cv2.contourArea(contour)
    circularity = (4.0 * math.pi * area / (perimeter * perimeter)) if perimeter else 0
    if length >= 7 and circularity >= 0.77:
        return 'kreis'
    return 'polygon'


def detect_figures(image_bgr: np.ndarray, *, min_area: int = 75) -> list[Figure]:
    """Sucht getrennte, gefüllte Geometriefiguren in Fotos oder Zeichnungen.

    Farbsättigung trennt bunte Formen, für monochrome Bilder wird Otsu
    benutzt. Kleine Pixelartefakte und der äußere Bildrahmen werden verworfen.
    Bei komplexen Fotos sind Fehlklassifikationen zu erwarten.
    """
    if image_bgr is None or image_bgr.ndim != 3 or image_bgr.shape[2] != 3:
        raise ValueError('Es wird ein dreikanaliges BGR-Bild erwartet.')
    h, w = image_bgr.shape[:2]
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)
    saturated = cv2.inRange(hsv, np.array([0, 55, 45], np.uint8),
                           np.array([179, 255, 255], np.uint8))
    kernel = np.ones((3, 3), np.uint8)
    colored_ratio = float(cv2.countNonZero(saturated)) / (h*w)
    # Bei einfachen Diagrammen (flächiger Hintergrund) anhand der
    # Hintergrundfarbe segmentieren. Dadurch werden auch schwarze Figuren
    # neben bunten und weiße Figuren auf schwarzem Grund erkannt.
    patch_size = max(2, min(12, h // 20, w // 20))
    corners = np.concatenate([
        image_bgr[:patch_size, :patch_size].reshape(-1, 3),
        image_bgr[:patch_size, -patch_size:].reshape(-1, 3),
        image_bgr[-patch_size:, :patch_size].reshape(-1, 3),
        image_bgr[-patch_size:, -patch_size:].reshape(-1, 3),
    ]).astype(np.int16)
    background = np.median(corners, axis=0)
    noise = float(np.percentile(np.max(np.abs(corners - background), axis=1), 70))
    if noise < 12:
        delta = np.max(np.abs(image_bgr.astype(np.int16) - background), axis=2)
        binary = np.where(delta > max(28, noise * 4), 255, 0).astype(np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    elif colored_ratio > 0.005:
        binary = cv2.morphologyEx(saturated, cv2.MORPH_CLOSE, kernel)
    else:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        _threshold, binary = cv2.threshold(gray, 0, 255,
                                            cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    found = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = found[0] if len(found) == 2 else found[1]
    result: list[Figure] = []
    min_object_area = max(int(min_area), int(w*h*0.00008))
    for cnt in contours:
        area = float(cv2.contourArea(cnt))
        if area < min_object_area or area > w*h*0.87:
            continue
        x, y, cw, ch = map(int, cv2.boundingRect(cnt))
        if cw < 7 or ch < 7:
            continue
        if (x <= 1 and y <= 1 and cw >= w-2 and ch >= h-2):
            continue
        kind = _classify_contour(cnt)
        color = _figure_color(hsv, cnt)
        # Approximation fuer auswählbare Qt-Polygone, Originalkoordinaten.
        contour = cv2.approxPolyDP(cnt, max(1.0, 0.007*cv2.arcLength(cnt, True)), True)
        points = tuple((int(p[0][0]), int(p[0][1])) for p in contour)
        result.append(Figure(kind, color, x, y, cw, ch, points, area))
    return sorted(result, key=lambda f: (f.y, f.x))


def figure_position(figure: Figure, image_width: int, image_height: int) -> str:
    x, y = figure.center
    horizontal = 'links' if x < image_width / 3 else 'rechts' if x > image_width*2/3 else 'mittig'
    vertical = 'oben' if y < image_height/3 else 'unten' if y > image_height*2/3 else 'mittig'
    return 'in der Mitte' if horizontal == vertical == 'mittig' else f'{horizontal} / {vertical}'


def matches_filter(figure: Figure, selection: str) -> bool:
    term = (selection or '').casefold()
    if 'alle figuren' in term or 'alle formen' in term:
        return True
    if 'kreis' in term: return figure.kind == 'kreis'
    if 'dreieck' in term: return figure.kind == 'dreieck'
    if 'rechteck' in term: return figure.kind in ('rechteck','quadrat')
    if 'quadrat' in term: return figure.kind == 'quadrat'
    if 'polygon' in term: return figure.kind == 'polygon'
    return True


def figures_for_overlay(figures: list[Figure], selection: str,
                        selected_ids: set[int] | None = None) -> list[Figure]:
    """Konturen, die in der Szene beschriftet werden dürfen.

    selected_ids=None: normales ComboBox-Filtern. Eine leere Menge bedeutet
    dagegen eine aktive Bildfrage ohne Treffer: ausdrücklich NICHT alle.
    Satzfragen ignorieren den ComboBox-Filter, damit z. B. ein roter Kreis
    auch bei zuvor gewähltem Dreieck-Filter exklusiv angezeigt wird.
    """
    if selected_ids is not None:
        return [figure for figure in figures if id(figure) in selected_ids]
    return [figure for figure in figures if matches_filter(figure, selection)]
