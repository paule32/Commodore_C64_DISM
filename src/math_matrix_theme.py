# -*- coding: utf-8 -*-
"""Stage 424: gemeinsame Farbschemata für die zwei Matrix-Lernansichten.

Diese Datei ist bewusst unabhängig von PyQt5; so lassen sich die Paletten
auch auf Systemen ohne Qt gegenprüfen. Die Widgets besitzen je eine eigene
Palette und wechseln damit beim globalen Theme-Umschalten vollständig um.
"""

ROTATION_DARK = {
    'canvas': '#101827',
    'paper_top': '#19283e',
    'paper_mid': '#152237',
    'paper_bottom': '#202d40',
    'title': '#e5f0ff',
    'heading': '#f7c58b',
    'formula': '#e6efff',
    'bracket': '#b8cbe7',
    'cube': '#c4ad72',
    'axis': '#87b8ff',
    'curve': '#e9effb',
    'cube_z': '#4cb3ef',
    'cube_x': '#f26b77',
    'cube_y': '#e3d46d',
}

ROTATION_LIGHT = {
    'canvas': '#eee9dd',
    'paper_top': '#fff8de',
    'paper_mid': '#fff8e1',
    'paper_bottom': '#f1f3e9',
    'title': '#0b315d',
    'heading': '#8c4a15',
    'formula': '#102c50',
    'bracket': '#122e51',
    'cube': '#bba166',
    'axis': '#153b7f',
    'curve': '#102132',
    'cube_z': '#146fbb',
    'cube_x': '#ce2933',
    'cube_y': '#b0a621',
}

MULTIPLICATION_DARK = {
    'canvas': '#0f1724',
    'page': '#101826',
    'panel': '#212836',
    'panel_border': '#5d708b',
    'title': '#f8fbff',
    'formula': '#f1f5fb',
    'text': '#f2f6fb',
    'bracket': '#e4e8ef',
    'token_normal': '#f6f7fb',
    'token_blue': '#76a8ff',
    'token_red': '#ff7c86',
    'row': (210, 74, 66, 60),
    'col': (67, 115, 244, 65),
    'cell': (232, 184, 92, 65),
    'result': (244, 214, 138, 55),
    'strip': (244, 207, 151, 40),
}

MULTIPLICATION_LIGHT = {
    'canvas': '#ebe5d7',
    'page': '#fbf7de',
    'panel': '#fffbeb',
    'panel_border': '#c9ba91',
    'title': '#25364d',
    'formula': '#27374d',
    'text': '#25364d',
    'bracket': '#34435a',
    'token_normal': '#283344',
    'token_blue': '#214da8',
    'token_red': '#b8232e',
    'row': (226, 88, 81, 67),
    'col': (72, 111, 224, 67),
    'cell': (222, 163, 72, 75),
    'result': (225, 180, 94, 55),
    'strip': (229, 165, 88, 60),
}


def rotation_palette(dark_mode: bool) -> dict:
    """Eigenständige Palette pro Widget/Theme statt globalem Farbzustand."""
    return dict(ROTATION_DARK if dark_mode else ROTATION_LIGHT)


def multiplication_palette(dark_mode: bool) -> dict:
    return dict(MULTIPLICATION_DARK if dark_mode else MULTIPLICATION_LIGHT)
