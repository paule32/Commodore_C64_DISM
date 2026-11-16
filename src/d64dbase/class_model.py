"""Stage 334: dBase class declarations and TObject ancestry metadata.

This module describes classes; code generation / dynamic dispatch is separate.
"""
from dataclasses import dataclass, field
import re
from typing import Dict, Tuple


class DBaseClassError(ValueError):
    pass


@dataclass(frozen=True)
class DBaseClassInfo:
    name: str
    parent: str
    methods: Tuple[str, ...] = ()
    properties: Tuple[str, ...] = ()
    builtin: bool = False
    property_access: Tuple[Tuple[str, str], ...] = ()


class DBaseClassRegistry:
    def __init__(self):
        self._classes: Dict[str, DBaseClassInfo] = {}
        self.register("TObject", None, builtin=True)
        self.register("FORM", "TObject", builtin=True)
        self.register("TV_Object", "TObject", builtin=True)
        self.register("TV_Application", "TV_Object", builtin=True)

    def register(self, name, parent="TObject", *, methods=(), properties=(), builtin=False, custom=False,
                 property_access=()):
        name = str(name).strip()
        if not re.fullmatch(r"[A-Za-z_]\w*", name):
            raise DBaseClassError(f"Ungueltiger Klassenname: {name!r}")
        key = name.casefold()
        previous = self._classes.get(key)
        if previous is not None and not (key == "tobject" and custom and previous.builtin):
            raise DBaseClassError(f"Klasse bereits definiert: {name}")
        if custom:
            # OF CUSTOM ist ein Wurzelklassen-Marker, keine Klasse namens CUSTOM.
            # Nur hier darf die eingebaute TObject-Definition ersetzt werden.
            if parent is not None and str(parent).strip().casefold() != "custom":
                raise DBaseClassError("OF CUSTOM darf keine weitere Basisklasse angeben")
            base = ""
        elif parent is None:
            if key != "tobject":
                raise DBaseClassError("Nur Wurzelklassen mit OF CUSTOM duerfen ohne Basisklasse sein")
            base = ""
        else:
            base = str(parent).strip() or "TObject"
            if key == "tobject":
                raise DBaseClassError("TObject ist die Wurzelklasse (fuer eigene Definition: OF CUSTOM)")
        self._classes[key] = DBaseClassInfo(name, base, tuple(methods), tuple(properties), builtin,
                                             tuple(property_access))
        return self._classes[key]

    def get(self, name):
        return self._classes.get(str(name).casefold())

    def ancestors(self, name):
        current = self.get(name)
        if current is None:
            raise DBaseClassError(f"Unbekannte Klasse: {name}")
        seen = set()
        parents = []
        while current.parent:
            key = current.name.casefold()
            if key in seen:
                raise DBaseClassError(f"Zyklische Klassenvererbung: {current.name}")
            seen.add(key)
            parent = self.get(current.parent)
            if parent is None:
                raise DBaseClassError(f"Unbekannte Basisklasse {current.parent} fuer {current.name}")
            parents.append(parent.name)
            current = parent
        return tuple(parents)

    def validate(self):
        for info in self._classes.values():
            self.ancestors(info.name)
        return self

    def inherits_from(self, name, ancestor):
        return name.casefold() == ancestor.casefold() or any(
            item.casefold() == ancestor.casefold() for item in self.ancestors(name)
        )

    def class_name(self, name):
        info = self.get(name)
        if info is None:
            raise DBaseClassError(f"Unbekannte Klasse: {name}")
        return info.name

    def class_type(self, name):
        """Stable descriptor for compilation, not a runtime instance pointer."""
        info = self.get(name)
        if info is None:
            raise DBaseClassError(f"Unbekannte Klasse: {name}")
        return info


_CLASS = re.compile(
    r"^\s*CLASS\s+([A-Za-z_]\w*)(?:\s+OF\s+([A-Za-z_]\w*))?"
    r"\s*(ENDCLASS)?\s*(?://.*)?$", re.I
)
_METHOD = re.compile(r"^\s*(?:METHOD|PROCEDURE|FUNCTION)\s+([A-Za-z_]\w*)\b", re.I)
_PROPERTY = re.compile(r"^\s*(?:(?:PUBLIC|PRIVATE)\s+)?(?:PROPERTY\s+)?([A-Za-z_]\w*)\s*(?:=\s*.+)?$", re.I)
_END = re.compile(r"^\s*ENDCLASS\s*(?://.*)?$", re.I)


def parse_dbase_class_metadata(source: str, registry=None):
    """Collect CLASS / OF declarations in a source, including implicit TObject.

    No attempt is made here to compile method bodies or generate vtables.
    """
    registry = registry or DBaseClassRegistry()
    active = None
    classes = []
    methods, properties, access = [], [], []
    visibility = 'public'
    for line_no, line in enumerate(str(source).splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("*", "//", "&&")):
            continue
        match = _CLASS.match(line)
        if match:
            if active is not None:
                raise DBaseClassError(f"CLASS verschachtelt in Zeile {line_no}")
            active = (match.group(1), match.group(2) or "TObject")
            methods, properties, access = [], [], []
            visibility = 'public'
            if match.group(3):
                classes.append((active[0], active[1], (), (), ()))
                active = None
            continue
        if _END.match(line):
            if active is None:
                raise DBaseClassError(f"ENDCLASS ohne CLASS in Zeile {line_no}")
            classes.append((active[0], active[1], tuple(methods), tuple(properties), tuple(access)))
            active = None
            continue
        if active is not None:
            mode = re.fullmatch(r'(PUBLIC|PRIVATE)', stripped, re.I)
            if mode:
                visibility = mode.group(1).casefold()
                continue
            m = _METHOD.match(line)
            if m:
                methods.append(m.group(1))
                continue
            m = _PROPERTY.match(line)
            if m and (re.search(r'\bPROPERTY\b', stripped, re.I) or '=' in stripped):
                prop = m.group(1)
                if prop.casefold() not in {item.casefold() for item in properties}:
                    properties.append(prop)
                    explicit = re.match(r'(PUBLIC|PRIVATE)\s+', stripped, re.I)
                    access.append((prop, explicit.group(1).casefold() if explicit else visibility))
    if active is not None:
        raise DBaseClassError(f"ENDCLASS fehlt fuer {active[0]}")
    for name, parent, methods, properties, access in classes:
        registry.register(
            name, parent, methods=methods, properties=properties,
            property_access=access,
            custom=parent.casefold() == "custom",
        )
    return registry.validate()
