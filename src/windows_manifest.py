"""Stage 149: project manifest data and XML export (no external toolchain)."""
import re
import xml.etree.ElementTree as ET


# Microsoft Learn: /windows/win32/sbscs/application-manifests#supportedos
# None means no documented supportedOS ID; never invent a Windows GUID.
SUPPORTED_OS = (
    ("Windows 12", None),
    ("Windows 11", "{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"),
    ("Windows 10", "{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"),
    ("Windows Vista", "{e2011457-1546-43c5-a5fe-008deee3d3f0}"),
    ("Windows 8.1", "{1f676c76-80e1-4239-95bb-83d0f6d0da78}"),
    ("Windows 8", "{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"),
    ("Windows 7", "{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"),
    ("Windows XP", None),
)
IDENTITY_DEFAULTS = {
    "type": "win32", "name": "", "language": "*",
    "processorArchitecture": "*", "version": "6.0.0.0", "publicKeyToken": "",
}
GUID_PATTERN = r"\{[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\}"


def normalize_manifest_settings(value=None):
    """Return independent data, also for old projects without a manifest section."""
    value = value if isinstance(value, dict) else {}
    identity = value.get("identity", {})
    identity = identity if isinstance(identity, dict) else {}
    compatibility = value.get("compatibility", {})
    compatibility = compatibility if isinstance(compatibility, dict) else {}
    result = {
        "identity": {key: str(identity.get(key, default)) for key, default in IDENTITY_DEFAULTS.items()},
        "compatibility": {},
        "longPathAware": str(value.get("longPathAware", True)).lower() in {"true", "1", "yes"},
    }
    for name, guid in SUPPORTED_OS:
        entry = compatibility.get(name, {})
        entry = entry if isinstance(entry, dict) else {}
        result["compatibility"][name] = {
            "checked": str(entry.get("checked", False)).lower() in {"true", "1", "yes"},
            "id": str(entry.get("id", guid or "")).strip(),
        }
    return result


def manifest_xml(value):
    """Validate and serialize the application identity, OS IDs and long-path flag."""
    data = normalize_manifest_settings(value)
    identity = {key: text.strip() for key, text in data["identity"].items()}
    if identity["type"] != "win32":
        raise ValueError("Type muss für ein Windows-Manifest win32 sein.")
    if not identity["name"]:
        raise ValueError("Bitte unter Identity Attribute einen Namen für die Anwendung eintragen.")
    version = identity["version"]
    if not re.fullmatch(r"[0-9]{1,5}(\.[0-9]{1,5}){3}", version) or any(int(p) > 65535 for p in version.split(".")):
        raise ValueError("Version benötigt vier Zahlen von 0 bis 65535 (z. B. 6.0.0.0).")
    token = identity["publicKeyToken"]
    if token and not re.fullmatch(r"[0-9a-fA-F]{16}", token):
        raise ValueError("publicKeyToken muss leer sein oder aus 16 Hexadezimalzeichen bestehen.")
    for text in identity.values():
        if any(not (c in "\t\n\r" or 0x20 <= ord(c) <= 0xD7FF or 0xE000 <= ord(c) <= 0xFFFD or 0x10000 <= ord(c) <= 0x10FFFF) for c in text):
            raise ValueError("Die Identity Attribute enthalten ein ungültiges XML-Zeichen.")
    root = ET.Element("assembly", {"xmlns": "urn:schemas-microsoft-com:asm.v1", "manifestVersion": "1.0"})
    # Application identity: omit a neutral language; '*' is the UI default.
    attrs = {key: text for key, text in identity.items() if text and not (key == "language" and text == "*")}
    ET.SubElement(root, "assemblyIdentity", attrs)
    ids = []
    for name, _ in SUPPORTED_OS:
        entry = data["compatibility"][name]
        if not entry["checked"]:
            continue
        guid = entry["id"]
        if name == "Windows XP" and not guid:
            continue  # XP predates supportedOS; keep the selection as project metadata.
        if not re.fullmatch(GUID_PATTERN, guid):
            raise ValueError(f"{name}: Bitte eine gültige supportedOS-ID in geschweiften Klammern eintragen.")
        if guid.lower() not in ids:
            ids.append(guid.lower())
    if ids:
        compatibility = ET.SubElement(root, "compatibility", {"xmlns": "urn:schemas-microsoft-com:compatibility.v1"})
        application = ET.SubElement(compatibility, "application")
        for guid in ids:
            ET.SubElement(application, "supportedOS", {"Id": guid})
    application = ET.SubElement(root, "application", {"xmlns": "urn:schemas-microsoft-com:asm.v3"})
    settings = ET.SubElement(application, "windowsSettings")
    ET.SubElement(settings, "longPathAware", {"xmlns": "http://schemas.microsoft.com/SMI/2016/WindowsSettings"}).text = "true" if data["longPathAware"] else "false"
    ET.indent(root, space="   ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"
