# BürgControl BASE -- Technisches Handbuch (Cursor-ready, V1)

**Ziel:** Vorhandene Streamlit-App 1:1 in der Business-Logik reproduzieren, UI/UX modernisieren (BASE-Flow), Performance + DB-Persistenz sicherstellen.

**Sprache UI/Fehler:** Deutsch. **Architektur:** Python-Core + FastAPI + SQL (PostgreSQL/SQLite Dev), JSON als Fallback.

## 0. Goldene Regeln (fix)

1) **Business-Logik bleibt 1:1.** Ergebnisse (Excel-Reiter, Summen/KPIs, Zolldoku) müssen paritätisch sein.

2) **BASE-Navigation strikt:** Bereitstellen → Analysieren → Strukturieren → Exportieren. Tabs immer sichtbar; leere Tabs zeigen Hinweis.

3) **Quelle der Wahrheit:** DB-first (Settings, History, Mandant/Auth), **JSON-Fallback** bis Parität grün.

4) **Fehlerpolitik:** Harte Stops bei Pflicht-/Strukturfehlern; keine stillen Korrekturen außer explizit definierter (Duplikate MRN+Pos).

5) **Exporte:** Excel **3 Reiter** (Schema/Spalten/Reihenfolge fix), Zolldoku **PDF & HTML** (Word optional/Legacy; Template vorhanden).
[oai_citation:0‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

6) **Performance:** Chunked Upload, Streaming-Parser, Async-Jobs; 300--400 MB stabil.

7) **Labels/UX:** UI-Begriffe Deutsch; Tooltips aus JSON/DB; Primärfarbe per Hex konfigurierbar.

---

## 1. Eingangsdateien (Beispieldaten)

- **1 SumA_Leitdatei_Demo.xlsx** -- Leit-/Summenakte (Basis aller Bewegungen)

