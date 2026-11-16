# -*- coding: utf-8 -*-
"""Stage 570: exakte, Qt-unabhängige Matrizenmultiplikation.

Die Rechenroutine bleibt unabhängig von der GUI und kann mit Python direkt
getestet werden. Leere Eingabefelder werden als Null interpretiert.
"""
from decimal import Decimal, InvalidOperation


def parse_matrix_value(text):
    """Numerischen Matrixeintrag lesen; '' entspricht 0 (auch Leerraum)."""
    source = str(text or '').strip().replace(',', '.')
    if not source:
        return Decimal(0)
    try:
        value = Decimal(source)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f'Ungültiger Matrixeintrag: {text!r}') from exc
    if not value.is_finite():
        raise ValueError(f'Ungültiger Matrixeintrag: {text!r}')
    return value


def format_matrix_value(value):
    value = parse_matrix_value(value)
    if value == 0:
        return '0'
    result = format(value, 'f')
    if '.' in result:
        result = result.rstrip('0').rstrip('.')
    return result


def multiply_matrices(left, right):
    """C[i,j] = Summe_k(A[i,k] * B[k,j]), Dimension m×n * n×p.

    Gibt eine Liste von Zeilen mit Decimal-Werten zurück und löst bei
    nicht-rechteckigen oder inkompatiblen Dimensionen ValueError aus.
    """
    if not left or not right or not left[0] or not right[0]:
        raise ValueError('Beide Matrizen müssen mindestens eine Zeile und Spalte besitzen.')
    n1 = len(left[0])
    n2 = len(right[0])
    if any(len(row) != n1 for row in left) or any(len(row) != n2 for row in right):
        raise ValueError('Matrizen müssen rechteckig sein.')
    if n1 != len(right):
        raise ValueError(
            f'Dimensionen passen nicht: n1={n1}, m2={len(right)}. '
            'Die Spaltenzahl der ersten Matrix muss der Zeilenzahl der zweiten entsprechen.'
        )
    a = [[parse_matrix_value(value) for value in row] for row in left]
    b = [[parse_matrix_value(value) for value in row] for row in right]
    return [
        [sum((a[i][k] * b[k][j] for k in range(n1)), Decimal(0))
         for j in range(n2)]
        for i in range(len(a))
    ]


def matrix_calculation_steps(left, right):
    """Beschriftete Terme pro Ergebniszeile (1-basierte Indexnotation)."""
    result = multiply_matrices(left, right)
    a = [[parse_matrix_value(v) for v in row] for row in left]
    b = [[parse_matrix_value(v) for v in row] for row in right]
    steps = []
    for i, row in enumerate(result):
        current = []
        for j, value in enumerate(row):
            terms = [
                f'({format_matrix_value(a[i][k])} × {format_matrix_value(b[k][j])})'
                for k in range(len(b))
            ]
            current.append(f'c{i+1},{j+1} = ' + ' + '.join(terms)
                           + f' = {format_matrix_value(value)}')
        steps.append(current)
    return steps
