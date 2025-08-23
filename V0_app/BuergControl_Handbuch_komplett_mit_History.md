# BürgControl – Komplettes Systemhandbuch

Dieses Dokument beschreibt **vollständig** die Logiken, Workflows, Businessregeln und Hilfetexte der App **BürgControl**.
Es ist optimiert für den Einsatz mit **v0.app** zur Modernisierung und Weiterentwicklung der bestehenden Python/Streamlit-Anwendung.

---

## 1. Grundprinzip (BASE-Logik)
Die App basiert auf dem BASE-Prinzip:
- **B – Bereitstellen:** Hochladen der relevanten Datendateien (SumA, EZA, NCTS, ZLVHV).
- **A – Analysieren:** Automatisierte Validierung und Analyse aller bereitgestellten Dateien.
- **S – Strukturieren:** Zusammenführung, Aufbereitung und Darstellung der Analyseergebnisse.
- **E – Exportieren:** Bereitstellung der aufbereiteten Ergebnisse als PDF, DOC oder HTML.

---

## 2. Login und Sicherheit
- Mandantenbezogener Login mit drei Parametern:
  - **Mandantencode**
  - **Benutzername**
  - **Passwort**
- Session-Management:
  - Speicherung der Mandanteninformationen
  - Dynamisches Laden des **Mandanten-Logos** im UI
- Sicherheitslogik:
  - Tokens werden nur während der Session gespeichert.
  - Abmeldung löscht alle lokal gespeicherten Daten.

---

## 3. Navigation & Sidebar
Die Sidebar zeigt folgende Elemente:
- **Mandantenauswahl:** Zeigt aktiven Mandanten und Logo an.
- **Zeitraum:** Auswahl des Analysezeitraums.
- **Zollsatz, Pauschalbetrag, Bürgschaftsbeträge:** Anzeige aktueller Einstellungen.
- **Navigationselemente:**
  - Dashboard
  - BASE-Tabs (Bereitstellen, Analysieren, Strukturieren, Exportieren)
  - History
  - Einstellungen
  - Hilfe (mit integrierten Hilfetexten)

---

## 4. Workflows

### 4.1 Bereitstellen
- Auswahl des **Zeitraums** als erster Schritt.
- Möglichkeit, mehrere Dateien nacheinander hochzuladen:
  - Leitdatei (SumA)
  - EZA-Dateien (einzeln oder als Splits)
  - ZLVHV
  - NCTS
- Automatische Erkennung und Validierung der Dateitypen.
- Fortschrittsanzeige mit Farbcodierung (z. B. grün ✓, rot ✗).

### 4.2 Analysieren
- Startet automatisch nach erfolgreichem Upload.
- Schritte:
  - Einlesen der Daten
  - Validierung der Dateistruktur
  - Entfernen von Duplikaten
  - Zusammenführen mehrerer EZA-Dateien bei Bedarf
- Fortschrittsbalken für Live-Feedback.

### 4.3 Strukturieren
- Aufbereitung der Ergebnisse in drei Bereichen:
  - **Verarbeitungsprotokoll:** Log der Verarbeitungsschritte.
  - **Finanzdaten:** Übersicht aller Abgaben, Zölle, Pauschalen und Bürgschaftsdaten.
  - **Statistische Auswertung:** Übersicht nach Anmeldearten.

### 4.4 Exportieren
- Export der Ergebnisse in folgenden Formaten:
  - PDF (bevorzugt für Prüfer und Behörden)
  - HTML (für webbasierte Berichte)
  - DOCX (nur bei Bedarf für Nachbearbeitung)
- Automatischer Dateiname mit Mandant, Datum und Zeitraum.

---

## 5. Einstellungen
- Speicherung mandantenspezifischer Konfigurationen aus JSON-Dateien.
- Variablen pro Mandant:
  - Zollsatz
  - Pauschalbetrag
  - Bürgschaftsberechnung
  - Historienoptionen
- Validierung aller Eingaben direkt im UI.

---

## 6. History
- Anzeige aller bisherigen Verarbeitungen.
- Metadaten pro Lauf:
  - Datum
  - Zeitraum
  - Verarbeitete Dateien
  - Versionsstand
- Möglichkeit, ältere Analysen neu zu exportieren.

---

## 7. Hilfetexte (kompakt integriert)
- Alle Hilfetexte liegen als strukturierte JSON-Datei vor.
- Darstellung per Tooltip (Info-Icons) an relevanten Stellen:
  - Upload
  - Analyse
  - Strukturierung
  - Export
  - Einstellungen
- Tooltips sind kurz, verständlich und prozessbegleitend.

---

## 8. Design & UX-Anforderungen
- Klare, moderne Oberfläche.
- Sidebar mobil ausblendbar, auf Desktop dauerhaft sichtbar.
- Tabs für BASE-Workflow mit klarer Nutzerführung:
  - Automatisches Springen in den nächsten Tab nach Abschluss eines Schrittes.
  - Möglichkeit, jederzeit zurückzugehen, ohne Daten zu verlieren.
- Barrierefreiheit optional, nicht zwingend.

---

## 9. Technische Regeln
- Unterstützung für große Dateien (bis 400 MB pro Upload).
- Automatisches Zusammenführen von Split-Dateien.
- Nutzung moderner Frameworks:
  - Frontend: React, TailwindCSS
  - Backend: Python FastAPI oder Node.js
- Echtzeit-Verarbeitung mit Live-Feedback.

---

## 10. Muss- & Nice-to-Have-Funktionen
**Muss:**
- Mandanten-Login
- BASE-Workflow mit automatischer Navigation
- Fortschrittsanzeige in allen Tabs
- Validierung und Analyse großer Dateien
- Exporte als PDF & HTML
- Vollständige History

**Nice-to-Have:**
- Dashboard mit KPIs
- Vergleich alter Ergebnisse
- Adminbereich für Benutzerverwaltung

---

## 11. Anhang
- JSON-Dateien für Settings und History
- Beispiel-Datensatz für realistische Tests
- Kompakte Hilfetexte in JSON

## Erweiterte History-Logik (Meta-Definition)

Die History speichert alle relevanten Aktionen in der Anwendung zur Nachvollziehbarkeit. Sie dient sowohl der internen Protokollierung als auch für externe Audits.

### 1. Metastruktur
- **timestamp:** Zeitstempel der Aktion
- **user:** Benutzername
- **action:** Typ der Aktion (Login, Upload, Analyse, Struktur, Export, Settings-Änderung)
- **mandant:** Zugehöriger Mandant
- **date_range:** Ausgewählter Zeitraum
- **status:** Status der Aktion (Success, Warning, Error)
- **details:** Detailinformationen (z. B. verarbeitete Datensätze, generierte Dateien, Hinweise)

### 2. Funktionalität
- Automatische Speicherung bei jedem relevanten Schritt
- Chronologische Ansicht in der App im Tab *History*
- Filtermöglichkeiten nach Zeitraum, Mandant und Aktionstyp
- Export der Historie als CSV, JSON oder PDF

### 3. Anforderungen
- Performant auch bei >10.000 Einträgen
- Strikte Trennung der Daten pro Mandant
- Sicherung gegen Datenverlust bei Absturz

### 4. Nice-to-Have Features
- Suchfeld für Stichworte
- Quick-Links zur zugehörigen Analyse oder Export-Datei