# Vision Gate Rules

## Absolutes Autorun-Verbot

- **AUTORUN IST PERMANENT VERBOTEN.** Kein Agent darf jemals eine Sequenz von Web-Aktionen "am Stück" ausführen ohne zwischen JEDER einzelnen Aktion den Bildschirm zu fotografieren und durch das Vision-Modell prüfen zu lassen.

## Die Vision-Gate-Schleife

Für JEDE Browser-Interaktion:

1. Aktion ausführen
2. Screenshot des gesamten Bildschirms
3. Screenshot an Vision-Modell senden
4. Vision-Modell-Antwort lesen
5. Nur bei POSITIVEM Ergebnis → nächste Aktion

## Vision-Modell

Primäres Modell: `meta/llama-3.2-11b-vision-instruct` via NVIDIA NIM  
Fallback: `look-screen` CLI mit REST API Chain

## OpenSIN-Bridge Pflicht

Keine Web-Automation ohne OpenSIN-Bridge. Bridge ist das einzige autorisierte Interface für Browser-DOM-Interaktionen.

## Konsequenzen

- Web-Aktion ohne Screenshot = **PERMANENTER BAN**
- Vision-Modell ignoriert = **PERMANENTER BAN**
- Autorun = **PERMANENTER BAN**
