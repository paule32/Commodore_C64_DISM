# -*- coding: utf-8 -*-
"""Stage 386: Lehrmodell fuer einen Chemie-Baukasten (kein Labor-Simulator).

Die ersten 40 Elemente sind waehlbar. Das Modell bildet bewusst nur
hinterlegte einfache Verbindungen und beispielhafte Reaktionsgleichungen ab.
"""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ChemicalElement:
    number: int
    symbol: str
    name: str
    family: str


_ELEMENTS = (
    ('H', 'Wasserstoff', 'Nichtmetall'),
    ('He', 'Helium', 'Edelgas'),
    ('Li', 'Lithium', 'Alkalimetall'),
    ('Be', 'Beryllium', 'Erdalkalimetall'),
    ('B', 'Bor', 'Halbmetall'),
    ('C', 'Kohlenstoff', 'Nichtmetall'),
    ('N', 'Stickstoff', 'Nichtmetall'),
    ('O', 'Sauerstoff', 'Nichtmetall'),
    ('F', 'Fluor', 'Halogen'),
    ('Ne', 'Neon', 'Edelgas'),
    ('Na', 'Natrium', 'Alkalimetall'),
    ('Mg', 'Magnesium', 'Erdalkalimetall'),
    ('Al', 'Aluminium', 'Metall'),
    ('Si', 'Silicium', 'Halbmetall'),
    ('P', 'Phosphor', 'Nichtmetall'),
    ('S', 'Schwefel', 'Nichtmetall'),
    ('Cl', 'Chlor', 'Halogen'),
    ('Ar', 'Argon', 'Edelgas'),
    ('K', 'Kalium', 'Alkalimetall'),
    ('Ca', 'Calcium', 'Erdalkalimetall'),
    ('Sc', 'Scandium', 'Uebergangsmetall'),
    ('Ti', 'Titan', 'Uebergangsmetall'),
    ('V', 'Vanadium', 'Uebergangsmetall'),
    ('Cr', 'Chrom', 'Uebergangsmetall'),
    ('Mn', 'Mangan', 'Uebergangsmetall'),
    ('Fe', 'Eisen', 'Uebergangsmetall'),
    ('Co', 'Cobalt', 'Uebergangsmetall'),
    ('Ni', 'Nickel', 'Uebergangsmetall'),
    ('Cu', 'Kupfer', 'Uebergangsmetall'),
    ('Zn', 'Zink', 'Uebergangsmetall'),
    ('Ga', 'Gallium', 'Metall'),
    ('Ge', 'Germanium', 'Halbmetall'),
    ('As', 'Arsen', 'Halbmetall'),
    ('Se', 'Selen', 'Nichtmetall'),
    ('Br', 'Brom', 'Halogen'),
    ('Kr', 'Krypton', 'Edelgas'),
    ('Rb', 'Rubidium', 'Alkalimetall'),
    ('Sr', 'Strontium', 'Erdalkalimetall'),
    ('Y', 'Yttrium', 'Uebergangsmetall'),
    ('Zr', 'Zirconium', 'Uebergangsmetall'),
)
ELEMENTS = tuple(ChemicalElement(i, *entry) for i, entry in enumerate(_ELEMENTS, 1))
BY_SYMBOL = {element.symbol: element for element in ELEMENTS}


@dataclass(frozen=True)
class ChemicalReaction:
    symbols: frozenset
    formula: str
    name: str
    equation: str
    note: str


def _reaction(symbols, formula, name, equation, note='Schematische Beispielreaktion; keine Laboranleitung.'):
    return ChemicalReaction(frozenset(symbols), formula, name, equation, note)


