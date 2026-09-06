"""E-Baukasten fuer d64_dism, Stage ASM 83 (PyQt5).

Port- und knotenbasierter Schaltungseditor. Kreuzende Leitungen sind erst
durch einen gemeinsamen Knoten elektrisch verbunden. Start prueft die
Netztopologie; dieser Editor enthaelt noch keinen elektrischen Solver.
"""
from __future__ import annotations

from collections import defaultdict
import copy
import html
import json
import math
from pathlib import Path
import uuid

from PyQt5.QtCore import Qt, QPointF, QRectF, QSize, QMimeData, pyqtSignal
from PyQt5.QtGui import (
    QColor, QDrag, QFont, QIcon, QPainter, QPainterPath, QPainterPathStroker,
    QPalette, QPen, QPixmap, QPolygonF, QTransform,
)
from PyQt5.QtWidgets import (
    QAction, QActionGroup, QAbstractItemView, QDoubleSpinBox, QFileDialog,
    QFormLayout, QGraphicsItem, QGraphicsPathItem, QGraphicsScene,
    QGraphicsView, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QMessageBox, QPlainTextEdit, QScrollArea,
    QSizePolicy, QSpinBox, QSplitter, QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

MIME_COMPONENT = "application/x-d64-electronics-component"
CATEGORIES = ("Analog", "Digital", "Quelle", "Widerstand", "Diode", "Kondensator", "Display")


def spec(category, title, symbol, prefix, ports, details, value=0.0, unit="", color=""):
    return dict(category=category, title=title, symbol=symbol, prefix=prefix,
                ports=ports, details=details, value=value, unit=unit, color=color)


TWO = (("1", -40, 0), ("2", 40, 0))
POLAR = (("+", -40, 0), ("−", 40, 0))
CATALOG = {
    "npn": spec("Analog", "NPN-Transistor", "npn", "Q",
        (("B", -40, 0), ("C", 20, -40), ("E", 20, 40)), "B: Basis · C: Kollektor · E: Emitter."),
    "opamp": spec("Analog", "Operationsverstärker", "opamp", "U",
        (("+", -40, -20), ("−", -40, 20), ("OUT", 40, 0)), "Signalanschlüsse eines idealisierten Operationsverstärkers."),
    "and": spec("Digital", "UND-Gatter", "and", "U",
        (("A", -40, -20), ("B", -40, 20), ("Y", 40, 0)), "UND: Ausgang Y ist aktiv, wenn A und B aktiv sind."),
    "or": spec("Digital", "ODER-Gatter", "or", "U",
        (("A", -40, -20), ("B", -40, 20), ("Y", 40, 0)), "ODER: Ausgang Y ist aktiv, wenn mindestens ein Eingang aktiv ist."),
    "not": spec("Digital", "NICHT-Gatter", "not", "U", TWO, "Invertiert den logischen Eingang."),
    "switch": spec("Digital", "Schalter", "switch", "S", TWO, "Zweipoliger Schalter als Schaltungselement."),
    "battery": spec("Quelle", "Batterie", "battery", "B", POLAR, "Gleichspannungsquelle. Polarität an + und − beachten.", 9, "V"),
    "dc": spec("Quelle", "Gleichspannung", "dc", "V", POLAR, "Ideale Gleichspannungsquelle.", 5, "V"),
    "current": spec("Quelle", "Gleichstromquelle", "current", "I", POLAR, "Ideale Gleichstromquelle.", 0.02, "A"),
    "ground": spec("Quelle", "Masse / Bezugspotential", "ground", "GND", (("0", 0, -40),), "Bezugspotential der Schaltung."),
    "resistor": spec("Widerstand", "Widerstand", "resistor", "R", TWO, "Widerstandswert in Ohm. Im Datenbereich veränderbar.", 1000, "Ω"),
    "pot": spec("Widerstand", "Potentiometer", "pot", "P",
        (("1", -40, 0), ("2", 40, 0), ("W", 0, -40)), "W: Schleifer; 1 und 2: Widerstandsbahn.", 10000, "Ω"),
    "diode": spec("Diode", "Diode", "diode", "D", (("A", -40, 0), ("K", 40, 0)), "A: Anode · K: Kathode. Der Balken markiert die Kathode."),
    "led_red": spec("Diode", "LED rot", "led", "D", (("A", -40, 0), ("K", 40, 0)), "Rote Leuchtdiode; für einen realen Aufbau einen Vorwiderstand vorsehen.", 2, "V", "#ee5858"),
    "led_green": spec("Diode", "LED grün", "led", "D", (("A", -40, 0), ("K", 40, 0)), "Grüne Leuchtdiode mit Anode und Kathode.", 2.2, "V", "#54c77a"),
    "led_blue": spec("Diode", "LED blau", "led", "D", (("A", -40, 0), ("K", 40, 0)), "Blaue Leuchtdiode mit Anode und Kathode.", 3.2, "V", "#579aff"),
    "capacitor": spec("Kondensator", "Kondensator", "capacitor", "C", TWO, "Ungepolter Kondensator. Kapazität in µF.", 0.1, "µF"),
    "elco": spec("Kondensator", "Elektrolytkondensator", "elco", "C", POLAR, "Gepolter Kondensator. Pluspol beachten.", 100, "µF"),
    "lamp": spec("Display", "Signallampe", "lamp", "H", TWO, "Zweipolige Signallampe.", 6, "V"),
    "sevenseg": spec("Display", "7-Segment-Anzeige", "sevenseg", "DIS",
        tuple((c, -40, -30 + i * 10) for i, c in enumerate("abcdefg")) + (("COM", 40, 0),),
        "Einzelanschlüsse a bis g und gemeinsamer Anschluss COM."),
}


def uid():
    return uuid.uuid4().hex


def point(value):
    return QPointF(float(value[0]), float(value[1]))


def xy(value):
    return [float(value.x()), float(value.y())]


def distance(a, b):
    return math.hypot(a.x() - b.x(), a.y() - b.y())


def same(a, b):
    return distance(a, b) < 0.001


def project_segment(p, a, b):
    dx, dy = b.x() - a.x(), b.y() - a.y()
    square = dx * dx + dy * dy
    t = max(0.0, min(1.0, ((p.x()-a.x())*dx + (p.y()-a.y())*dy) / square)) if square else 0
    return QPointF(a.x()+t*dx, a.y()+t*dy)


def intersection(a, b, c, d):
    """Schnittpunkt orthogonaler Segmente, inklusive T-Abzweigungen."""
    ah, ch = abs(a.y()-b.y()) < .001, abs(c.y()-d.y()) < .001
    if ah == ch:
        return None
    h1, h2, v1, v2 = (a, b, c, d) if ah else (c, d, a, b)
    x, y = v1.x(), h1.y()
    if (min(h1.x(), h2.x())-.001 <= x <= max(h1.x(), h2.x())+.001 and
            min(v1.y(), v2.y())-.001 <= y <= max(v1.y(), v2.y())+.001):
        return QPointF(x, y)
    return None


class ComponentItem(QGraphicsItem):
    def __init__(self, kind, name, component_id=None):
        super().__init__()
        self.kind, self.name, self.uid = kind, name, component_id or uid()
        self.angle = 0.0
        self.value = float(CATALOG[kind]["value"])
        self.setFlags(self.ItemIsMovable | self.ItemIsSelectable | self.ItemSendsGeometryChanges)
        self.setZValue(10)
        self.setToolTip(CATALOG[kind]["title"] + "\n" + CATALOG[kind]["details"])

    def boundingRect(self):
        k = self.scale_factor()
        if self.vertical_label():
            return QRectF(-68*k, -68*k, 121*k+90, 136*k)
        return QRectF(-68*k, -68*k, 136*k, 136*k+30)

    def vertical_label(self):
        return abs(math.sin(math.radians(self.angle))) > .707

    def scale_factor(self):
        return self.scene().grid / 10.0 if self.scene() else 1.0

    def shape(self):
        path = QPainterPath()
        k = self.scale_factor()
        path.addRect(QRectF(-34*k, -34*k, 68*k, 68*k))
        for i in range(len(CATALOG[self.kind]["ports"])):
            path.addEllipse(self.port_local(i), 7, 7)
        return path

    def raw_port(self, index):
        _, x, y = CATALOG[self.kind]["ports"][index]
        k = self.scale_factor()
        return QTransform().rotate(self.angle).map(QPointF(x*k, y*k))

    def port_local(self, index):
        scene = self.scene()
        if scene is None:
            return self.raw_port(index)
        # Auch bei freien Winkeln (insbesondere 260 Grad) keine zwei Pins
        # auf denselben Rasterpunkt legen. Anschlussfahnen zeigen den Versatz.
        used = set()
        for i in range(index+1):
            raw = self.raw_port(i)
            candidate = scene.snap(raw)
            if tuple(xy(candidate)) in used:
                options = [candidate+QPointF(dx*scene.grid,dy*scene.grid)
                           for dx in (-1,0,1) for dy in (-1,0,1)]
                candidate = min((p for p in options if tuple(xy(p)) not in used),
                                key=lambda p: distance(p, raw))
            used.add(tuple(xy(candidate)))
        return candidate

    def port_position(self, index):
        return self.mapToScene(self.port_local(index))

    def rotate_by(self, angle):
        self.prepareGeometryChange()
        self.angle = (self.angle + angle) % 360
        self.update()
        if self.scene():
            self.scene().refresh_wires()
            self.scene().modified.emit()

    def itemChange(self, change, value):
        scene = self.scene()
        if change == self.ItemPositionChange and scene:
            return scene.snap(value)
        if change == self.ItemPositionHasChanged and scene:
            scene.refresh_wires()
            scene.modified.emit()
        return super().itemChange(change, value)

    def paint(self, painter, option, widget=None):
        scene = self.scene()
        ink = QColor(scene.ink if scene else "#20343c")
        k = self.scale_factor()
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isSelected():
            painter.setBrush(QColor(53, 141, 198, 35))
            painter.setPen(QPen(QColor("#55b8e8"), 1, Qt.DashLine))
            painter.drawRoundedRect(QRectF(-56*k, -56*k, 112*k, 116*k), 5, 5)
        painter.setPen(QPen(ink, 2))
        painter.setBrush(Qt.NoBrush)
        for i in range(len(CATALOG[self.kind]["ports"])):
            painter.drawLine(self.raw_port(i), self.port_local(i))
        painter.save()
        painter.rotate(self.angle)
        painter.scale(k, k)
        self.draw_symbol(painter, ink)
        painter.restore()
        painter.setFont(QFont("Sans Serif", 8))
        for i, (label, _, _) in enumerate(CATALOG[self.kind]["ports"]):
            pos = self.port_local(i)
            painter.setPen(QPen(QColor(scene.wire_color if scene else "#28784c"), 1.5))
            painter.setBrush(QColor(scene.background if scene else "white"))
            painter.drawEllipse(pos, 3, 3)
            painter.setPen(ink)
            painter.drawText(pos + QPointF(5, -5), label)
        painter.setPen(ink)
        label_rect = QRectF(53*k,-15,90,15) if self.vertical_label() else QRectF(-67*k,53*k,134*k,15)
        alignment = Qt.AlignLeft if self.vertical_label() else Qt.AlignCenter
        painter.drawText(label_rect, alignment, self.name)
        unit = CATALOG[self.kind]["unit"]
        if unit:
            painter.drawText(label_rect.translated(0,15), alignment, f"{self.value:g} {unit}")

    def draw_symbol(self, p, ink):
        symbol = CATALOG[self.kind]["symbol"]
        line = lambda x1, y1, x2, y2: p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
        if symbol == "ground":
            line(0, -40, 0, 0)
            for y, width in ((0, 22), (8, 14), (16, 6)):
                line(-width, y, width, y)
            return
        if symbol in {"and", "or", "opamp"}:
            line(-40, -20, -22, -20); line(-40, 20, -22, 20); line(22, 0, 40, 0)
            if symbol == "opamp":
                p.drawPolygon(QPolygonF([QPointF(-22, -30), QPointF(22, 0), QPointF(-22, 30)]))
            else:
                p.drawRect(QRectF(-22, -30, 44, 60))
                p.drawText(QRectF(-20, -20, 40, 40), Qt.AlignCenter, "&" if symbol == "and" else "≥1")
            return
        if symbol == "npn":
            line(-40, 0, -8, 0); line(-8, -20, -8, 20)
            line(-8, -10, 20, -25); line(20, -25, 20, -40)
            line(-8, 10, 20, 25); line(20, 25, 20, 40)
            line(20, 25, 8, 23); line(20, 25, 14, 14)
            return
        if symbol == "sevenseg":
            p.drawRect(QRectF(-23, -38, 46, 76))
            for i in range(7):
                line(-40, -30+i*10, -23, -30+i*10)
            line(23, 0, 40, 0)
            p.setPen(QPen(QColor("#df6262"), 3))
            for a,b,c,d in ((-10,-23,10,-23),(-10,0,10,0),(-10,23,10,23),
                            (-12,-21,-12,-2),(12,-21,12,-2),(-12,2,-12,21),(12,2,12,21)):
                line(a,b,c,d)
            return
        line(-40, 0, -22, 0); line(22, 0, 40, 0)
        if symbol in {"resistor", "pot"}:
            p.drawRect(QRectF(-22, -9, 44, 18))
            if symbol == "pot":
                line(0,-40,0,-10); line(0,-10,-5,-18); line(0,-10,5,-18)
        elif symbol in {"diode", "led"}:
            p.setBrush(QColor(CATALOG[self.kind]["color"]) if symbol == "led" else Qt.NoBrush)
            p.drawPolygon(QPolygonF([QPointF(-22,-13),QPointF(-22,13),QPointF(18,0)]))
            line(18,-15,18,15); line(18,0,22,0)
            if symbol == "led":
                for x in (-6, 8):
                    line(x,-18,x+10,-28); line(x+10,-28,x+5,-27); line(x+10,-28,x+9,-23)
        elif symbol in {"capacitor", "elco"}:
            line(-22,0,-5,0); line(5,0,22,0); line(-5,-18,-5,18); line(5,-18,5,18)
            if symbol == "elco":
                p.drawText(QPointF(-20,-19), "+")
        elif symbol == "battery":
            line(-22,0,-5,0); line(6,0,22,0); line(-5,-22,-5,22); line(6,-12,6,12)
        elif symbol in {"dc", "current", "lamp"}:
            p.drawEllipse(QRectF(-22,-22,44,44))
            if symbol == "dc":
                p.drawText(QRectF(-20,-16,40,32), Qt.AlignCenter, "+ −")
            elif symbol == "current":
                line(-12,0,12,0); line(12,0,5,-6); line(12,0,5,6)
            else:
                line(-15,-15,15,15); line(-15,15,15,-15)
        elif symbol == "switch":
            line(-22,0,18,-17)
            p.drawEllipse(QPointF(-22,0), 3,3); p.drawEllipse(QPointF(22,0),3,3)
        elif symbol == "not":
            p.drawPolygon(QPolygonF([QPointF(-22,-20),QPointF(-22,20),QPointF(15,0)]))
            p.drawEllipse(QPointF(19,0),4,4)


class WireItem(QGraphicsPathItem):
    def __init__(self, anchors, wire_id=None):
        super().__init__()
        self.uid = wire_id or uid()
        self.anchors = copy.deepcopy(anchors)
        self.segments = []
        self.setFlag(self.ItemIsSelectable)
        self.setZValue(0)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(self.path())

    def update_path(self):
        scene = self.scene()
        if not scene:
            return
        points = [scene.anchor_position(a) for a in self.anchors]
        self.segments = []
        path = QPainterPath(points[0])
        for interval, (start, end) in enumerate(zip(points, points[1:])):
            # Orthogonale Fuehrung; gemeinsame Knoten/Benutzerknicke bleiben
            # feste Wegpunkte, waehrend die Port-Endpunkte mitwandern.
            elbow = QPointF(end.x(), start.y())
            for a, b in ((start, elbow), (elbow, end)):
                if not same(a, b):
                    path.lineTo(b)
                    self.segments.append((a, b, interval))
        self.setPath(path)
        self.setPen(QPen(QColor(scene.wire_color), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#62bce8") if self.isSelected() else QColor(self.scene().wire_color),
                            3 if self.isSelected() else 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(self.path())


class CircuitScene(QGraphicsScene):
    modified = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.components, self.wires, self.nodes = {}, {}, {}
        self.grid = 10
        self.dark = False
        self.blueprint = False
        self.loading = False
        self._crossings = []
        self.setSceneRect(-1000, -1000, 4000, 3000)
        self.set_theme(False)

    def set_theme(self, dark, blueprint=False):
        self.dark, self.blueprint = bool(dark), bool(blueprint)
        self.background = "#153553" if blueprint else ("#182126" if dark else "#f6f8f5")
        self.ink = "#edf8ff" if blueprint else ("#dae5e8" if dark else "#24373d")
        self.wire_color = "#a9d8f0" if blueprint else ("#36835b" if dark else "#236b46")
        self.grid_color = "#284a64" if blueprint else ("#2c3a40" if dark else "#dce4df")
        self.setBackgroundBrush(QColor(self.background))
        for wire in self.wires.values():
            wire.update_path()
        self.update()

    def snap(self, p):
        return QPointF(round(p.x()/self.grid)*self.grid, round(p.y()/self.grid)*self.grid)

    def set_grid(self, size):
        size = int(size)
        if size not in (5, 10, 15, 20):
            raise ValueError("Raster muss 5, 10, 15 oder 20 Pixel betragen.")
        for component in self.components.values():
            component.prepareGeometryChange()
        self.grid = size
        for component in self.components.values():
            component.setPos(self.snap(component.pos()))
            component.update()
        for key, position in self.nodes.items():
            self.nodes[key] = xy(self.snap(point(position)))
        self.refresh_wires()
        self.modified.emit()

    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        # Bei starkem Herauszoomen nur ein groebes Unterraster zeichnen.
        step = self.grid
        scale = max(.01, abs(painter.transform().m11()))
        while step * scale < 7:
            step *= 2
        painter.setPen(QPen(QColor(self.grid_color), 1))
        points = []
        for x in range(math.floor(rect.left()/step)*step, math.ceil(rect.right())+1, step):
            for y in range(math.floor(rect.top()/step)*step, math.ceil(rect.bottom())+1, step):
                points.append(QPointF(x, y))
        if points:
            painter.drawPoints(QPolygonF(points))

    def add_component(self, kind, position, name=None, component_id=None):
        if kind not in CATALOG:
            raise ValueError("Unbekannte Komponente")
        if not name:
            prefix = CATALOG[kind]["prefix"]
            names = {c.name for c in self.components.values()}
            number = 1
            while f"{prefix}{number}" in names:
                number += 1
            name = f"{prefix}{number}"
        item = ComponentItem(kind, name, component_id)
        self.components[item.uid] = item
        self.addItem(item)
        item.setPos(self.snap(position))
        self.clearSelection()
        item.setSelected(True)
        if not self.loading:
            self.modified.emit()
        return item

    def new_node(self, position):
        key = uid()
        self.nodes[key] = xy(self.snap(position))
        return {"node": key}

    def anchor_position(self, anchor):
        if "component" in anchor:
            return self.components[anchor["component"]].port_position(anchor["port"])
        return point(self.nodes[anchor["node"]])

    @staticmethod
    def anchor_key(anchor):
        return ("port", anchor["component"], anchor["port"]) if "component" in anchor else ("node", anchor["node"])

    def port_at(self, pos, tolerance=8):
        nearest, best = None, tolerance
        for component in self.components.values():
            for i in range(len(CATALOG[component.kind]["ports"])):
                d = distance(pos, component.port_position(i))
                if d <= best:
                    nearest, best = {"component": component.uid, "port": i}, d
        return nearest

    def wire_at(self, pos, tolerance=6):
        best = None
        for wire in self.wires.values():
            for a, b, interval in wire.segments:
                projected = project_segment(pos, a, b)
                d = distance(pos, projected)
                if d <= tolerance and (best is None or d < best[0]):
                    best = (d, wire, projected, interval)
        return best

    def insert_anchor(self, wire, position, anchor=None):
        """Fuegt einen topologischen Knoten in den getroffenen Pfadabschnitt."""
        for index, existing in enumerate(wire.anchors):
            if same(self.anchor_position(existing), position):
                if anchor is not None and existing != anchor:
                    wire.anchors[index] = copy.deepcopy(anchor)
                return copy.deepcopy(wire.anchors[index])
        nearest = min(wire.segments, key=lambda s: distance(position, project_segment(position, s[0], s[1])))
        inserted = copy.deepcopy(anchor) if anchor is not None else self.new_node(position)
        wire.anchors.insert(nearest[2]+1, inserted)
        wire.update_path()
        return copy.deepcopy(inserted)

    def contact_at(self, position, tolerance=8):
        port = self.port_at(position, tolerance)
        if port:
            return port
        hit = self.wire_at(position, tolerance)
        if hit:
            anchor = self.insert_anchor(hit[1], self.snap(hit[2]))
            self.refresh_wires()
            return anchor
        return self.new_node(position)

    def add_wire(self, anchors, wire_id=None):
        if len(anchors) < 2:
            raise ValueError("Eine Leitung braucht mindestens zwei Endpunkte.")
        if all(same(self.anchor_position(anchors[0]), self.anchor_position(a)) for a in anchors[1:]):
            raise ValueError("Leitung ohne Länge")
        wire = WireItem(anchors, wire_id)
        self.wires[wire.uid] = wire
        self.addItem(wire)
        wire.update_path()
        self.refresh_wires()
        if not self.loading:
            self.modified.emit()
        return wire

    def refresh_wires(self):
        if self.loading:
            return
        for wire in self.wires.values():
            wire.update_path()
        self._crossings = self.compute_crossings()
        self.update()

    def compute_crossings(self):
        crossings = {}
        wires = list(self.wires.values())
        for i, first in enumerate(wires):
            for second in wires[i+1:]:
                if not first.sceneBoundingRect().intersects(second.sceneBoundingRect()):
                    continue
                for a, b, _ in first.segments:
                    for c, d, _ in second.segments:
                        pos = intersection(a, b, c, d)
                        if pos is None:
                            continue
                        key = (round(pos.x(), 4), round(pos.y(), 4))
                        entry = crossings.setdefault(key, {"position": pos, "wires": set()})
                        entry["wires"].update((first.uid, second.uid))
        for entry in crossings.values():
            keys = []
            for wire_id in entry["wires"]:
                keys.append({self.anchor_key(a) for a in self.wires[wire_id].anchors
                             if same(self.anchor_position(a), entry["position"])})
            # Mindestens zwei Leitungen benutzen denselben echten Anschluss.
            shared = set()
            seen = set()
            for group in keys:
                shared.update(seen & group)
                seen.update(group)
            entry["shared"] = bool(shared)
            entry["joined"] = bool(set.intersection(*keys)) if keys else False
        return list(crossings.values())

    def crossing_at(self, position, tolerance=8):
        matches = [c for c in self._crossings if distance(c["position"], position) <= tolerance]
        return min(matches, key=lambda c: distance(c["position"], position), default=None)

    def join_crossing(self, crossing):
        position = crossing["position"]
        # Bereits geteilte Ports/Knoten erhalten ihre Identitaet.
        anchor = self.port_at(position, .1)
        if anchor is None:
            anchor = next((copy.deepcopy(a) for w in crossing["wires"]
                           for a in self.wires[w].anchors
                           if same(self.anchor_position(a), position)), None)
        anchor = anchor or self.new_node(position)
        for wire_id in crossing["wires"]:
            self.insert_anchor(self.wires[wire_id], position, anchor)
        self.refresh_wires()
        self.modified.emit()

    def unjoin_crossing(self, crossing):
        position = crossing["position"]
        for wire_id in crossing["wires"]:
            wire = self.wires[wire_id]
            private = self.new_node(position)
            self.insert_anchor(wire, position, private)
        self.refresh_wires()
        self.modified.emit()

    def drawForeground(self, painter, rect):
        painter.setRenderHint(QPainter.Antialiasing)
        for crossing in self._crossings:
            p = crossing["position"]
            if not rect.contains(p):
                continue
            color = QColor(self.wire_color)
            if crossing["joined"]:
                painter.setPen(Qt.NoPen)
                painter.setBrush(color)
                painter.drawEllipse(p, 4, 4)
            else:
                # Ein Bogen ueber der horizontalen Leitung zeigt die Trennung.
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(self.background), 5))
                painter.drawLine(p+QPointF(-6,0), p+QPointF(6,0))
                painter.setPen(QPen(color, 2))
                painter.drawLine(p+QPointF(0,-5), p+QPointF(0,5))
                bridge = QPainterPath(p+QPointF(-6,0))
                bridge.cubicTo(p+QPointF(-6,-9), p+QPointF(6,-9), p+QPointF(6,0))
                painter.setPen(QPen(QColor(self.background), 5))
                painter.drawPath(bridge)
                painter.setPen(QPen(color, 2))
                painter.drawPath(bridge)

    def remove_wire(self, wire):
        if wire.uid in self.wires:
            del self.wires[wire.uid]
            self.removeItem(wire)
            self.refresh_wires()
            self.modified.emit()

    def remove_component(self, component):
        for wire in list(self.wires.values()):
            if any(a.get("component") == component.uid for a in wire.anchors):
                self.remove_wire(wire)
        self.components.pop(component.uid, None)
        self.removeItem(component)
        self.refresh_wires()
        self.modified.emit()

    def network_report(self):
        """Netze folgen Anker-Identitaeten, niemals bloss Bildschirmkreuzungen."""
        parent = {}
        def find(key):
            parent.setdefault(key, key)
            if parent[key] != key:
                parent[key] = find(parent[key])
            return parent[key]
        for wire in self.wires.values():
            keys = [self.anchor_key(a) for a in wire.anchors]
            for key in keys[1:]:
                parent[find(key)] = find(keys[0])
        nets = defaultdict(list)
        for wire in self.wires.values():
            nets[find(self.anchor_key(wire.anchors[0]))].append(wire.uid)
        connected = {self.anchor_key(a) for w in self.wires.values() for a in w.anchors}
        loose = []
        for c in self.components.values():
            for index, (name, _, _) in enumerate(CATALOG[c.kind]["ports"]):
                if ("port", c.uid, index) not in connected:
                    loose.append(f"{c.name}.{name}")
        return list(nets.values()), loose

    def to_data(self):
        used = {a["node"] for w in self.wires.values() for a in w.anchors if "node" in a}
        return {
            "format": "d64-e-baukasten", "version": 1, "grid": self.grid,
            "components": [dict(id=c.uid, kind=c.kind, name=c.name, position=xy(c.pos()),
                                angle=c.angle, value=c.value) for c in self.components.values()],
            "nodes": {n: p for n, p in self.nodes.items() if n in used},
            "wires": [dict(id=w.uid, anchors=copy.deepcopy(w.anchors)) for w in self.wires.values()],
        }

    @staticmethod
    def validate_data(data):
        if not isinstance(data, dict) or data.get("format") != "d64-e-baukasten" or data.get("version") != 1:
            raise ValueError("Keine unterstützte E-Baukasten-Datei.")
        if data.get("grid") not in (5,10,15,20):
            raise ValueError("Ungültiges Raster.")
        components, wires, nodes = data.get("components"), data.get("wires"), data.get("nodes")
        if not isinstance(components, list) or not isinstance(wires, list) or not isinstance(nodes, dict):
            raise ValueError("Ungültige Schaltungsdaten.")
        if len(components)>2000 or len(wires)>4000 or len(nodes)>20000:
            raise ValueError("Die Schaltung ist für diese Editorstufe zu groß.")
        def number(n):
            return isinstance(n,(float,int)) and not isinstance(n,bool) and math.isfinite(n) and abs(n)<=1e12
        def position(p):
            return isinstance(p,list) and len(p)==2 and all(number(n) and abs(n)<=100000 for n in p)
        ids = {}
        for c in components:
            if not isinstance(c,dict) or c.get("kind") not in CATALOG or not isinstance(c.get("id"),str):
                raise ValueError("Ungültige Komponente.")
            if c["id"] in ids or not position(c.get("position")) or not number(c.get("angle")) or not number(c.get("value")):
                raise ValueError("Ungültige Komponentenposition oder Werte.")
            if not isinstance(c.get("name"),str) or len(c["name"])>80:
                raise ValueError("Ungültiger Komponentenname.")
            ids[c["id"]] = c
        if any(not isinstance(n,str) or not position(p) for n,p in nodes.items()):
            raise ValueError("Ungültige Verbindungspunkte.")
        seen = set()
        for w in wires:
            if not isinstance(w,dict) or not isinstance(w.get("id"),str) or w["id"] in seen:
                raise ValueError("Ungültige Leitung.")
            seen.add(w["id"])
            anchors=w.get("anchors")
            if not isinstance(anchors,list) or not 2<=len(anchors)<=200:
                raise ValueError("Ungültiger Leitungspfad.")
            for a in anchors:
                if not isinstance(a,dict):
                    raise ValueError("Ungültiger Leitungsanschluss.")
                if set(a)=={"node"} and isinstance(a["node"],str) and a["node"] in nodes:
                    continue
                if (set(a)=={"component","port"} and isinstance(a["component"],str)
                    and a["component"] in ids and type(a["port"]) is int
                    and 0<=a["port"]<len(CATALOG[ids[a["component"]]["kind"]]["ports"])):
                    continue
                raise ValueError("Leitung verweist auf einen fehlenden Anschluss.")

    def load_data(self, data):
        self.validate_data(data)  # Erst pruefen, dann den vorhandenen Entwurf ersetzen.
        self.loading = True
        try:
            self.clear()
            self.components, self.wires, self.nodes = {}, {}, copy.deepcopy(data["nodes"])
            self.grid = int(data["grid"])
            for c in data["components"]:
                item = self.add_component(c["kind"], point(c["position"]), c["name"], c["id"])
                item.angle, item.value = float(c["angle"])%360, float(c["value"])
            for w in data["wires"]:
                wire = WireItem(w["anchors"], w["id"])
                self.wires[wire.uid] = wire
                self.addItem(wire)
            self.clearSelection()
        finally:
            self.loading = False
        self.refresh_wires()
        self.modified.emit()



class ComponentList(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragOnly)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setIconSize(QSize(48, 40))
        self.setSpacing(4)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if item is None:
            return
        mime = QMimeData()
        mime.setData(MIME_COMPONENT, item.data(Qt.UserRole).encode("utf-8"))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(item.icon().pixmap(48,40))
        drag.exec_(Qt.CopyAction)


class CircuitView(QGraphicsView):
    message = pyqtSignal(str)
    mode_changed = pyqtSignal(str)

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.mode = "mouse"
        self.pending_kind = None
        self.pending_anchors = []
        self.preview = None
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setMinimumSize(180, 180)
        self.centerOn(300, 200)

    def tolerance(self):
        return 8 / max(.25, self.transform().m11())

    def set_mode(self, mode):
        self.cancel_drawing()
        self.mode = mode
        self.pending_kind = None
        self.setDragMode(QGraphicsView.RubberBandDrag if mode == "mouse" else QGraphicsView.NoDrag)
        self.viewport().setCursor(Qt.ArrowCursor if mode == "mouse" else Qt.CrossCursor)
        self.mode_changed.emit(mode)

    def arm_component(self, kind):
        self.set_mode("place")
        self.pending_kind = kind
        self.message.emit(f"{CATALOG[kind]['title']}: auf die Schaltung klicken oder aus der Liste ziehen. ESC bricht ab.")

    @staticmethod
    def dragged_kind(event):
        if not event.mimeData().hasFormat(MIME_COMPONENT):
            return None
        try:
            kind = bytes(event.mimeData().data(MIME_COMPONENT)).decode("utf-8")
        except (UnicodeError, ValueError):
            return None
        return kind if kind in CATALOG else None

    def dragEnterEvent(self, event):
        if self.dragged_kind(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        kind = self.dragged_kind(event)
        if kind:
            self.scene().add_component(kind, self.mapToScene(event.pos()))
            self.set_mode("mouse")
            self.setFocus(Qt.MouseFocusReason)
            self.message.emit("Komponente platziert. Ports verbinden: Werkzeug Leitung wählen.")
            event.acceptProposedAction()
        else:
            event.ignore()

    def cancel_drawing(self):
        self.pending_anchors = []
        if self.preview is not None:
            self.scene().removeItem(self.preview)
            self.preview = None

    def update_preview(self, pos):
        if not self.pending_anchors:
            return
        positions = [self.scene().anchor_position(a) for a in self.pending_anchors]
        positions.append(self.scene().snap(pos))
        path = QPainterPath(positions[0])
        for a,b in zip(positions,positions[1:]):
            path.lineTo(QPointF(b.x(),a.y()))
            path.lineTo(b)
        if self.preview is None:
            self.preview = self.scene().addPath(path, QPen(QColor("#54b9df"),2,Qt.DashLine))
            self.preview.setZValue(30)
        else:
            self.preview.setPath(path)

    def finish_wire(self, position):
        scene = self.scene()
        anchor = scene.contact_at(position, self.tolerance())
        if not self.pending_anchors or not same(scene.anchor_position(self.pending_anchors[-1]), scene.anchor_position(anchor)):
            self.pending_anchors.append(anchor)
        anchors = self.pending_anchors
        self.cancel_drawing()
        try:
            scene.add_wire(anchors)
        except ValueError as exc:
            self.message.emit(str(exc))
            return
        self.message.emit("Leitung verbunden. Weitere Leitung: auf einen Port klicken. ESC bricht ab.")

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return super().mousePressEvent(event)
        pos = self.mapToScene(event.pos())
        scene = self.scene()
        if self.mode == "place" and self.pending_kind:
            scene.add_component(self.pending_kind, pos)
            self.set_mode("mouse")
            self.message.emit("Komponente platziert.")
            event.accept()
            return
        if self.mode == "bridge":
            crossing = scene.crossing_at(pos, self.tolerance())
            if crossing:
                scene.unjoin_crossing(crossing)
                self.message.emit("Überbrückung: diese Leitungen sind hier getrennt.")
            else:
                self.message.emit("Auf eine Leitungskreuzung klicken.")
            event.accept()
            return
        if self.mode == "wire":
            if not self.pending_anchors:
                self.pending_anchors = [scene.contact_at(pos, self.tolerance())]
                self.message.emit("Zielport wählen. Leere Stelle: Knick setzen; Doppelklick: freies Ende; ESC: abbrechen.")
            elif scene.port_at(pos, self.tolerance()) or scene.wire_at(pos, self.tolerance()):
                self.finish_wire(pos)
            else:
                snap = scene.snap(pos)
                if not same(scene.anchor_position(self.pending_anchors[-1]),snap):
                    self.pending_anchors.append(scene.new_node(snap))
            self.update_preview(pos)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.mode == "wire" and self.pending_anchors and event.button() == Qt.LeftButton:
            self.finish_wire(self.mapToScene(event.pos()))
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mouseMoveEvent(self, event):
        self.update_preview(self.mapToScene(event.pos()))
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.set_mode("mouse")
            self.message.emit("Aktion abgebrochen. Mausmodus aktiv.")
            event.accept()
            return
        if event.key() == Qt.Key_Delete:
            self.cancel_drawing()
            selected = list(self.scene().selectedItems())
            for item in selected:
                if isinstance(item, WireItem) and item.uid in self.scene().wires:
                    self.scene().remove_wire(item)
            for item in selected:
                if isinstance(item, ComponentItem) and item.uid in self.scene().components:
                    self.scene().remove_component(item)
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            factor = 1.15 if event.angleDelta().y()>0 else 1/1.15
            if .25 <= self.transform().m11()*factor <= 4:
                self.scale(factor,factor)
            event.accept()
        else:
            super().wheelEvent(event)

    def contextMenuEvent(self, event):
        scene = self.scene()
        pos = self.mapToScene(event.pos())
        component = next((item for item in self.items(event.pos()) if isinstance(item, ComponentItem)), None)
        menu = QMenu(self)
        if component:
            scene.clearSelection()
            component.setSelected(True)
            for angle in (90, 180, 260):
                action = menu.addAction(f"Um {angle}° drehen")
                action.triggered.connect(lambda checked=False,a=angle: component.rotate_by(a))
            menu.addSeparator()
            menu.addAction("Komponente löschen", lambda: scene.remove_component(component))
        else:
            crossing = scene.crossing_at(pos, self.tolerance())
            hit = scene.wire_at(pos, self.tolerance())
            if not crossing and not hit:
                return
            chosen = next((w for w in scene.selectedItems() if isinstance(w,WireItem)
                           and crossing and w.uid in crossing["wires"]), None)
            wire = chosen or (hit[1] if hit else scene.wires[next(iter(crossing["wires"]))])
            scene.clearSelection()
            wire.setSelected(True)
            separate = menu.addAction("Zusammenführung aufheben")
            separate.setEnabled(bool(crossing and crossing["shared"]))
            join = menu.addAction("Zusammenführen")
            join.setEnabled(bool(crossing and not crossing["joined"]))
            if crossing:
                separate.triggered.connect(lambda: scene.unjoin_crossing(crossing))
                join.triggered.connect(lambda: scene.join_crossing(crossing))
            menu.addSeparator()
            menu.addAction("Leitung löschen", lambda: scene.remove_wire(wire))
            menu.addAction("Hilfe", lambda: QMessageBox.information(self, "Leitungen und Kreuzungen",
                "Punkt: Leitungen sind hier verbunden.\nBogen: Leitungen überkreuzen sich ohne Verbindung.\n\n"
                "Zusammenführen erzeugt einen gemeinsamen Verbindungspunkt. Dieser bleibt beim Verschieben "
                "der Bauteile erhalten. Zusammenführung aufheben trennt die Leitungen an diesem Punkt.\n\n"
                "Im Werkzeug Leitung: Port anklicken, Knicke setzen, Zielport anklicken. "
                "Ein Klick auf eine bestehende Leitung erzeugt einen Abzweig."))
        menu.exec_(event.globalPos())
        event.accept()


class ElectronicsWorkbench(QWidget):
    """Einbettbarer Inhalt des E-Baukasten-Docking-Fensters."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("e_baukasten_widget")
        self.current_path = None
        self.dirty = False
        self.current_component = None
        self.dark = False
        self.scene = CircuitScene(self)
        self.tabs = QTabWidget(self)
        self.tabs.setObjectName("e_baukasten_tabs")
        self.circuit_page = QWidget()
        self.tabs.addTab(self.circuit_page, "Schaltung")
        self.simulation_page = QWidget()
        self.tabs.addTab(self.simulation_page, "Simulation")
        self.blueprint_page = QWidget()
        self.tabs.addTab(self.blueprint_page, "Blaupause")
        root = QVBoxLayout(self)
        root.setContentsMargins(4,4,4,4)
        root.addWidget(self.tabs)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setObjectName("e_baukasten_horizontal_splitter")
        self.splitter.setChildrenCollapsible(False)
        page_layout = QVBoxLayout(self.circuit_page)
        page_layout.setContentsMargins(0,4,0,0)
        page_layout.addWidget(self.splitter)

        sidebar = QWidget()
        sidebar.setMinimumWidth(190)
        left = QVBoxLayout(sidebar)
        left.setContentsMargins(0,0,0,0)
        self.side_splitter = QSplitter(Qt.Vertical)
        self.side_splitter.setChildrenCollapsible(False)
        left.addWidget(self.side_splitter)
        self.category_tabs = QTabWidget()
        self.category_tabs.setObjectName("e_baukasten_component_tabs")
        self.category_tabs.setTabPosition(QTabWidget.West)
        self.category_tabs.setUsesScrollButtons(True)
        self.category_tabs.setMinimumHeight(190)
        self.lists = {}
        for category in CATEGORIES:
            listing = ComponentList()
            listing.setObjectName("e_baukasten_list_" + category.lower())
            for kind, definition in CATALOG.items():
                if definition["category"] != category:
                    continue
                item = QListWidgetItem(definition["title"])
                item.setData(Qt.UserRole,kind)
                item.setSizeHint(QSize(190,52))
                item.setToolTip(definition["details"])
                listing.addItem(item)
            listing.itemClicked.connect(self.pick_component)
            self.category_tabs.addTab(listing,category)
            self.lists[category] = listing
        self.side_splitter.addWidget(self.category_tabs)

        self.properties_scroll = QScrollArea()
        self.properties_scroll.setObjectName("e_baukasten_properties_scroll")
        self.properties_scroll.setWidgetResizable(True)
        self.properties_scroll.setMinimumHeight(120)
        properties = QWidget()
        properties_layout = QVBoxLayout(properties)
        properties_layout.setContentsMargins(4,4,4,4)
        self.data_group = QGroupBox("Daten")
        self.data_form = QFormLayout(self.data_group)
        self.data_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.data_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.details_group = QGroupBox("Details")
        self.details_label = QLabel("Komponente aus der Liste wählen oder in der Schaltung markieren.")
        self.details_label.setWordWrap(True)
        self.details_label.setTextFormat(Qt.PlainText)
        details_layout = QVBoxLayout(self.details_group)
        details_layout.addWidget(self.details_label)
        properties_layout.addWidget(self.data_group)
        properties_layout.addWidget(self.details_group)
        properties_layout.addStretch()
        self.properties_scroll.setWidget(properties)
        self.side_splitter.addWidget(self.properties_scroll)
        self.side_splitter.setSizes([340,260])
        self.splitter.addWidget(sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0,0,0,0)
        self.toolbar = QToolBar("E-Baukasten")
        self.toolbar.setObjectName("e_baukasten_toolbar")
        self.toolbar.setIconSize(QSize(18,18))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)
        self.toolbar.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Fixed)
        self.view = CircuitView(self.scene)
        self.view.setObjectName("e_baukasten_circuit_view")
        self.tools = QActionGroup(self)
        self.tools.setExclusive(True)
        self.mode_actions = {}
        for label,mode in (("Maus","mouse"),("Leitung","wire"),("Überbrücken","bridge")):
            action = self.toolbar.addAction(label)
            action.setCheckable(True)
            action.setData(mode)
            self.tools.addAction(action)
            self.mode_actions[mode] = action
            action.triggered.connect(lambda checked=False,m=mode: self.view.set_mode(m))
        self.mode_actions["mouse"].setChecked(True)
        self.view.mode_changed.connect(lambda mode: self.mode_actions.get(mode,self.mode_actions["mouse"]).setChecked(True))
        self.toolbar.addSeparator()
        self.start_action = self.toolbar.addAction("Start", self.start_check)
        self.start_action.setToolTip("Verbindungen und offene Ports prüfen; Simulation-Tab öffnen")
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QLabel(" Raster "))
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(5,20)
        self.grid_spin.setSingleStep(5)
        self.grid_spin.setValue(10)
        self.grid_spin.setSuffix(" px")
        self.grid_spin.setFixedWidth(82)
        self.grid_spin.editingFinished.connect(self.change_grid)
        self.toolbar.addWidget(self.grid_spin)
        self.toolbar.addSeparator()
        self.toolbar.addAction("Laden", self.load_file)
        self.toolbar.addAction("Speichern", self.save_file)
        self.toolbar.addAction("Speichern unter …", lambda: self.save_file(True))
        self.toolbar.addAction("Einpassen", self.fit_circuit)
        self.toolbar.addSeparator()
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.view,1)
        self.message_label = QLabel("Komponente anklicken und platzieren oder per Drag & Drop in die Schaltung ziehen.")
        self.message_label.setWordWrap(True)
        right_layout.addWidget(self.message_label)
        self.view.message.connect(self.message_label.setText)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setSizes([290,900])

        simulation_layout = QVBoxLayout(self.simulation_page)
        simulation_layout.addWidget(QLabel("Verbindungen und Netze"))
        self.simulation_output = QPlainTextEdit()
        self.simulation_output.setReadOnly(True)
        self.simulation_output.setPlainText(
            "Mit Start die Schaltung auf Verbindungen und offene Anschlüsse prüfen.\n\n"
            "Diese Stufe enthält den Schaltungseditor und die Netztopologie.\n"
            "Eine elektrische Simulation mit Spannungen, Strömen oder Zeitverläufen ist noch nicht implementiert.")
        simulation_layout.addWidget(self.simulation_output)
        self.blueprint_scene = CircuitScene(self)
        self.blueprint_view = QGraphicsView(self.blueprint_scene)
        self.blueprint_view.setInteractive(False)
        self.blueprint_view.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        blueprint_layout = QVBoxLayout(self.blueprint_page)
        blueprint_layout.addWidget(QLabel("Blaupause · aktuelle Schaltung als schreibgeschützte Übersicht"))
        blueprint_layout.addWidget(self.blueprint_view)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.scene.selectionChanged.connect(self.selection_changed)
        self.scene.modified.connect(self.on_modified)
        self.show_properties(None)
        self.set_dark_mode(False)

    def icon_for(self, kind):
        pixmap = QPixmap(64,48)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(32,24)
        painter.scale(.65,.55)
        painter.setPen(QPen(QColor(self.scene.ink),2.2))
        painter.setBrush(Qt.NoBrush)
        ComponentItem(kind, "").draw_symbol(painter,QColor(self.scene.ink))
        painter.end()
        return QIcon(pixmap)

    def set_dark_mode(self, enabled):
        self.dark = bool(enabled)
        self.scene.set_theme(enabled)
        self.blueprint_scene.set_theme(enabled,True)
        background, foreground, border = (("#202a30","#e0e8ec","#46555e") if enabled
                                          else ("#f5f7f3","#25343b","#bcc9c1"))
        palette = QPalette(self.palette())
        for role in (QPalette.Window,QPalette.Base,QPalette.Button):
            palette.setColor(role,QColor(background))
        for role in (QPalette.WindowText,QPalette.Text,QPalette.ButtonText):
            palette.setColor(role,QColor(foreground))
        palette.setColor(QPalette.Highlight,QColor("#315c72"))
        palette.setColor(QPalette.HighlightedText,Qt.white)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self.setStyleSheet(
            f"QWidget#e_baukasten_widget {{ background: {background}; color: {foreground}; }}"
            f"QWidget#e_baukasten_widget QWidget {{ background-color: {background}; color: {foreground}; }}"
            f"QWidget#e_baukasten_widget QGroupBox {{ border: 1px solid {border}; margin-top: 12px; padding-top: 8px; }}"
            f"QWidget#e_baukasten_widget QGroupBox::title {{ color: {foreground}; subcontrol-origin: margin; left: 8px; }}"
            f"QWidget#e_baukasten_widget QTabWidget::pane {{ border: 1px solid {border}; }}"
            f"QWidget#e_baukasten_widget QTabBar::tab {{ background: {background}; color: {foreground}; padding: 6px; border: 1px solid {border}; }}"
            "QWidget#e_baukasten_widget QTabBar::tab:selected { background: #315c72; color: white; }"
            f"QWidget#e_baukasten_widget QToolButton {{ color: {foreground}; padding: 4px; }}"
            "QWidget#e_baukasten_widget QToolButton:checked { background: #315c72; color: white; }"
            f"QWidget#e_baukasten_widget QLineEdit, QWidget#e_baukasten_widget QAbstractSpinBox {{ border: 1px solid {border}; padding: 3px; }}"
            f"QWidget#e_baukasten_widget QListWidget {{ background: {background}; color: {foreground}; }}"
            "QWidget#e_baukasten_widget QListWidget::item:selected { background: #315c72; color: white; }"
        )
        for listing in self.lists.values():
            for i in range(listing.count()):
                item = listing.item(i)
                item.setIcon(self.icon_for(item.data(Qt.UserRole)))

    def pick_component(self, item):
        kind = item.data(Qt.UserRole)
        self.view.arm_component(kind)
        self.scene.clearSelection()
        self.show_properties(None, kind)

    def selection_changed(self):
        component = next((item for item in self.scene.selectedItems() if isinstance(item,ComponentItem)),None)
        self.show_properties(component)

    def show_properties(self, component, catalog_kind=None):
        self.current_component = component
        while self.data_form.count():
            item = self.data_form.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        self.value_editor = None
        if component is None:
            self.data_form.addRow(QLabel("Zum Ändern eine platzierte Komponente markieren."))
            self.details_label.setText(CATALOG[catalog_kind]["details"] if catalog_kind else
                "Komponente aus der Liste wählen oder in der Schaltung markieren.")
            return
        definition = CATALOG[component.kind]
        name = QLineEdit(component.name)
        name.setMaxLength(80)
        name.editingFinished.connect(lambda: self.update_name(component,name.text()))
        self.data_form.addRow("Name",name)
        if definition["unit"]:
            value = QDoubleSpinBox()
            value.setRange(-1e9 if definition["category"] == "Quelle" else 0, 1e9)
            value.setDecimals(6)
            value.setSuffix(" " + definition["unit"])
            value.setValue(component.value)
            value.setKeyboardTracking(False)
            value.valueChanged.connect(lambda v: self.update_value(component,v))
            self.value_editor = value
            label = {"Ω":"Widerstand","V":"Spannung","A":"Strom","µF":"Kapazität"}[definition["unit"]]
            if definition["symbol"] == "led":
                label = "Flussspannung"
            self.data_form.addRow(label,value)
        self.angle_label = QLabel(f"{component.angle:g}°")
        self.position_label = QLabel(f"{component.x():g} / {component.y():g}")
        self.data_form.addRow("Drehung",self.angle_label)
        self.data_form.addRow("X / Y",self.position_label)
        self.details_label.setText(definition["title"] + "\n\n" + definition["details"] +
            "\n\nPorts: " + ", ".join(p[0] for p in definition["ports"]))

    def update_name(self, component, name):
        if component.uid in self.scene.components and name.strip():
            component.name = name.strip()
            component.update()
            self.scene.modified.emit()

    def update_value(self, component, value):
        if component.uid in self.scene.components:
            component.value = float(value)
            component.update()
            self.scene.modified.emit()

    def on_modified(self):
        if self.scene.loading:
            return
        self.dirty = True
        component = self.current_component
        if component and component.uid in self.scene.components:
            self.angle_label.setText(f"{component.angle:g}°")
            self.position_label.setText(f"{component.x():g} / {component.y():g}")
        if self.tabs.currentIndex() == 1:
            self.simulation_output.setPlainText("Die Schaltung wurde geändert. Mit Start erneut prüfen.")
        if self.tabs.currentIndex() == 2:
            self.refresh_blueprint()

    def change_grid(self):
        grid = min((5,10,15,20),key=lambda n: abs(n-self.grid_spin.value()))
        self.grid_spin.setValue(grid)
        if self.scene.grid != grid:
            self.view.cancel_drawing()
            self.scene.set_grid(grid)

    def fit_circuit(self):
        if self.scene.components or self.scene.wires:
            self.view.fitInView(self.scene.itemsBoundingRect().adjusted(-60,-60,60,60),Qt.KeepAspectRatio)
        else:
            self.view.resetTransform()
            self.view.centerOn(300,200)

    def start_check(self):
        nets, loose = self.scene.network_report()
        lines = ["Verbindungsprüfung abgeschlossen", "",
                 f"Komponenten: {len(self.scene.components)}", f"Leitungen: {len(self.scene.wires)}",
                 f"Netze: {len(nets)}", f"Offene Ports: {len(loose)}", ""]
        for index, net in enumerate(nets,1):
            ports = set()
            for wire_id in net:
                for a in self.scene.wires[wire_id].anchors:
                    if "component" in a:
                        c = self.scene.components[a["component"]]
                        ports.add(c.name + "." + CATALOG[c.kind]["ports"][a["port"]][0])
            lines.append(f"Netz {index}: " + (", ".join(sorted(ports)) or "freie Leitung"))
        if loose:
            lines.extend(["", "Offene Ports: " + ", ".join(loose)])
        lines.extend(["", "Die Prüfung untersucht die Verdrahtung. Elektrische Spannungs-/Stromberechnung",
                      "und Zeitverläufe sind in dieser Stufe noch nicht implementiert."])
        self.simulation_output.setPlainText("\n".join(lines))
        self.tabs.setCurrentWidget(self.simulation_page)

    def tab_changed(self, index):
        if index != 0:
            self.view.cancel_drawing()
        if index == 2:
            self.refresh_blueprint()

    def refresh_blueprint(self):
        self.blueprint_scene.load_data(self.scene.to_data())
        self.blueprint_scene.set_theme(self.dark,True)
        bounds = self.blueprint_scene.itemsBoundingRect()
        if not bounds.isEmpty():
            self.blueprint_view.fitInView(bounds.adjusted(-50,-50,50,50),Qt.KeepAspectRatio)

    def save_to_path(self, path):
        target = Path(path)
        text = json.dumps(self.scene.to_data(),ensure_ascii=False,indent=2)
        temporary = target.with_name(target.name+".tmp-"+uid())
        try:
            temporary.write_text(text,encoding="utf-8")
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        self.current_path, self.dirty = target, False
        self.message_label.setText(f"Gespeichert: {target.name}")

    def save_file(self, save_as=False):
        path = self.current_path
        if save_as or path is None:
            filename,_ = QFileDialog.getSaveFileName(self,"E-Baukasten speichern",
                str(path or "Schaltung.ebk"),"E-Baukasten (*.ebk)")
            if not filename:
                return False
            path = Path(filename)
            if not path.suffix:
                path = path.with_suffix(".ebk")
        try:
            self.save_to_path(path)
        except OSError as exc:
            QMessageBox.warning(self,"Speichern fehlgeschlagen",str(exc))
            return False
        return True

    def load_from_path(self, path):
        path = Path(path)
        if path.stat().st_size > 10*1024*1024:
            raise ValueError("Die E-Baukasten-Datei ist zu groß.")
        data = json.loads(path.read_text(encoding="utf-8"))
        self.scene.validate_data(data)
        self.view.cancel_drawing()
        self.current_component = None
        self.scene.load_data(data)
        self.grid_spin.setValue(self.scene.grid)
        self.current_path, self.dirty = path, False
        self.tabs.setCurrentIndex(0)
        self.show_properties(None)
        self.fit_circuit()
        self.message_label.setText(f"Geladen: {path.name}")

    def confirm_discard(self):
        if not self.dirty:
            return True
        answer = QMessageBox.question(self,"E-Baukasten", "Änderungen an der Schaltung speichern?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,QMessageBox.Save)
        if answer == QMessageBox.Cancel:
            return False
        return self.save_file() if answer == QMessageBox.Save else True

    def load_file(self):
        if not self.confirm_discard():
            return
        filename,_ = QFileDialog.getOpenFileName(self,"E-Baukasten laden","","E-Baukasten (*.ebk)")
        if not filename:
            return
        try:
            self.load_from_path(filename)
        except (OSError,ValueError,TypeError,KeyError) as exc:
            QMessageBox.warning(self,"Schaltung konnte nicht geladen werden",str(exc))
