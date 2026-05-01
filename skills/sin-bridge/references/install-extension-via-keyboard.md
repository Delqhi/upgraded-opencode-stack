# Chrome Extension Installation via Keyboard (Tastatur-Only Workflow)

## Zweck / Purpose

Diese Sequenz installiert eine entpackte Chrome Extension (Unpacked Extension)
OHNE Maus — nur via Spotlight + Tastatur. Exakt 1:1 gespeicherter Ablauf des Users.

## Anwendungsfall / Use Case

- OpenSIN Bridge Extension in Default Chrome Profil installieren
- Jede andere Unpacked Extension installieren
- Automatisierbar via AppleScript oder skylight-cli-mcp Tastatur-Simulation

## Exakter Ablauf (1:1 gespeichert vom User)

### Schritt 1: Spotlight öffnen

```
CMD + LEERTASTE
```

- Öffnet macOS Spotlight Search

### Schritt 2: Chrome starten

```
"chrome" eintippen + ENTER
```

- Chrome wird gesucht und geöffnet

### Schritt 3: Adressleiste anspringen

```
TAB (4x) + ENTER
```

- Navigiert zur Chrome Adressleiste / URL Bar

### Schritt 4: Extensions-URL eingeben

```
TAB (3x) + LEERTASTE
```

- Öffnet chrome://extensions oder navigiert zum Extensions-Bereich

### Schritt 5: Developer Mode / Entwicklermodus

```
TAB (10x) + ENTER
```

- Aktiviert den Entwicklermodus (Developer Mode Toggle)

### Schritt 6: "Entpackte Erweiterung laden" Button

```
TAB (2x) + ENTER
```

- Klickt auf den Button "Entpackte Erweiterung laden" (Load unpacked)

### Schritt 7: Extension-Ordner auswählen

```
Extension-Ordner auswählen im Finder-Dialog
```

- Navigiert zum Ordner der Extension und bestätigt

## Automatisierung via AppleScript

```applescript
-- OpenSIN Bridge Extension via Spotlight + Tastatur installieren
tell application "System Events"
    -- Schritt 1: Spotlight
    key down command
    key down space
    key up space
    key up command
    delay 0.5

    -- Schritt 2: Chrome öffnen
    keystroke "chrome"
    delay 0.3
    key code 36 -- ENTER
    delay 2

    -- Schritt 3: 4x TAB + ENTER
    repeat 4 times
        key code 48 -- TAB
        delay 0.1
    end repeat
    key code 36 -- ENTER
    delay 0.5

    -- Schritt 4: 3x TAB + LEERTASTE
    repeat 3 times
        key code 48 -- TAB
        delay 0.1
    end repeat
    keystroke " " -- LEERTASTE
    delay 0.5

    -- Schritt 5: 10x TAB + ENTER (Developer Mode)
    repeat 10 times
        key code 48 -- TAB
        delay 0.1
    end repeat
    key code 36 -- ENTER
    delay 0.5

    -- Schritt 6: 2x TAB + ENTER (Load Unpacked)
    repeat 2 times
        key code 48 -- TAB
        delay 0.1
    end repeat
    key code 36 -- ENTER
    delay 1

    -- Schritt 7: Extension-Ordner auswählen
    -- Hier muss der Pfad zur Extension eingetragen werden:
    -- z.B. /Users/jeremy/dev/OpenSIN-Bridge/extension
end tell
```

## Integration in real*bridge*\*.py

```python
async def install_opensin_bridge_extension():
    """
    Installiert die OpenSIN Bridge Extension via macOS AppleScript Keyboard-Simulation.
    WHY: Notwendig wenn Extension nicht bereits installiert ist oder nach Chrome-Neuinstallation.
    CONSEQUENCES: Ändert Chrome-Konfiguration dauerhaft (Extension bleibt installiert).
    """
    extension_path = "/Users/jeremy/dev/OpenSIN-Bridge/extension"

    script = f'''
    tell application "System Events"
        key down command
        key down space
        key up space
        key up command
        delay 0.5
        keystroke "chrome"
        delay 0.3
        key code 36
        delay 2
        repeat 4 times
            key code 48
            delay 0.1
        end repeat
        key code 36
        delay 0.5
        repeat 3 times
            key code 48
            delay 0.1
        end repeat
        keystroke " "
        delay 0.5
        repeat 10 times
            key code 48
            delay 0.1
        end repeat
        key code 36
        delay 0.5
        repeat 2 times
            key code 48
            delay 0.1
        end repeat
        key code 36
        delay 1
        keystroke "{extension_path}"
        key code 36
        delay 1
    end tell
    '''

    import subprocess
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.returncode == 0
```

## Referenz / Tags

- Tags: chrome, extension, install, unpacked, keyboard, spotlight, applescript
- Kontext: OpenSIN Bridge, A2A-SIN-Worker-heypiggy, sin-bridge skill
- Zuletzt aktualisiert: 2026-04-10
- Quelle: Exakter Ablauf gespeichert vom User