# Formal ausgeglichene Beispiele, nicht in allen Faellen ohne besondere
# Bedingungen unmittelbar durch einfaches Zusammengeben herstellbar.
REACTIONS = (
    _reaction(('H', 'O'), 'H2O', 'Wasser', '2 H2 + O2 -> 2 H2O'),
    _reaction(('C', 'O'), 'CO2', 'Kohlenstoffdioxid', 'C + O2 -> CO2'),
    _reaction(('Na', 'Cl'), 'NaCl', 'Natriumchlorid (Kochsalz)', '2 Na + Cl2 -> 2 NaCl'),
    _reaction(('Mg', 'O'), 'MgO', 'Magnesiumoxid', '2 Mg + O2 -> 2 MgO'),
    _reaction(('Fe', 'S'), 'FeS', 'Eisen(II)-sulfid', 'Fe + S -> FeS'),
    _reaction(('N', 'H'), 'NH3', 'Ammoniak', 'N2 + 3 H2 -> 2 NH3', 'Technische Synthese benoetigt besondere Bedingungen.'),
    _reaction(('Ca', 'O'), 'CaO', 'Calciumoxid', '2 Ca + O2 -> 2 CaO'),
    _reaction(('K', 'Cl'), 'KCl', 'Kaliumchlorid', '2 K + Cl2 -> 2 KCl'),
    _reaction(('Al', 'O'), 'Al2O3', 'Aluminiumoxid', '4 Al + 3 O2 -> 2 Al2O3'),
    _reaction(('S', 'O'), 'SO2', 'Schwefeldioxid', 'S + O2 -> SO2'),
    _reaction(('Si', 'O'), 'SiO2', 'Siliciumdioxid', 'Si + O2 -> SiO2'),
    _reaction(('Li', 'O'), 'Li2O', 'Lithiumoxid', '4 Li + O2 -> 2 Li2O', 'Moegliches Produkt; die Produktverteilung ist bedingungsabhaengig.'),
    _reaction(('Be', 'O'), 'BeO', 'Berylliumoxid', '2 Be + O2 -> 2 BeO'),
    _reaction(('P', 'O'), 'P4O10', 'Phosphor(V)-oxid', 'P4 + 5 O2 -> P4O10'),
    _reaction(('H', 'F'), 'HF', 'Fluorwasserstoff', 'H2 + F2 -> 2 HF'),
    _reaction(('H', 'Cl'), 'HCl', 'Chlorwasserstoff', 'H2 + Cl2 -> 2 HCl'),
    _reaction(('H', 'Br'), 'HBr', 'Bromwasserstoff', 'H2 + Br2 -> 2 HBr'),
    _reaction(('Cu', 'O'), 'CuO', 'Kupfer(II)-oxid', '2 Cu + O2 -> 2 CuO'),
    _reaction(('Zn', 'O'), 'ZnO', 'Zinkoxid', '2 Zn + O2 -> 2 ZnO'),
    _reaction(('Fe', 'O'), 'Fe2O3', 'Eisen(III)-oxid', '4 Fe + 3 O2 -> 2 Fe2O3', 'Eine moegliche Oxidationsstufe von Eisen.'),
    _reaction(('Ca', 'Cl'), 'CaCl2', 'Calciumchlorid', 'Ca + Cl2 -> CaCl2'),
    _reaction(('Mg', 'Cl'), 'MgCl2', 'Magnesiumchlorid', 'Mg + Cl2 -> MgCl2'),
    _reaction(('Sr', 'O'), 'SrO', 'Strontiumoxid', '2 Sr + O2 -> 2 SrO'),
    _reaction(('Zn', 'S'), 'ZnS', 'Zinksulfid', 'Zn + S -> ZnS'),
)
BY_PAIR = {reaction.symbols: reaction for reaction in REACTIONS}
SUBSCRIPT = str.maketrans('0123456789', '₀₁₂₃₄₅₆₇₈₉')


def pretty_formula(formula):
    """Chemische Indizes als Unicode-Tiefstellungen anzeigen."""
    return str(formula).translate(SUBSCRIPT)


def pretty_equation(equation):
    """Nur Formelindizes tiefstellen, nicht stoechiometrische Faktoren."""
    return re.sub(r'[A-Z][a-z]?\d*', lambda m: pretty_formula(m.group(0)), equation).replace('->', '→')


def find_reaction(symbols):
    """Nur bekannte Paare mit zwei verschiedenen Elementen liefern."""
    selection = tuple(symbols)
    if len(selection) != 2 or len(set(selection)) != 2:
        return None
    if any(symbol not in BY_SYMBOL for symbol in selection):
        return None
    return BY_PAIR.get(frozenset(selection))


def atom_counts(formula):
    """Atome in einer einfachen Summenformel zaehlen (ohne Klammergruppen)."""
    matches = list(re.finditer(r'([A-Z][a-z]?)(\d*)', formula))
    if not matches or ''.join(m.group(0) for m in matches) != formula:
        raise ValueError('Ungueltige Summenformel: ' + formula)
    result = {}
    for match in matches:
        symbol = match.group(1)
        if symbol not in BY_SYMBOL:
            raise ValueError('Unbekanntes Element: ' + symbol)
        result[symbol] = result.get(symbol, 0) + int(match.group(2) or '1')
    return result


def _equation_side_counts(side):
    counts = {}
    for term in side.split(' + '):
        match = re.fullmatch(r'(?:(\d+) )?([A-Z][A-Za-z0-9]*)', term.strip())
        if match is None:
            raise ValueError('Ungueltiger Reaktionsterm: ' + term)
        factor = int(match.group(1) or 1)
        for symbol, amount in atom_counts(match.group(2)).items():
            counts[symbol] = counts.get(symbol, 0) + factor * amount
    return counts


def is_balanced(equation):
    left, right = equation.split(' -> ')
    return _equation_side_counts(left) == _equation_side_counts(right)