- **1.1 NCAR_Demo.xlsx** -- NCTS-Beendigungen: Transport-MRN, Packstücke (ersetzt „Menge")

- **2 Importverzollung_EZA_Demo.xlsx** -- EZA (Mehrdatei-Merge → 13 Spalten, Duplikate MRN+Pos raus)

- **3 Importverzollung_ZL_VAV_Demo.xlsx** -- Zolllager/Vereinfachte Verfahren

- **4 NCTS_Aus_Sich_Demo.xlsx** -- NCTS-Eröffnungen/Bezüge

- **5_Zieldatei_Verwahrliste.xlsx** -- Referenz-Zielstruktur (3 Reiter; 1:1 Schema)

- **config.json** -- Demo-Mandant/Zugang (u. a. Aktivierungscode, Test-Creds)
[oai_citation:1‡config.json](file-service://file-4fFXzQGJeqv2sWZVyEmHtd)

- **Hilfetexte_kompakt.json** -- kontextsensitive Hilfen/Notices je Tab/Widget (Login, Bereitstellen, Analyse, Strukturieren, Export etc.)
[oai_citation:2‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

- **settings_test_mandant_-_scills_gmbh.json** -- Mandanten-Settings (Zeitraum, Start-Bürgschaft, Ersatz-Zollsatz, Pauschale ...)
[oai_citation:3‡settings_test_mandant_-_scills_gmbh.json](file-service://file-6ie1JejgBbU2hdFFf2CUvK)

- **Zoll_Dokumentation_Template.docx** -- Seriendruck-Template für Zolldoku (Platzhalter/Sektionen definiert)
[oai_citation:4‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

---

## 2. Architektur (Kurz)

- **Backend:** FastAPI; Endpunkte für Upload, Process, Status, Export, History, Settings.

- **Frontend (Phase 1):** Streamlit aufgeräumt, Wizard-Flow; (Phase 2) Next.js/Tailwind/shadcn/ui.

- **DB:** PostgreSQL (Prod) / SQLite (Dev); JSON-Fallback (Dual-Write) für Settings/History/Tooltip-Cache.

- **Speicher:** Dateisystem (oder S3-kompatibel) -- Pfade in DB.

---

## 3. BASE-Flow (Wizard)

### 3.1 Bereitstellen (B)

1) Zeitraum wählen (Pflicht, Settings/Zeitraum vorfiltern).

2) Upload: **Leit + NCAR** → **EZA (multi)** → **ZL/VAV** → **NCTS**.

3) Sofortige Validierungen (Dateityp, Mindestspalten, Größenlimit, Zeitraumfilter).

**Hilfen & Notices:** Login-Hilfen, EZA-Reduzierung/13-Spalten, Warnungen bei fehlenden Spalten (z. B. „BEAnteil SumA") -- siehe Hilfetext-JSON.
[oai_citation:5‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

### 3.2 Analysieren (A)

- Auto-Wechsel nach erfolgreichem Upload.

- Pipeline (protokolliert): EZA_MERGE → EZA_13 → DEDUP(MRN+Pos) → MATCH_ATB → ERSATZ_ZOLLSATZ → PAUSCHALBETRAG → TAGESSALDEN/KPIs.

- Fortschritt + Log-Konsole; klare Fehler in Deutsch (harte Stops).

### 3.3 Strukturieren (S)

- Ergebnis-Kacheln: Verarbeitung pro Anmeldeart, Finanz- & Bürgschaftsstatistik, Filter.

- NCAR ergänzt Transport-MRN/Packstücke; ATB-Filter verfügbar. (Hilfetext-Sektionen zu „Geladene Daten", „NCAR", „Kalkulationsdateien" etc.)
[oai_citation:6‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

### 3.4 Exportieren (E)

- Kacheln: **Excel (3 Reiter), PDF, HTML**.

- Zolldoku aus Template generieren; Hinweis, wenn Template fehlt; Status-Meldungen „bereit/erzeugt/fehlgeschlagen".
[oai_citation:7‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)
[oai_citation:8‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

---

## 4. Business-Logik (fix)

- **EZA-Normalisierung:** Mehrdatei-Merge → **13 Kernspalten**; **Duplikate** per (MRN, Position) raus.

- **Matching:** ATB/Positions-Matching; Anmeldearten IMDC/WIDS/IPDC/NCDP; Ersatz-Zollsatz bei 0 %, Pauschale bei fehlenden Werten; Tagessalden.

- **NCAR-Erweiterung:** Packstücke ersetzen „Menge"; Transport-MRN wird verknüpft.

- **Paritätspflicht:** Excel-Schema & Summen/KPIs 1:1; Zolldoku-Platzhalter vollständig gefüllt.
[oai_citation:9‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

---

## 5. Einstellungen (Quelle der Wahrheit)

- **DB-Felder (Mindestsatz):** Zeitraum (`von`, `bis`), `start_buergschaft`, `ersatz_zollsatz`, `pauschale`, `buergschaft_erhoehung_*`.

- **Beispiel-Settings:** siehe `settings_test_mandant_-_scills_gmbh.json` (Konfiguration „2024_2025" mit Startbürgschaft, Ersatz-Zollsatz 12 %, Pauschale 10 000 €).
[oai_citation:10‡settings_test_mandant_-_scills_gmbh.json](file-service://file-6ie1JejgBbU2hdFFf2CUvK)

- **Fallback:** JSON bleibt lesbar/schreibbar, bis DB-Parität „grün".

---

## 6. Hilfetexte (kontextsensitiv)

- **Quelle:** `Hilfetexte_kompakt.json` -- enthält Hilfen/Notices je Tab/Widget (Login, Bereitstellen, Analyse, Strukturieren, Export, Einstellungen).

Beispiele: Login-Hilfen, EZA-13-Reduktion, NCAR-Hinweise, „Downloads bereit!", „Dokumentation erstellt", Warnungen/Success/Info.
[oai_citation:11‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

---

## 7. Exporte

- **Excel:** exakt **3 Reiter** (Ergebnis / Bewegungsdetails / Tageszusammenfassung).

- **Zolldoku (PDF/HTML):** generiert aus Template `Zoll_Dokumentation_Template.docx` mit Platzhaltern: Mandant, Zeitraum, Startbürgschaft, Verarbeitungsübersicht, Anmeldearten-Aufschlüsselung, Geschäftsregeln, Bürgschaftsberechnung, Summaries.
[oai_citation:12‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

- **Word (optional/Legacy):** nur wenn explizit gewünscht.

---

## 8. API-Skizze (FastAPI)

- `POST /auth/login` → JWT

- `GET /settings`, `PUT /settings` → DB + JSON-Fallback

- `POST /upload/leit-ncar`, `POST /upload/eza`, `POST /upload/zlvav`, `POST /upload/ncts` → Chunked

- `POST /process/start`, `GET /process/status?id=...` → Async-Jobs

- `GET /exports/{run_id}` → Links/Dateipfade

- `GET /history`, `GET /history/{run_id}` → Runs + KPIs

---

## 9. Datenbank (Minimalmodell)

- **mandants**(id, name, code, ...)

- **users**(id, mandant_id, login, hash, role)

- **settings**(mandant_id, zeitraum_von, zeitraum_bis, start_buergschaft, ersatz_zollsatz, pauschale, ...)

- **uploads**(run_id, typ, pfad, rows, checksum)

- **runs_history**(id, mandant_id, zeitraum, status, kpis_json, created_at)

- **tooltips**(key, scope, text_json) -- optionaler Sync aus `Hilfetexte_kompakt.json`
[oai_citation:13‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

---

## 10. Fehlerpolitik (DE)

- **Hart stoppen** bei: fehlende Pflichtspalten, falsches Schema, unplausible Summen.

- **Erlaubte auto-Korrektur:** Duplikate MRN+Pos entfernen (protokolliert).

- **Hinweise/Erfolge/Warnungen** gemäß Hilfetext-JSON (z. B. „✅ Downloads bereit!" / „⚠️ keine Daten im Zeitraum").
[oai_citation:14‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

---

## 11. Performance

- Chunked Upload (400 MB), Streaming-Parser für XLSX/CSV, Async-Jobs + Status-Polling.

- Zielzeiten: import + normalize + match **< 2--3 Min** bei 300--400 MB.

---

## 12. History

- Pro Lauf speichern: Zeitstempel, Mandant, Zeitraum, Dateinamen, KPIs, Status, Export-Links.

- Anzeige im „Verlauf"-Tab; Export History → Excel.

---

## 13. UI/Design

- **Sidebar:** BASE-Phasen (B/A/S/E) + „Verlauf", „Einstellungen", „Hilfe". Fortschritt: Grau (offen), Blau (aktiv), Grün (fertig).

- **Tabs:** im Main-Area BASE sichtbar, auch leer mit Hinweis.

- **Farbwelt:** Primärfarbe via Hex in Settings konfigurierbar.

- **Tooltips:** „?"-Icons; Inhalte aus Hilfetext-JSON.
[oai_citation:15‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

---

## 14. Paritäts-Checkliste (Go/No-Go)

- **Excel-Schema** exakt 1:1 (3 Reiter, Spalten, Reihenfolge).

- **Summen/KPIs** inkl. Tagessalden passen.

- **Zolldoku** füllt alle Platzhalter, keine leeren Felder.
[oai_citation:16‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

- **Settings/Zeitraum** korrekt angewandt (vgl. Beispiel-Settings).
[oai_citation:17‡settings_test_mandant_-_scills_gmbh.json](file-service://file-6ie1JejgBbU2hdFFf2CUvK)

- **Hilfen/Statusmeldungen** erscheinen an den richtigen Stellen.
[oai_citation:18‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)

---

## 15. Demo-Mandant/Logins (für Dev)

- Beispielwerte/Code/Logo in `config.json` (z. B. Demo-Code + Test-User).
[oai_citation:19‡config.json](file-service://file-4fFXzQGJeqv2sWZVyEmHtd)

---

## 16. Mapping-Wizard (V2-Stub)

- Drag&Drop Quelle→Ziel, KI-Vorschläge (Claude/GPT/Gemini), Profile pro Mandant speichern.

- In V1 **deaktiviert**, aber strukturell vorgesehen.

---

## 17. Deployment (Docker-First)

- **Services:** web(frontend), api(FastAPI), db(Postgres), storage(volumes).

- **Ohne Cloud-Zwang** beim Kunden betreibbar.

---

## 18. .env (Beispiel)

```env
DATABASE_URL=postgresql://bcb:change-me@db:5432/bcb
JWT_SECRET=change-me
PRIMARY_COLOR=#B00020
MAX_UPLOAD_MB=400
```

---

## 19. Tests (Minimal)

- Unit: Parser/Normalizer/Matcher

- Integration: Upload→Process→Export (Dry-Run mit Demo-Dateien)

- Parität: Excel-Schema & KPIs gegen Referenz (No-Go bei Abweichung)

---

## 20. Nächste Schritte

1) API-Gerüst + Upload-Pfade anlegen (Chunked).

2) EZA-Pipeline (Merge→13→Dedup) + ATB-Match implementieren.

3) NCAR-Einbindung (Packstücke/MRN).

4) Export (Excel 3 Reiter) + Zolldoku (Template) verknüpfen.
[oai_citation:20‡Zoll_Dokumentation_Template.docx](file-service://file-MXyqrB6LkWHuXmVC3gEQUY)

5) History/Settings DB + JSON-Fallback.
[oai_citation:21‡settings_test_mandant_-_scills_gmbh.json](file-service://file-6ie1JejgBbU2hdFFf2CUvK)

6) Tooltips/UI-Notices einhängen.
[oai_citation:22‡Hilfetexte_kompakt.json](file-service://file-H31Q2oD9MZGBkzfXWTsk9F)