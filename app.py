#!/usr/bin/env python3
"""Zoll-Dateiverwaltung PORT v5.0.1 - Reparierte Version"""

import streamlit as st
import pandas as pd
from datetime import timedelta, date, datetime
import io
import numpy as np
import re
from typing import List, Dict, Optional, Tuple
import json
import os
import traceback

# Konfiguration
st.set_page_config(
    page_title="Zoll-Dateiverwaltung PORT",
    page_icon="📦",
    layout="wide"
)

# ================== LOGIN UND AUTHENTIFIZIERUNG ==================

def load_config():
    """Lädt die Konfiguration aus externer Datei"""
    config_file = "config.json"
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
            return {
                "TEST-2024-DEMO-1234": {
                    "kunde": "Demo Kunde",
                    "logo": None,
                    "user": "test",
                    "pass": "test123"
                }
            }
    else:
        st.warning("⚠️ Keine config.json gefunden. Nutze Demo-Konfiguration.")
        return {
            "TEST-2024-DEMO-1234": {"kunde": "Test Mandant", "logo": None, "user": "test", "pass": "test123"}
        }

def validate_activation_code(code):
    """Validiert den Aktivierungscode"""
    config = load_config()
    return config.get(code)

def check_credentials(username, password, mandant_data):
    """Prüft Login-Credentials"""
    return (username == mandant_data.get('user') and 
            password == mandant_data.get('pass'))

def show_login():
    """Zeigt Login-Screen mit Aktivierungscode und Credentials"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
        st.session_state['mandant'] = None
        st.session_state['mandant_logo'] = None
        st.session_state['mandant_data'] = None
    
    if not st.session_state['authenticated']:
        st.markdown("""
        <style>
        .main > div {
            padding-top: 2rem;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.title("🔐 PORT v5.0.1 - Anmeldung")
            st.markdown("---")
            
            activation_code = st.text_input("Aktivierungscode", 
                                          placeholder="XXX-XXXX-XXXX-XXXX",
                                          help="Geben Sie Ihren Aktivierungscode ein")
            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("🔑 Anmelden", type="primary", use_container_width=True):
                    mandant_data = validate_activation_code(activation_code)
                    if mandant_data and check_credentials(username, password, mandant_data):
                        st.session_state['authenticated'] = True
                        st.session_state['mandant'] = mandant_data['kunde']
                        st.session_state['mandant_logo'] = mandant_data.get('logo')
                        st.session_state['mandant_data'] = mandant_data
                        st.success("✅ Anmeldung erfolgreich!")
                        st.rerun()
                    else:
                        st.error("❌ Ungültige Anmeldedaten!")
            
            with col_btn2:
                if st.button("ℹ️ Demo-Zugänge", use_container_width=True):
                    st.info("""
                    **Demo-Zugänge:**
                    - Code: `TEST-2024-DEMO-1234`
                    - User: `test` / Pass: `test123`
                    """)
        
        st.stop()

# ================== SETTINGS MANAGEMENT ==================

def load_settings():
    """Lädt mandantenspezifische Settings"""
    if 'mandant' not in st.session_state:
        return {}
    
    settings_file = f"settings_{st.session_state['mandant'].lower().replace(' ', '_')}.json"
    
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_settings(settings):
    """Speichert mandantenspezifische Settings"""
    if 'mandant' not in st.session_state:
        return
    
    settings_file = f"settings_{st.session_state['mandant'].lower().replace(' ', '_')}.json"
    
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

def check_initial_setup():
    """Prüft ob Ersteinrichtung nötig - KORRIGIERTE VERSION"""
    # WICHTIG: Prüfe zuerst ob wir schon in der Verarbeitung sind
    if any([
        'df_leit' in st.session_state and st.session_state.df_leit is not None,
        'processing_active' in st.session_state and st.session_state.processing_active,
        'datum_filter_confirmed' in st.session_state and st.session_state.datum_filter_confirmed
    ]):
        # Wir sind schon in der Verarbeitung - keine Ersteinrichtung!
        return True
    
    # Lade Settings
    settings = load_settings()
    
    # Wenn keine Settings vorhanden, zeige Ersteinrichtung
    if not settings or 'current_config' not in settings:
        show_initial_setup()
        return False
    
    # Lade aktuelle Konfiguration in Session State
    current_config_name = settings.get('current_config')
    if current_config_name and current_config_name in settings:
        config = settings[current_config_name]
        
        # Sichere Werte mit Defaults laden
        try:
            # Nur setzen wenn noch nicht vorhanden (verhindert Überschreiben während Verarbeitung)
            if 'von_datum' not in st.session_state:
                st.session_state['von_datum'] = datetime.strptime(config.get('von', '01.05.2024'), '%d.%m.%Y').date()
            if 'bis_datum' not in st.session_state:
                st.session_state['bis_datum'] = datetime.strptime(config.get('bis', '30.04.2025'), '%d.%m.%Y').date()
            if 'startbuergschaft' not in st.session_state:
                st.session_state['startbuergschaft'] = float(config.get('buergschaft', 0))
            if 'zollsatz_ersatz' not in st.session_state:
                st.session_state['zollsatz_ersatz'] = float(config.get('ersatz_zollsatz', 12.0)) / 100
            if 'pauschalbetrag' not in st.session_state:
                st.session_state['pauschalbetrag'] = float(config.get('pauschale', 10000))
            
            # Bürgschaftserhöhung
            if 'buergschaft_erhöhung_aktiv' not in st.session_state:
                st.session_state['buergschaft_erhöhung_aktiv'] = config.get('buergschaft_erhoehung_aktiv', False)
            if 'buergschaft_erhöhung_datum' not in st.session_state:
                if config.get('buergschaft_erhoehung_datum'):
                    try:
                        st.session_state['buergschaft_erhöhung_datum'] = datetime.strptime(config['buergschaft_erhoehung_datum'], '%d.%m.%Y').date()
                    except:
                        st.session_state['buergschaft_erhöhung_datum'] = date(2025, 2, 4)
                else:
                    st.session_state['buergschaft_erhöhung_datum'] = date(2025, 2, 4)
            if 'buergschaft_erhöhung_betrag' not in st.session_state:
                st.session_state['buergschaft_erhöhung_betrag'] = float(config.get('buergschaft_erhoehung_betrag', 1500000.0))
                
        except Exception as e:
            st.error(f"❌ Fehler beim Laden der Konfiguration: {e}")
            show_initial_setup()
            return False
    
    return True

def show_initial_setup():
    """Zeigt Ersteinrichtungs-Dialog"""
    st.title("⚙️ Ersteinrichtung")
    st.info("Bitte konfigurieren Sie die Grundeinstellungen für Ihren Mandanten.")
    
    existing_settings = load_settings()
    has_existing = bool(existing_settings)
    
    with st.form("initial_setup"):
        st.subheader("Bewilligungszeitraum")
        
        col1, col2 = st.columns(2)
        with col1:
            von_datum = st.date_input("Von", value=date.today() if not has_existing else date(2024, 5, 1))
        with col2:
            default_bis = date.today().replace(year=date.today().year + 1) if not has_existing else date(2025, 4, 30)
            bis_datum = st.date_input("Bis", value=default_bis)
        
        st.subheader("Finanzielle Parameter")
        
        col3, col4 = st.columns(2)
        with col3:
            buergschaft = st.number_input(
                "Bürgschafts-Startsumme (€)",
                min_value=0.0,
                value=0.0,
                step=100000.0,
                format="%.2f"
            )
            ersatz_zollsatz = st.number_input(
                "Ersatz-Zollsatz bei 0% (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0 if not has_existing else 12.0,
                step=0.1
            )
        
        with col4:
            pauschale = st.number_input(
                "Pauschalbetrag (€)",
                min_value=0.0,
                value=0.0 if not has_existing else 10000.0,
                step=1000.0,
                format="%.2f"
            )
        
        st.subheader("Bürgschaftserhöhung (optional)")
        buergschaft_erhoehung_aktiv = st.checkbox("Bürgschaftserhöhung aktivieren", value=False)
        
        col5, col6 = st.columns(2)
        with col5:
            buergschaft_erhoehung_datum = st.date_input(
                "Datum der Erhöhung",
                value=date.today(),
                disabled=not buergschaft_erhoehung_aktiv
            )
        with col6:
            buergschaft_erhoehung_betrag = st.number_input(
                "Erhöhungsbetrag (€)",
                min_value=0.0,
                value=0.0,
                step=100000.0,
                format="%.2f",
                disabled=not buergschaft_erhoehung_aktiv
            )
        
        if st.form_submit_button("💾 Einstellungen speichern", type="primary"):
            config_name = f"{von_datum.year}_{bis_datum.year}"
            
            settings = {
                config_name: {
                    "von": von_datum.strftime('%d.%m.%Y'),
                    "bis": bis_datum.strftime('%d.%m.%Y'),
                    "buergschaft": buergschaft,
                    "ersatz_zollsatz": ersatz_zollsatz,
                    "pauschale": pauschale,
                    "buergschaft_erhoehung_aktiv": buergschaft_erhoehung_aktiv,
                    "buergschaft_erhoehung_datum": buergschaft_erhoehung_datum.strftime('%d.%m.%Y'),
                    "buergschaft_erhoehung_betrag": buergschaft_erhoehung_betrag
                },
                "current_config": config_name
            }
            
            save_settings(settings)
            st.success("✅ Einstellungen gespeichert!")
            st.rerun()

def show_settings_page():
    """Zeigt Settings-Seite im Hauptbereich"""
    st.title("⚙️ Einstellungen")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← Zurück zur Verarbeitung", type="secondary"):
            st.session_state['show_settings'] = False
            st.rerun()
    
    settings = load_settings()
    current_config = settings.get(settings.get('current_config', ''), {})
    
    with st.form("settings_change"):
        st.subheader("Mandanten-Einstellungen bearbeiten")
        
        st.markdown("### Bewilligungszeitraum")
        col1, col2 = st.columns(2)
        with col1:
            von_datum = st.date_input(
                "Von", 
                value=datetime.strptime(current_config.get('von', '01.05.2024'), '%d.%m.%Y').date()
            )
        with col2:
            bis_datum = st.date_input(
                "Bis", 
                value=datetime.strptime(current_config.get('bis', '30.04.2025'), '%d.%m.%Y').date()
            )
        
        st.markdown("### Finanzielle Parameter")
        col3, col4 = st.columns(2)
        with col3:
            buergschaft = st.number_input(
                "Bürgschafts-Startsumme (€)",
                value=float(current_config.get('buergschaft', 0)),
                step=100000.0,
                format="%.2f"
            )
            ersatz_zollsatz = st.number_input(
                "Ersatz-Zollsatz bei 0% (%)",
                value=float(current_config.get('ersatz_zollsatz', 0)),
                step=0.1
            )
        
        with col4:
            pauschale = st.number_input(
                "Pauschalbetrag (€)",
                value=float(current_config.get('pauschale', 0)),
                step=1000.0,
                format="%.2f"
            )
        
        st.markdown("### Bürgschaftserhöhung (optional)")
        buergschaft_erhoehung_aktiv = st.checkbox(
            "Bürgschaftserhöhung aktivieren", 
            value=current_config.get('buergschaft_erhoehung_aktiv', False)
        )
        
        col5, col6 = st.columns(2)
        with col5:
            if current_config.get('buergschaft_erhoehung_datum'):
                datum_value = datetime.strptime(current_config['buergschaft_erhoehung_datum'], '%d.%m.%Y').date()
            else:
                datum_value = date.today()
                
            buergschaft_erhoehung_datum = st.date_input(
                "Datum der Erhöhung",
                value=datum_value,
                disabled=not buergschaft_erhoehung_aktiv
            )
        with col6:
            buergschaft_erhoehung_betrag = st.number_input(
                "Erhöhungsbetrag (€)",
                value=float(current_config.get('buergschaft_erhoehung_betrag', 0)),
                step=100000.0,
                format="%.2f",
                disabled=not buergschaft_erhoehung_aktiv
            )
        
        submitted = st.form_submit_button("💾 Einstellungen speichern", type="primary", use_container_width=True)
        
    if submitted:
        config_name = f"{von_datum.year}_{bis_datum.year}"
        settings[config_name] = {
            "von": von_datum.strftime('%d.%m.%Y'),
            "bis": bis_datum.strftime('%d.%m.%Y'),
            "buergschaft": buergschaft,
            "ersatz_zollsatz": ersatz_zollsatz,
            "pauschale": pauschale,
            "buergschaft_erhoehung_aktiv": buergschaft_erhoehung_aktiv,
            "buergschaft_erhoehung_datum": buergschaft_erhoehung_datum.strftime('%d.%m.%Y'),
            "buergschaft_erhoehung_betrag": buergschaft_erhoehung_betrag
        }
        settings['current_config'] = config_name
        save_settings(settings)
        
        # Session State aktualisieren
        st.session_state['von_datum'] = von_datum
        st.session_state['bis_datum'] = bis_datum
        st.session_state['startbuergschaft'] = float(buergschaft)
        st.session_state['zollsatz_ersatz'] = float(ersatz_zollsatz) / 100
        st.session_state['pauschalbetrag'] = float(pauschale)
        st.session_state['buergschaft_erhöhung_aktiv'] = buergschaft_erhoehung_aktiv
        st.session_state['buergschaft_erhöhung_datum'] = buergschaft_erhoehung_datum
        st.session_state['buergschaft_erhöhung_betrag'] = float(buergschaft_erhoehung_betrag)
        
        st.success("✅ Einstellungen wurden gespeichert!")
        st.balloons()
        st.info("👆 Klicken Sie auf 'Zurück zur Verarbeitung' um fortzufahren.")

# ================== KONSTANTEN UND KONFIGURATION ==================

EXAKTE_EZA_SPALTEN = [
    "Teilnehmer",
    "Verfahren", 
    "Bezugsnummer/LRN",
    "Überlassungsdatum",
    "Registriernummer/MRN",
    "PositionNo",
    "Zollwert",
    "AbgabeZoll",
    "AbgabeZollsatz",
    "Eustwert",
    "AbgabeEust",
    "Warentarifnummer",
    "BEAnteil SumA"
]

ANMELDEART_CONFIG = {
    'IMDC': {
        'unique_field': 'weitere',
        'import_source': 'df_import_eza',
        'match_field': 'import_eza_col',
        'pos_field': 'pos_field_eza',
        'has_menge': True,
        'needs_import': True,
        'process_all_rows': True
    },
    'WIDS': {
        'unique_field': 'weitere',
        'import_source': 'df_import_zl',
        'match_field': 'import_zl_col',
        'pos_field': 'pos_field_zl',
        'has_menge': False,
        'needs_import': True,
        'process_all_rows': True
    },
    'IPDC': {
        'unique_field': 'weitere',
        'needs_import': False,
        'process_all_rows': True
    },
    'NCDP': {
        'unique_field': 'reg',
        'import_source': 'df_ncts',
        'match_field': 'ncts_mrn_col',
        'needs_import': True,
        'process_all_rows': True
    },
    'NCAR': {
        'unique_field': 'reg',
        'needs_import': False,
        'process_all_rows': True
    }
}

# ================== INITIALISIERUNG ==================

def init_session_state():
    """Initialisiert den Session State"""
    defaults = {
        'df_leit': None,
        'df_import_eza': None,
        'df_import_zl': None,
        'df_ncts': None,
        'df_ncar': None,
        'stats': {},
        'leere_verarbeiten': True,
        'eust_satz': 0.19,
        'verwahrungsfrist_tage': 90,
        'wids_aggregation': 'Position mit höchstem Zollwert',
        'leere_anmeldeart_option': 'Alle Zeilen (wie andere Anmeldearten)',
        'zollsatz_null_ersetzen': True,
        'datum_filter_confirmed': False,
        'eza_auto_reduce': True,
        'ncar_enabled': True,
        'atb_filtered_count': 0,
        'show_settings': False,
        'processing_active': False,  # Flag für aktive Verarbeitung
        'processing_error': None  # NEU: Speichert Fehler während Verarbeitung
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ================== UTILITY FUNKTIONEN ==================

def safe_strftime(dt) -> str:
    """Konvertiert ein Datum sicher in einen String."""
    try:
        return pd.to_datetime(dt).strftime('%d.%m.%Y') if pd.notnull(dt) else ''
    except (ValueError, TypeError):
        return ''

def safe_date_value(dt):
    """Konvertiert ein Datum sicher in ein Date-Objekt für Excel."""
    try:
        if pd.notnull(dt):
            parsed = pd.to_datetime(dt)
            return parsed.date() if hasattr(parsed, 'date') else parsed
        return None
    except (ValueError, TypeError):
        return None

def safe_numeric(value, default=0):
    """Konvertiert einen Wert sicher in eine Zahl"""
    result = pd.to_numeric(value, errors='coerce')
    return default if pd.isna(result) else float(result)

def safe_numeric_series(series, default=0):
    """Konvertiert eine ganze Series sicher in numerische Werte"""
    return pd.to_numeric(series, errors='coerce').fillna(default)

def process_suma_position(row_data, suma_pos_col):
    """Verarbeitet SUMA-Position einheitlich"""
    if suma_pos_col and suma_pos_col in row_data:
        suma_value = row_data[suma_pos_col]
        return pd.to_numeric(suma_value, errors='ignore') if pd.notna(suma_value) else ''
    return ''

def prepare_dataframe_for_sorting(df):
    """Bereitet DataFrame für Standard-Sortierung vor"""
    df = df.copy()
    df['_gestell_date'] = df['Gestellungsdatum'].apply(parse_german_date)
    df['_suma_pos_numeric'] = pd.to_numeric(df['SUMA-Position'], errors='coerce').fillna(999999)
    return df

def sort_dataframe_standard(df):
    """Führt Standard-Sortierung durch und entfernt temporäre Spalten"""
    df_sorted = df.sort_values(
        by=['_gestell_date', 'ATB-Nummer', '_suma_pos_numeric'],
        ascending=[True, True, True]
    )
    columns_to_drop = ['_gestell_date', '_suma_pos_numeric']
    columns_to_drop = [col for col in columns_to_drop if col in df_sorted.columns]
    if columns_to_drop:
        df_sorted = df_sorted.drop(columns=columns_to_drop)
    return df_sorted

def find_col(df: pd.DataFrame, candidates: List[str], required: bool = True) -> Optional[str]:
    """Findet die erste passende Spalte aus einer Liste von möglichen Namen."""
    for c in candidates:
        if c in df.columns:
            return c
    
    if required:
        st.error(f"❌ Keine der Spalten gefunden: {candidates}")
        raise ValueError(f"Pflichtfeld fehlt: {candidates}")
    return None

def clean_mrn(mrn_value) -> str:
    """Bereinigt MRN-Werte für den Vergleich"""
    if pd.isna(mrn_value):
        return ''
    cleaned = str(mrn_value).strip()
    if '.' in cleaned:
        cleaned = cleaned.split('.')[0]
    return cleaned

def has_atb_in_weitere_folge(leit_row, field_mappings) -> bool:
    """Prüft ob Weitere Registriernummer Folgeverfahren mit ATB beginnt"""
    weitere_folge = leit_row.get(field_mappings['leit_col_weitere'], '')
    return str(weitere_folge).strip().startswith('ATB')

def parse_german_date(date_str):
    """Konvertiert deutsches Datum (DD.MM.YYYY) in Date-Objekt"""
    if pd.isna(date_str) or date_str == '' or date_str is None:
        return None
    
    try:
        if isinstance(date_str, (datetime, date)):
            return date_str.date() if isinstance(date_str, datetime) else date_str
        
        if isinstance(date_str, str):
            date_str = date_str.strip()
            if '.' in date_str:
                parts = date_str.split('.')
                if len(parts) == 3:
                    try:
                        day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                        if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                            return datetime(year, month, day).date()
                    except ValueError:
                        pass
            
            try:
                parsed = pd.to_datetime(date_str, format='%d.%m.%Y')
                return parsed.date()
            except:
                pass
    except:
        pass
    
    return None

def calculate_warehouse_dates(gestell, beendigung, frist_tage=90):
    """Zentrale Datumberechnung für alle Anmeldearten"""
    try:
        dt1 = pd.to_datetime(gestell)
        dt2 = pd.to_datetime(beendigung)
        verfrist_date = (dt1 + timedelta(days=frist_tage)).date()
        return {
            'verwahrungsfrist': (dt1 + timedelta(days=frist_tage)).strftime('%d.%m.%Y'),
            'verwahrungsfrist_date': verfrist_date,
            'verwahrungsdauer': (dt2 - dt1).days + 1
        }
    except:
        return {'verwahrungsfrist': '', 'verwahrungsfrist_date': None, 'verwahrungsdauer': 0}

def validate_dataframe(df: pd.DataFrame, required_cols: List[List[str]], df_name: str) -> bool:
    """Validiert, ob alle erforderlichen Spalten vorhanden sind."""
    missing = []
    for col_candidates in required_cols:
        if not any(c in df.columns for c in col_candidates):
            missing.append(col_candidates)
    
    if missing:
        st.error(f"❌ Fehlende Spalten in {df_name}:")
        for cols in missing:
            st.error(f"   - Eine dieser Spalten wird benötigt: {cols}")
        raise ValueError(f"Pflichtfelder fehlen in {df_name}")
    return True

def calculate_statistics(df: pd.DataFrame, anmeldeart_col: str) -> Dict[str, int]:
    """Berechnet Statistiken für die Anzeige."""
    stats = {}
    if anmeldeart_col in df.columns:
        alle_anmeldearten = ['IMDC', 'IPDC', 'NCDP', 'WIDS', 'SUSP', 'SUDC', 'SUCO', 'SUCF', 'APDC', 'AVDC', 'NCAR']
        counts = df[anmeldeart_col].value_counts()
        
        for art in alle_anmeldearten:
            stats[f"{art}"] = int(counts.get(art, 0))
        
        stats["(leer)"] = int(df[anmeldeart_col].isna().sum())
        stats["Gesamt"] = len(df)
    return stats

def apply_zoelle_rule(results):
    """Wendet die Regel an: Mindestabgaben und Zölle = Gesamtabgaben"""
    pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
    
    for row in results:
        # Fall 1: Gesamtabgaben zwischen 0 und 1€ → immer 1€
        if row['Gesamtabgaben'] > 0 and row['Gesamtabgaben'] < 1.0:
            row['Gesamtabgaben'] = 1.0
        
        # Fall 2: Gesamtabgaben = 0
        elif row['Gesamtabgaben'] == 0:
            if row['Zollwert (total)'] > 0:
                row['Gesamtabgaben'] = 1.0
            else:
                row['Gesamtabgaben'] = pauschalbetrag
        
        # Zölle = Gesamtabgaben (immer)
        row['Zölle (total)'] = row['Gesamtabgaben']
    
    return results

def is_dataframe_valid(df):
    """Prüft ob DataFrame gültig und nicht leer ist"""
    return df is not None and isinstance(df, pd.DataFrame) and not df.empty

def clean_dataframe_for_export(df):
    """Bereinigt DataFrame von NaN-Werten für Excel-Export"""
    df_clean = df.copy()
    
    numeric_columns = ['Menge', 'Zollwert (total)', 'Drittlandzollsatz', 
                      'Zölle (total)', 'EUSt', 'Gesamtabgaben']
    for col in numeric_columns:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
    
    text_columns = ['Referenznummer', 'MRN-Nummer Eingang', 'ATB-Nummer', 
                    'Erledigung mit', 'Anmeldeart']
    for col in text_columns:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('').astype(str)
    
    if 'SUMA-Position' in df_clean.columns:
        df_clean['SUMA-Position'] = df_clean['SUMA-Position'].apply(
            lambda x: pd.to_numeric(x, errors='ignore') if x != '' else ''
        )
    
    if 'Pos' in df_clean.columns:
        df_clean['Pos'] = df_clean['Pos'].apply(
            lambda x: pd.to_numeric(x, errors='ignore') 
            if x not in ['KEIN MATCH', 'Pauschale', ''] and not str(x).startswith('SUMME') and ' von ' not in str(x) else x
        )
    
    if 'Codenummer' in df_clean.columns:
        df_clean['Codenummer'] = df_clean['Codenummer'].apply(
            lambda x: pd.to_numeric(x, errors='ignore') if x != '' else ''
        )
    
    if 'Verwahrungsdauer' in df_clean.columns:
        df_clean['Verwahrungsdauer'] = pd.to_numeric(
            df_clean['Verwahrungsdauer'], errors='coerce'
        ).fillna(0).astype(int)
    
    return df_clean

# ================== GEMEINSAME VERARBEITUNGSFUNKTIONEN ==================

def create_common_data(leit_row, gestell_col, dates_info):
    """Erstellt gemeinsame Daten für alle Anmeldearten"""
    return {
        'Referenznummer': str(leit_row.get('Bezugsnummer/LRN SumA', '')),
        'MRN-Nummer Eingang': str(leit_row.get('Registriernummer/MRN SumA', '')),
        'ATB-Nummer': str(leit_row.get('Registriernummer/MRN SumA', '')),
        'SUMA-Position': '',
        'Gestellungsdatum': safe_date_value(leit_row.get(gestell_col, '')),
        'Beendigung der Verwahrung': safe_date_value(leit_row.get('Datum Ende - CUSFIN', '')),
        'Verwahrungsfrist': dates_info.get('verwahrungsfrist_date', None),
        'Verwahrungsdauer': dates_info.get('verwahrungsdauer', 0),
        'Erledigung mit': ''
    }

def create_no_match_row(common_data, leit_row, anmeldeart, suma_pos_col):
    """Einheitliche No-Match Zeile für alle Anmeldearten"""
    common_data['SUMA-Position'] = process_suma_position(leit_row, suma_pos_col)
    
    pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
    
    if anmeldeart == 'NCDP':
        menge = 0
    elif anmeldeart == 'WIDS':
        menge = ''
    else:
        menge = 0
    
    return {
        **common_data,
        'Pos': 'KEIN MATCH',
        'Codenummer': '',
        'Menge': menge,
        'Zollwert (total)': 0.0,
        'Drittlandzollsatz': 0.0,
        'Zölle (total)': 0.0,
        'EUSt': 0.0,
        'Gesamtabgaben': pauschalbetrag,
        'Anmeldeart': anmeldeart
    }

def find_import_matches(unique_id, fallback_id, import_df, match_col):
    """Sucht Matches in Import-Datei mit Fallback"""
    matches = import_df[import_df[match_col] == unique_id]
    used_id = unique_id
    
    if matches.empty and fallback_id != unique_id:
        matches = import_df[import_df[match_col] == fallback_id]
        used_id = fallback_id
    
    return matches, used_id

# ================== SPEZIFISCHE BERECHNUNGSFUNKTIONEN ==================

def process_imdc_row(import_row, common_data, leit_row, pos_field, suma_pos_col):
    """Verarbeitet eine IMDC-Zeile"""
    zollwert = safe_numeric(import_row.get('Zollwert', 0))
    drittlandzollsatz = safe_numeric(import_row.get('AbgabeZollsatz', 0))
    
    if st.session_state.get('zollsatz_null_ersetzen', True) and drittlandzollsatz == 0 and zollwert > 0:
        drittlandzollsatz = st.session_state.get('zollsatz_ersatz', 0.12) * 100
    
    zoelle_total = round(zollwert * drittlandzollsatz / 100, 2)
    eust = round((zollwert + zoelle_total) * st.session_state.get('eust_satz', 0.19), 2)
    
    pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
    gesamtabgaben = zoelle_total if zollwert > 0 else pauschalbetrag
    
    common_data['ATB-Nummer'] = leit_row['Registriernummer/MRN SumA']
    common_data['SUMA-Position'] = process_suma_position(leit_row, suma_pos_col)
    
    menge_value = safe_numeric(import_row.get('Menge', 0))
    pos_value = import_row.get(pos_field, '')
    pos_numeric = pd.to_numeric(pos_value, errors='ignore') if pos_value else ''
    codenummer = import_row.get('Warentarifnummer', '')
    codenummer_numeric = pd.to_numeric(codenummer, errors='ignore') if codenummer else ''
    
    return {
        **common_data,
        'Pos': pos_numeric,
        'Codenummer': codenummer_numeric,
        'Menge': menge_value,
        'Zollwert (total)': zollwert,
        'Drittlandzollsatz': drittlandzollsatz,
        'Zölle (total)': zoelle_total,
        'EUSt': eust,
        'Gesamtabgaben': gesamtabgaben,
        'Anmeldeart': 'IMDC'
    }

def find_zl_value(row: pd.Series, field_type: str):
    """Findet Werte in der ZL-Datei mit verschiedenen Schreibweisen."""
    field_mapping = {
        'zollabgabe': ['Vorraussichtliche Zollabgabe', 'Voraussichtliche Zollabgabe'],
        'zollsatz': ['Vorraussichtliche Zollsatzabgabe', 'Voraussichtliche Zollsatzabgabe'],
        'dv1': ['DV1UmgerechnerterRechnungsbetrag', 'DV1 Umgerechneter Rechnungsbetrag']
    }
    
    candidates = field_mapping.get(field_type, [])
    for col in candidates:
        if col in row and pd.notna(row[col]):
            return safe_numeric(row[col])
    return 0.0

def calculate_wids_zollwert(row):
    """Berechnet den Zollwert für eine WIDS-Position"""
    zollabgabe = find_zl_value(row, 'zollabgabe')
    zollsatz = find_zl_value(row, 'zollsatz')
    dv1_betrag = find_zl_value(row, 'dv1')
    
    if zollsatz == 0:
        return dv1_betrag
    else:
        return round(zollabgabe / (zollsatz / 100), 2) if zollsatz > 0 else 0

def process_wids_row(import_row, common_data, leit_row, pos_field, suma_pos_col):
    """Verarbeitet eine WIDS-Zeile"""
    zollabgabe = find_zl_value(import_row, 'zollabgabe')
    zollsatz = find_zl_value(import_row, 'zollsatz')
    dv1_betrag = find_zl_value(import_row, 'dv1')
    
    if zollsatz == 0:
        zollwert = dv1_betrag
    else:
        zollwert = round(zollabgabe / (zollsatz / 100), 2) if zollsatz > 0 else 0
    
    if st.session_state.get('zollsatz_null_ersetzen', True) and zollsatz == 0 and zollwert > 0:
        zollsatz = st.session_state.get('zollsatz_ersatz', 0.12) * 100
        zollabgabe = round(zollwert * zollsatz / 100, 2)
    
    eust = round((zollwert + zollabgabe) * st.session_state.get('eust_satz', 0.19), 2)
    
    pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
    gesamtabgaben = zollabgabe if zollwert > 0 else pauschalbetrag
    
    common_data['SUMA-Position'] = process_suma_position(leit_row, suma_pos_col)
    
    pos_value = import_row.get(pos_field, '')
    pos_numeric = pd.to_numeric(pos_value, errors='ignore') if pos_value else ''
    codenummer = import_row.get('Warentarifnummer', '')
    codenummer_numeric = pd.to_numeric(codenummer, errors='ignore') if codenummer else ''
    
    return {
        **common_data,
        'Pos': pos_numeric,
        'Codenummer': codenummer_numeric,
        'Menge': '',
        'Zollwert (total)': zollwert,
        'Drittlandzollsatz': zollsatz,
        'Zölle (total)': zollabgabe,
        'EUSt': eust,
        'Gesamtabgaben': gesamtabgaben,
        'Anmeldeart': 'WIDS'
    }

def process_ipdc_row(common_data, leit_row, suma_pos_col):
    """Verarbeitet eine IPDC-Zeile"""
    zollwert_folge = safe_numeric(leit_row.get('Zollwert Folgeverfahren', 0))
    zollbetrag_folge = safe_numeric(leit_row.get('Zollbetrag Folgeverfahren', 0))
    
    if zollwert_folge > 0:
        drittlandzollsatz = round((zollbetrag_folge / zollwert_folge) * 100, 1)
    else:
        drittlandzollsatz = 0.0
    
    if st.session_state.get('zollsatz_null_ersetzen', True) and drittlandzollsatz == 0 and zollwert_folge > 0:
        drittlandzollsatz = st.session_state.get('zollsatz_ersatz', 0.12) * 100
        zollbetrag_folge = round(zollwert_folge * drittlandzollsatz / 100, 2)
    
    eust = round((zollwert_folge + zollbetrag_folge) * st.session_state.get('eust_satz', 0.19), 2)
    
    pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
    gesamtabgaben = zollbetrag_folge if zollwert_folge > 0 else pauschalbetrag
    
    if suma_pos_col and suma_pos_col in leit_row:
        suma_value = leit_row[suma_pos_col]
        common_data['SUMA-Position'] = pd.to_numeric(suma_value, errors='ignore') if pd.notna(suma_value) else ''
    else:
        common_data['SUMA-Position'] = ''
    
    common_data['Erledigung mit'] = common_data['Erledigung mit'] or str(leit_row.get('Weitere Registriernummer Folgeverfahren', ''))
    
    return {
        **common_data,
        'Pos': '',
        'Codenummer': '',
        'Menge': '',
        'Zollwert (total)': zollwert_folge,
        'Drittlandzollsatz': drittlandzollsatz,
        'Zölle (total)': zollbetrag_folge,
        'EUSt': eust,
        'Gesamtabgaben': gesamtabgaben,
        'Anmeldeart': 'IPDC'
    }

def extract_sicherheitsbetrag(sicherheit_data) -> float:
    """Extrahiert den Sicherheitsbetrag aus den NCTS-Sicherheitsdaten."""
    try:
        if isinstance(sicherheit_data, dict) and 'Sicherheitsleistungen' in sicherheit_data:
            leistungen = str(sicherheit_data['Sicherheitsleistungen'])
            match = re.search(r'Sicherheit:\s*([\d.,]+)', leistungen)
            if match:
                return float(match.group(1).replace(',', '.'))
        elif isinstance(sicherheit_data, str):
            match = re.search(r'Sicherheit:\s*([\d.,]+)', sicherheit_data)
            if match:
                return float(match.group(1).replace(',', '.'))
    except Exception as e:
        st.warning(f"⚠️ Fehler beim Extrahieren des Sicherheitsbetrags: {e}")
    return 0.0

def process_ncdp_row(common_data, leit_row, ncts_row, suma_pos_col):
    """Verarbeitet eine NCDP-Zeile"""
    sicherheitsbetrag = safe_numeric(extract_sicherheitsbetrag(ncts_row.get('Sicherheit', {})))
    
    common_data['SUMA-Position'] = process_suma_position(leit_row, suma_pos_col)
    
    return {
        **common_data,
        'Pos': '',
        'Codenummer': '',
        'Menge': 0,
        'Zollwert (total)': 0.0,
        'Drittlandzollsatz': 0.0,
        'Zölle (total)': 0.0,
        'EUSt': 0.0,
        'Gesamtabgaben': round(sicherheitsbetrag, 2),
        'Anmeldeart': 'NCDP'
    }

# ================== BE-ANTEIL VERARBEITUNG ==================

def process_eza_be_anteil(df_import_eza):
    """Verarbeitet die BE Anteil SumA Spalte und multipliziert Zeilen entsprechend"""
    if len(df_import_eza.columns) < 13:
        st.warning("⚠️ Spalte 'BEAnteil SumA' nicht gefunden. Fahre ohne Verarbeitung fort.")
        return df_import_eza
    
    be_anteil_col = df_import_eza.columns[12]
    processed_rows = []
    
    for idx, row in df_import_eza.iterrows():
        be_anteil_value = row[be_anteil_col]
        
        if pd.isna(be_anteil_value) or str(be_anteil_value).strip() == '':
            new_row = row.copy()
            new_row['ATBnummer'] = ''
            new_row['Position'] = ''
            processed_rows.append(new_row)
        else:
            be_anteil_str = str(be_anteil_value).strip()
            atb_entries = be_anteil_str.split(',')
            
            for entry in atb_entries:
                entry = entry.strip()
                
                if ' - POS ' in entry:
                    try:
                        atb_part = entry.split(' - POS ')[0].strip()
                        pos_part = entry.split(' - POS ')[1].strip()
                        
                        new_row = row.copy()
                        new_row['ATBnummer'] = atb_part.strip()
                        new_row['Position'] = pos_part
                        processed_rows.append(new_row)
                    except:
                        st.warning(f"⚠️ Konnte BE-Anteil nicht parsen: {entry}")
                        new_row = row.copy()
                        new_row['ATBnummer'] = ''
                        new_row['Position'] = ''
                        processed_rows.append(new_row)
                else:
                    new_row = row.copy()
                    new_row['ATBnummer'] = ''
                    new_row['Position'] = ''
                    processed_rows.append(new_row)
    
    return pd.DataFrame(processed_rows)

# ================== GENERISCHE ANMELDEARTEN-VERARBEITUNG ==================

def process_anmeldeart_generic(anmeldeart, df_leit, data_sources, field_mappings, stats):
    """Generische Verarbeitung für alle Anmeldearten"""
    config = ANMELDEART_CONFIG.get(anmeldeart, {})
    results = []
    
    anmeldeart_data = df_leit[df_leit[field_mappings['anmeldeart_col']] == anmeldeart]
    
    for idx, leit_row in anmeldeart_data.iterrows():
        if has_atb_in_weitere_folge(leit_row, field_mappings):
            stats['atb_skipped'] = stats.get('atb_skipped', 0) + 1
            continue
        
        uid = leit_row[field_mappings[f'leit_col_{config["unique_field"]}']]
        
        dates_info = calculate_warehouse_dates(
            leit_row[field_mappings['gestell_col']], 
            leit_row['Datum Ende - CUSFIN'],
            st.session_state.get('verwahrungsfrist_tage', 90)
        )
        
        common_data = create_common_data(leit_row, field_mappings['gestell_col'], dates_info)
        
        results.extend(process_anmeldeart_row(
            anmeldeart, uid, leit_row, common_data, data_sources, field_mappings, stats
        ))
        
        stats[f'processed_{anmeldeart.lower()}'] += 1
    
    return results

def process_anmeldeart_row(anmeldeart, uid, leit_row, common_data, data_sources, field_mappings, stats):
    """Verarbeitet eine einzelne Zeile basierend auf der Anmeldeart"""
    if anmeldeart == 'IMDC':
        return process_imdc_generic(
            uid, leit_row, common_data, data_sources, field_mappings, stats
        )
    elif anmeldeart == 'WIDS':
        return process_wids_generic(
            uid, leit_row, common_data, data_sources, field_mappings, stats
        )
    elif anmeldeart == 'IPDC':
        zollwert = pd.to_numeric(leit_row.get('Zollwert Folgeverfahren', 0), errors='coerce')
        if zollwert > 0:
            stats['ipdc_with_zollwert'] += 1
        else:
            stats['ipdc_without_zollwert'] += 1
        return [process_ipdc_row(common_data, leit_row, field_mappings['suma_pos_col'])]
    elif anmeldeart == 'NCDP':
        return process_ncdp_generic(
            uid, leit_row, common_data, data_sources, field_mappings, stats
        )
    else:
        return []

def process_imdc_generic(uid, leit_row, common_data, data_sources, field_mappings, stats):
    """IMDC-spezifische Verarbeitung mit verbessertem 3-Kriterien-Matching"""
    results = []
    
    mrn_suma = leit_row.get('Registriernummer/MRN SumA', '')
    pos_suma = str(leit_row.get(field_mappings['suma_pos_col'], '')) if field_mappings['suma_pos_col'] else ''
    
    import_df = data_sources['df_import_eza']
    match_col = field_mappings['import_eza_col']
    
    has_be_anteil = 'ATBnummer' in import_df.columns and 'Position' in import_df.columns
    
    if mrn_suma and pos_suma and has_be_anteil:
        mrn_weitere = uid
        mrn_reg = leit_row[field_mappings['leit_col_reg']]
        
        precise_matches = import_df[
            (import_df[match_col] == mrn_weitere) &
            (import_df['ATBnummer'] == mrn_suma) &
            (import_df['Position'] == pos_suma)
        ]
        
        used_mrn = mrn_weitere
        
        if precise_matches.empty and mrn_reg != mrn_weitere:
            precise_matches = import_df[
                (import_df[match_col] == mrn_reg) &
                (import_df['ATBnummer'] == mrn_suma) &
                (import_df['Position'] == pos_suma)
            ]
            used_mrn = mrn_reg
        
        if not precise_matches.empty:
            common_data['Erledigung mit'] = used_mrn
            stats['imdc_match'] += 1
            stats['imdc_3criteria_match'] += 1
            if pd.notna(precise_matches.iloc[0].get('ATBnummer', '')):
                stats['imdc_be_anteil_rows'] += 1
            
            import_row = precise_matches.iloc[0]
            results.append(process_imdc_row(
                import_row, common_data, leit_row, 
                field_mappings['pos_field_eza'], 
                field_mappings['suma_pos_col']
            ))
            return results
    
    fallback_id = leit_row[field_mappings['leit_col_reg']]
    fallback_matches, used_id = find_import_matches(
        uid, fallback_id, import_df, match_col
    )
    
    if not fallback_matches.empty:
        common_data['Erledigung mit'] = used_id
        stats['imdc_match'] += 1
        stats['imdc_fallback_match'] += 1
        
        sorted_matches = fallback_matches.sort_values(by=field_mappings['pos_field_eza'])
        import_row = sorted_matches.iloc[0]
        
        if has_be_anteil and pd.notna(import_row.get('ATBnummer', '')):
            stats['imdc_be_anteil_rows'] += 1
        
        results.append(process_imdc_row(
            import_row, common_data, leit_row, 
            field_mappings['pos_field_eza'], 
            field_mappings['suma_pos_col']
        ))
    else:
        stats['imdc_no_match'] += 1
        results.append(create_no_match_row(common_data, leit_row, 'IMDC', field_mappings['suma_pos_col']))
    
    return results

def process_wids_generic(uid, leit_row, common_data, data_sources, field_mappings, stats):
    """WIDS-spezifische Verarbeitung mit konfigurierbarer Aggregation"""
    results = []
    fallback_id = leit_row[field_mappings['leit_col_reg']]
    
    import_matches, used_id = find_import_matches(
        uid, fallback_id,
        data_sources['df_import_zl'],
        field_mappings['import_zl_col']
    )
    
    common_data['Erledigung mit'] = used_id
    
    if import_matches.empty:
        stats['wids_no_match'] += 1
        results.append(create_no_match_row(common_data, leit_row, 'WIDS', field_mappings['suma_pos_col']))
    else:
        stats['wids_match'] += 1
        
        agg_mode = st.session_state.get('wids_aggregation', 'Position mit höchstem Zollwert')
        
        if len(import_matches) == 1:
            results.append(process_wids_row(
                import_matches.iloc[0], common_data, leit_row,
                field_mappings['pos_field_zl'],
                field_mappings['suma_pos_col']
            ))
        else:
            if agg_mode == "Nur Position 1":
                sorted_matches = import_matches.sort_values(by=field_mappings['pos_field_zl'])
                selected_row = sorted_matches.iloc[0]
                row_data = process_wids_row(
                    selected_row, common_data, leit_row,
                    field_mappings['pos_field_zl'],
                    field_mappings['suma_pos_col']
                )
                pos_value = row_data['Pos']
                row_data['Pos'] = f"{pos_value} (1 von {len(import_matches)})"
                
            elif agg_mode == "Position mit höchstem Zollwert":
                import_matches['_calculated_zollwert'] = import_matches.apply(
                    lambda row: calculate_wids_zollwert(row), axis=1
                )
                selected_row = import_matches.loc[import_matches['_calculated_zollwert'].idxmax()]
                row_data = process_wids_row(
                    selected_row, common_data, leit_row,
                    field_mappings['pos_field_zl'],
                    field_mappings['suma_pos_col']
                )
                pos_value = row_data['Pos']
                row_data['Pos'] = f"{pos_value} (max von {len(import_matches)})"
                
            else:  # "Summe aller Positionen"
                total_zollabgabe = 0
                total_zollwert = 0
                max_zollsatz = 0
                
                for _, import_row in import_matches.iterrows():
                    zollabgabe = find_zl_value(import_row, 'zollabgabe')
                    zollsatz = find_zl_value(import_row, 'zollsatz')
                    dv1_betrag = find_zl_value(import_row, 'dv1')
                    
                    if zollsatz == 0:
                        zollwert = dv1_betrag
                    else:
                        zollwert = round(zollabgabe / (zollsatz / 100), 2) if zollsatz > 0 else 0
                    
                    total_zollabgabe += zollabgabe
                    total_zollwert += zollwert
                    max_zollsatz = max(max_zollsatz, zollsatz)
                
                avg_zollsatz = round(total_zollabgabe / total_zollwert * 100, 2) if total_zollwert > 0 else 0
                
                if st.session_state.get('zollsatz_null_ersetzen', True) and avg_zollsatz == 0 and total_zollwert > 0:
                    avg_zollsatz = st.session_state.get('zollsatz_ersatz', 0.12) * 100
                    total_zollabgabe = round(total_zollwert * avg_zollsatz / 100, 2)
                
                eust = round((total_zollwert + total_zollabgabe) * st.session_state.get('eust_satz', 0.19), 2)
                
                if field_mappings['suma_pos_col'] and field_mappings['suma_pos_col'] in leit_row:
                    suma_value = leit_row[field_mappings['suma_pos_col']]
                    common_data['SUMA-Position'] = pd.to_numeric(suma_value, errors='ignore') if pd.notna(suma_value) else ''
                
                pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
                
                row_data = common_data.copy()
                row_data.update({
                    'Pos': f'SUMME ({len(import_matches)} Pos.)',
                    'Codenummer': '',
                    'Menge': '',
                    'Zollwert (total)': total_zollwert,
                    'Drittlandzollsatz': avg_zollsatz,
                    'Zölle (total)': total_zollabgabe,
                    'EUSt': eust,
                    'Gesamtabgaben': total_zollabgabe if total_zollwert > 0 else pauschalbetrag,
                    'Anmeldeart': 'WIDS'
                })
            
            results.append(row_data)
    
    return results

def process_ncdp_generic(uid, leit_row, common_data, data_sources, field_mappings, stats):
    """NCDP-spezifische Verarbeitung"""
    results = []
    fallback_id = leit_row[field_mappings['leit_col_weitere']]
    
    ncts_matches, used_id = find_import_matches(
        uid, fallback_id,
        data_sources['df_ncts'],
        field_mappings['ncts_mrn_col']
    )
    
    common_data['Erledigung mit'] = used_id
    
    if ncts_matches.empty:
        stats['ncdp_no_match'] += 1
        results.append(create_no_match_row(common_data, leit_row, 'NCDP', field_mappings['suma_pos_col']))
    else:
        stats['ncdp_match'] += 1
        ncts_row = ncts_matches.iloc[0]
        results.append(process_ncdp_row(common_data, leit_row, ncts_row, field_mappings['suma_pos_col']))
    
    return results

def process_pauschale_anmeldeart(df_leit, field_mappings, stats, anmeldeart_filter=None, anmeldeart_name='(leer)'):
    """Verarbeitet pauschale Anmeldearten (leer, APDC, AVDC, NCAR)"""
    results = []
    
    if anmeldeart_filter is None:
        anmeldeart_data = df_leit[df_leit[field_mappings['anmeldeart_col']].isna() | (df_leit[field_mappings['anmeldeart_col']] == '')]
    else:
        anmeldeart_data = df_leit[df_leit[field_mappings['anmeldeart_col']] == anmeldeart_filter]
    
    pauschalbetrag = st.session_state.get('pauschalbetrag', 10000.0)
    
    for idx, pos_data in anmeldeart_data.iterrows():
        if has_atb_in_weitere_folge(pos_data, field_mappings):
            stats['atb_skipped'] = stats.get('atb_skipped', 0) + 1
            continue
        
        stats[f'{anmeldeart_name.lower()}_processed'] += 1
        
        dates_info = calculate_warehouse_dates(
            pos_data[field_mappings['gestell_col']],
            pos_data['Datum Ende - CUSFIN'],
            st.session_state.get('verwahrungsfrist_tage', 90)
        )
        
        pos_value = ''
        if field_mappings['suma_pos_col'] and field_mappings['suma_pos_col'] in pos_data:
            pos_raw = pos_data[field_mappings['suma_pos_col']]
            pos_value = pd.to_numeric(pos_raw, errors='ignore') if pd.notna(pos_raw) else ''
        
        results.append({
            'Referenznummer': str(pos_data.get('Bezugsnummer/LRN SumA', '')),
            'MRN-Nummer Eingang': str(pos_data.get('Registriernummer/MRN SumA', '')),
            'ATB-Nummer': str(pos_data.get('Registriernummer/MRN SumA', '')),
            'SUMA-Position': pos_value,
            'Gestellungsdatum': safe_date_value(pos_data[field_mappings['gestell_col']]),
            'Beendigung der Verwahrung': safe_date_value(pos_data['Datum Ende - CUSFIN']),
            'Verwahrungsfrist': dates_info.get('verwahrungsfrist_date', None),
            'Verwahrungsdauer': dates_info.get('verwahrungsdauer', 0),
            'Erledigung mit': '',
            'Pos': pos_value if pos_value else 'Pauschale',
            'Codenummer': '',
            'Menge': 0,
            'Zollwert (total)': 0.0,
            'Drittlandzollsatz': 0.0,
            'Zölle (total)': 0.0,
            'EUSt': 0.0,
            'Gesamtabgaben': pauschalbetrag,
            'Anmeldeart': anmeldeart_name
        })
    
    return results

# ================== BÜRGSCHAFTSSALDO FUNKTIONEN ==================

def create_bewegungstabelle(df_ziel):
    """Erstellt eine Memory-Tabelle mit allen Bewegungen (Ein- und Ausgänge)"""
    bewegungen = []
    
    for idx, row in df_ziel.iterrows():
        gestell_date = parse_german_date(row['Gestellungsdatum'])
        if gestell_date:
            bewegungen.append({
                'Datum': gestell_date,
                'Datum_str': safe_strftime(row['Gestellungsdatum']),
                'Bewegungsart': 'Eingang',
                'ATB-Nummer': row['ATB-Nummer'],
                'Referenznummer': row['Referenznummer'],
                'Pos': row['Pos'],
                'SUMA-Position': row.get('SUMA-Position', ''),
                'Belastung': row['Gesamtabgaben'],
                'Entlastung': 0,
                'Anmeldeart': row['Anmeldeart'],
                '_original_idx': idx
            })
        
        beend_date = parse_german_date(row['Beendigung der Verwahrung'])
        if beend_date:
            bewegungen.append({
                'Datum': beend_date,
                'Datum_str': safe_strftime(row['Beendigung der Verwahrung']),
                'Bewegungsart': 'Ausgang',
                'ATB-Nummer': row['ATB-Nummer'],
                'Referenznummer': row['Referenznummer'],
                'Pos': row['Pos'],
                'SUMA-Position': row.get('SUMA-Position', ''),
                'Belastung': 0,
                'Entlastung': row['Gesamtabgaben'],
                'Anmeldeart': row['Anmeldeart'],
                '_original_idx': idx
            })
    
    for bewegung in bewegungen:
        suma_pos = bewegung.get('SUMA-Position', '')
        try:
            bewegung['_suma_pos_numeric'] = float(suma_pos) if suma_pos != '' else 999999
        except:
            bewegung['_suma_pos_numeric'] = 999999
    
    bewegungen.sort(key=lambda x: (x['Datum'], 0 if x['Bewegungsart'] == 'Eingang' else 1, x['_original_idx'], x['_suma_pos_numeric']))
    
    for bewegung in bewegungen:
        bewegung.pop('_suma_pos_numeric', None)
    
    df_bewegungen = pd.DataFrame(bewegungen)
    if '_original_idx' in df_bewegungen.columns:
        df_bewegungen = df_bewegungen.drop(columns=['_original_idx'])
    
    return df_bewegungen

def calculate_daily_summary(bewegungen_df, startbuergschaft):
    """Berechnet Tagessummen und fortlaufenden Bürgschaftsstand"""
    startbuergschaft = float(startbuergschaft)
    daily_summary = {}
    
    bewegungen_df['Belastung'] = pd.to_numeric(bewegungen_df['Belastung'], errors='coerce').fillna(0)
    bewegungen_df['Entlastung'] = pd.to_numeric(bewegungen_df['Entlastung'], errors='coerce').fillna(0)
    
    unique_dates = sorted(bewegungen_df['Datum'].unique())
    
    for datum in unique_dates:
        tages_data = bewegungen_df[bewegungen_df['Datum'] == datum]
        
        belastung_summe = float(tages_data['Belastung'].sum())
        entlastung_summe = float(tages_data['Entlastung'].sum())
        
        if (st.session_state.get('buergschaft_erhöhung_aktiv', False) and 
            datum == st.session_state.get('buergschaft_erhöhung_datum', date(2025, 2, 4))):
            entlastung_summe += st.session_state.get('buergschaft_erhöhung_betrag', 1500000.0)
        
        daily_summary[datum] = {
            'Belastung': round(belastung_summe, 2),
            'Entlastung': round(entlastung_summe, 2),
            'Netto': round(entlastung_summe - belastung_summe, 2)
        }
    
    laufender_stand = startbuergschaft
    for datum in unique_dates:
        laufender_stand = laufender_stand - daily_summary[datum]['Belastung'] + daily_summary[datum]['Entlastung']
        daily_summary[datum]['Bürgschaftsstand'] = round(laufender_stand, 2)
    
    return daily_summary

def add_tagessummen_to_ziel(df_ziel, daily_summary):
    """Fügt Tagessummen zur Zieldatei hinzu - in der letzten Zeile des Tages"""
    df_ziel = prepare_dataframe_for_sorting(df_ziel)
    df_sorted = df_ziel.sort_values(['_gestell_date', 'ATB-Nummer', '_suma_pos_numeric']).copy()
    
    df_sorted[''] = ''  # Spalte S
    df_sorted['Belastung'] = ''
    df_sorted['Entlastung'] = ''
    df_sorted['Netto-Belastung'] = ''
    df_sorted['Bürgschaftsstand'] = ''
    
    for datum in daily_summary.keys():
        mask = df_sorted['_gestell_date'] == datum
        tag_indices = df_sorted[mask].index
        
        if len(tag_indices) > 0:
            last_idx = tag_indices[-1]
            
            if (st.session_state.get('buergschaft_erhöhung_aktiv', False) and 
                datum == st.session_state.get('buergschaft_erhöhung_datum', date(2025, 2, 4))):
                betrag = st.session_state.get('buergschaft_erhöhung_betrag', 1500000.0)
                df_sorted.loc[last_idx, ''] = f'TAGESSALDO {datum.strftime("%d.%m.%Y")} (Bürgschaft +{betrag/1000000:.1f} Mio)'
            else:
                df_sorted.loc[last_idx, ''] = f'TAGESSALDO {datum.strftime("%d.%m.%Y")}'
            
            df_sorted.loc[last_idx, 'Belastung'] = daily_summary[datum]['Belastung']
            df_sorted.loc[last_idx, 'Entlastung'] = daily_summary[datum]['Entlastung']
            df_sorted.loc[last_idx, 'Netto-Belastung'] = daily_summary[datum]['Netto']
            df_sorted.loc[last_idx, 'Bürgschaftsstand'] = daily_summary[datum]['Bürgschaftsstand']
    
    columns_to_drop = ['_gestell_date', '_suma_pos_numeric']
    columns_to_drop = [col for col in columns_to_drop if col in df_sorted.columns]
    if columns_to_drop:
        df_sorted = df_sorted.drop(columns=columns_to_drop)
    
    return df_sorted

def create_bewegungsdetails_df(bewegungen_df, daily_summary, startbuergschaft):
    """Erstellt die Bewegungsdetails-Tabelle mit Tagessummen"""
    bewegungen_df['_suma_pos_numeric'] = bewegungen_df['SUMA-Position'].apply(
        lambda x: float(x) if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.','').isdigit()) else 999999
    )
    
    bewegungen_sorted = bewegungen_df.sort_values(['Datum', 'Bewegungsart', 'ATB-Nummer', '_suma_pos_numeric'], 
                                                  ascending=[True, False, True, True]).copy()
    bewegungen_sorted = bewegungen_sorted.drop(columns=['_suma_pos_numeric'])
    
    result_rows = []
    
    result_rows.append({
        'Datum': None,
        'ATB-Nummer': 'START',
        'Referenznummer': '',
        'SUMA-Position': '',
        'Pos': '',
        'Belastung': 0,
        'Entlastung': 0,
        'Netto-Belastung': 0,
        'Bürgschaftsstand': startbuergschaft
    })
    
    laufender_stand = float(startbuergschaft)
    current_date = None
    
    for idx, row in bewegungen_sorted.iterrows():
        datum_obj = row['Datum']
        
        if (current_date != datum_obj and 
            datum_obj == st.session_state.get('buergschaft_erhöhung_datum', date(2025, 2, 4)) and
            st.session_state.get('buergschaft_erhöhung_aktiv', False)):
            
            laufender_stand += st.session_state.get('buergschaft_erhöhung_betrag', 1500000.0)
            
            result_rows.append({
                'Datum': datum_obj,
                'ATB-Nummer': 'BÜRGSCHAFTSERHÖHUNG',
                'Referenznummer': 'Erhöhung der verfügbaren Bürgschaft',
                'SUMA-Position': '',
                'Pos': '',
                'Belastung': '',
                'Entlastung': st.session_state.get('buergschaft_erhöhung_betrag', 1500000.0),
                'Netto-Belastung': '',
                'Bürgschaftsstand': round(laufender_stand, 2)
            })
        
        if current_date is not None and datum_obj != current_date:
            if current_date in daily_summary:
                result_rows.append({
                    'Datum': current_date,
                    'ATB-Nummer': 'TAGESSUMME',
                    'Referenznummer': '',
                    'SUMA-Position': '',
                    'Pos': '',
                    'Belastung': daily_summary[current_date]['Belastung'],
                    'Entlastung': daily_summary[current_date]['Entlastung'],
                    'Netto-Belastung': daily_summary[current_date]['Belastung'] - daily_summary[current_date]['Entlastung'],
                    'Bürgschaftsstand': daily_summary[current_date]['Bürgschaftsstand']
                })
                
                result_rows.append({
                    'Datum': None,
                    'ATB-Nummer': '',
                    'Referenznummer': '',
                    'SUMA-Position': '',
                    'Pos': '',
                    'Belastung': '',
                    'Entlastung': '',
                    'Netto-Belastung': '',
                    'Bürgschaftsstand': ''
                })
        
        belastung_wert = float(row['Belastung'])
        entlastung_wert = float(row['Entlastung'])
        
        laufender_stand = laufender_stand - belastung_wert + entlastung_wert
        
        result_rows.append({
            'Datum': datum_obj,
            'ATB-Nummer': row['ATB-Nummer'],
            'Referenznummer': row['Referenznummer'],
            'SUMA-Position': row.get('SUMA-Position', ''),
            'Pos': row['Pos'] if pd.notna(row['Pos']) else '',
            'Belastung': belastung_wert if belastung_wert > 0 else '',
            'Entlastung': entlastung_wert if entlastung_wert > 0 else '',
            'Netto-Belastung': '',
            'Bürgschaftsstand': round(laufender_stand, 2)
        })
        
        current_date = datum_obj
    
    if current_date is not None and current_date in daily_summary:
        result_rows.append({
            'Datum': current_date,
            'ATB-Nummer': 'TAGESSUMME',
            'Referenznummer': '',
            'SUMA-Position': '',
            'Pos': '',
            'Belastung': daily_summary[current_date]['Belastung'],
            'Entlastung': daily_summary[current_date]['Entlastung'],
            'Netto-Belastung': daily_summary[current_date]['Belastung'] - daily_summary[current_date]['Entlastung'],
            'Bürgschaftsstand': daily_summary[current_date]['Bürgschaftsstand']
        })
    
    return pd.DataFrame(result_rows)

def create_tageszusammenfassung_df_mit_extrema(bewegungen_df, daily_summary, startbuergschaft):
    """Erstellt eine kompakte Tagesübersicht mit Tagessummen und Höchst-/Tiefstständen"""
    result_rows = []
    
    result_rows.append({
        'Datum': 'START',
        'Tages-Belastung': '',
        'Tages-Entlastung': '',
        'Netto-Bewegung': '',
        'Tiefststand': float(startbuergschaft),
        'Höchststand': float(startbuergschaft),
        'Schlussstand': float(startbuergschaft),
        'Auslastung %': 0.0,
        'Hinweis': ''
    })
    
    bewegungen_df['_suma_pos_numeric'] = bewegungen_df['SUMA-Position'].apply(
        lambda x: float(x) if isinstance(x, (int, float)) or (isinstance(x, str) and x.replace('.','').isdigit()) else 999999
    )
    
    bewegungen_sorted = bewegungen_df.sort_values(['Datum', 'Bewegungsart', 'ATB-Nummer', '_suma_pos_numeric'], 
                                                  ascending=[True, False, True, True]).copy()
    bewegungen_sorted = bewegungen_sorted.drop(columns=['_suma_pos_numeric'])
    
    laufender_stand = float(startbuergschaft)
    sorted_dates = sorted(daily_summary.keys())
    
    for datum in sorted_dates:
        tages_bewegungen = bewegungen_sorted[bewegungen_sorted['Datum'] == datum]
        tages_data = daily_summary[datum]
        
        tagesstart_stand = laufender_stand
        tiefststand = tagesstart_stand
        hoechststand = tagesstart_stand
        
        for _, bewegung in tages_bewegungen.iterrows():
            laufender_stand = laufender_stand - float(bewegung['Belastung']) + float(bewegung['Entlastung'])
            tiefststand = min(tiefststand, laufender_stand)
            hoechststand = max(hoechststand, laufender_stand)
        
        if (st.session_state.get('buergschaft_erhöhung_aktiv', False) and 
            datum == st.session_state.get('buergschaft_erhöhung_datum', date(2025, 2, 4))):
            laufender_stand += st.session_state.get('buergschaft_erhöhung_betrag', 1500000.0)
            hoechststand = max(hoechststand, laufender_stand)
        
        max_auslastung = 0 if startbuergschaft == 0 else ((startbuergschaft - tiefststand) / startbuergschaft * 100)
        
        hinweis = ''
        if (st.session_state.get('buergschaft_erhöhung_aktiv', False) and 
            datum == st.session_state.get('buergschaft_erhöhung_datum', date(2025, 2, 4))):
            betrag = st.session_state.get('buergschaft_erhöhung_betrag', 1500000.0)
            hinweis = f'Bürgschaftserhöhung +{betrag:,.0f} €'
        
        result_rows.append({
            'Datum': safe_strftime(datum),
            'Tages-Belastung': tages_data['Belastung'],
            'Tages-Entlastung': tages_data['Entlastung'],
            'Netto-Bewegung': tages_data['Belastung'] - tages_data['Entlastung'],
            'Tiefststand': round(tiefststand, 2),
            'Höchststand': round(hoechststand, 2),
            'Schlussstand': round(tages_data['Bürgschaftsstand'], 2),
            'Auslastung %': round(max_auslastung, 2),
            'Hinweis': hinweis
        })
    
    if len(daily_summary) > 0:
        total_belastung = sum(daily_summary[d]['Belastung'] for d in daily_summary)
        total_entlastung = sum(daily_summary[d]['Entlastung'] for d in daily_summary)
        final_stand = daily_summary[sorted_dates[-1]]['Bürgschaftsstand']
        
        alle_tiefstwerte = [row['Tiefststand'] for row in result_rows[1:] if isinstance(row['Tiefststand'], (int, float))]
        alle_hoechstwerte = [row['Höchststand'] for row in result_rows[1:] if isinstance(row['Höchststand'], (int, float))]
        
        globaler_tiefststand = min(alle_tiefstwerte) if alle_tiefstwerte else startbuergschaft
        globaler_hoechststand = max(alle_hoechstwerte) if alle_hoechstwerte else startbuergschaft
        max_auslastung = 0 if startbuergschaft == 0 else ((startbuergschaft - globaler_tiefststand) / startbuergschaft * 100)
        
        result_rows.append({
            'Datum': '',
            'Tages-Belastung': '',
            'Tages-Entlastung': '',
            'Netto-Bewegung': '',
            'Tiefststand': '',
            'Höchststand': '',
            'Schlussstand': '',
            'Auslastung %': '',
            'Hinweis': ''
        })
        
        result_rows.append({
            'Datum': 'GESAMT',
            'Tages-Belastung': round(total_belastung, 2),
            'Tages-Entlastung': round(total_entlastung, 2),
            'Netto-Bewegung': round(total_belastung - total_entlastung, 2),
            'Tiefststand': globaler_tiefststand,
            'Höchststand': globaler_hoechststand,
            'Schlussstand': final_stand,
            'Auslastung %': round(max_auslastung, 2),
            'Hinweis': ''
        })
    
    return pd.DataFrame(result_rows)

# ================== NCAR-ENHANCEMENT FUNKTIONEN ==================

def enhance_ziel_with_ncar(ziel_df, ncar_df):
    """Erweitert Zieldatei um NCAR-Daten - vereinfachte Logik"""
    ziel_df['_atb_clean'] = ziel_df['ATB-Nummer'].astype(str).str.strip()
    ncar_df['_atb_clean'] = ncar_df['Registriernr.-SumA'].astype(str).str.strip()
    
    enhanced = ziel_df.merge(
        ncar_df[['_atb_clean', 'RegistriernNr./MRN', 'Anzahl Packstücke']],
        on='_atb_clean',
        how='left'
    )
    
    enhanced['MRN-Nummer Eingang'] = enhanced['RegistriernNr./MRN'].fillna(enhanced['MRN-Nummer Eingang'])
    enhanced['Menge'] = enhanced['Anzahl Packstücke'].fillna(enhanced['Menge'])
    
    enhanced = enhanced.drop(columns=['_atb_clean', 'RegistriernNr./MRN', 'Anzahl Packstücke'])
    
    return enhanced

def process_ncar_file(ncar_file):
    """Verarbeitet NCAR-Datei und validiert Struktur"""
    try:
        ncar_df = pd.read_excel(ncar_file)
        
        required_cols = ['Registriernr.-SumA', 'RegistriernNr./MRN', 'Anzahl Packstücke']
        missing_cols = [col for col in required_cols if col not in ncar_df.columns]
        
        if missing_cols:
            st.error(f"❌ Fehlende Spalten in NCAR-Datei: {missing_cols}")
            return None
        
        return ncar_df
        
    except Exception as e:
        st.error(f"❌ Fehler beim Lesen der NCAR-Datei: {e}")
        return None

# ================== HAUPTVERARBEITUNG ==================

def process_data():
    """Hauptverarbeitungsfunktion mit ATB-Filter und Error Handling"""
    # Setze Flag für aktive Verarbeitung
    st.session_state['processing_active'] = True
    st.session_state['processing_error'] = None
    
    try:
        df_leit = st.session_state.df_leit.copy()
        
        data_sources = {
            'df_leit': df_leit,
            'df_import_eza': st.session_state.df_import_eza.copy() if st.session_state.df_import_eza is not None else pd.DataFrame(),
            'df_import_zl': st.session_state.df_import_zl.copy() if st.session_state.df_import_zl is not None else pd.DataFrame(),
            'df_ncts': st.session_state.df_ncts.copy() if is_dataframe_valid(st.session_state.get('df_ncts')) else pd.DataFrame()
        }
        
        progress_bar = st.progress(0)
        
        # Spaltennamen-Mappings
        try:
            field_mappings = {
                'leit_col_weitere': find_col(df_leit, ['Weitere Registriernummer Folgeverfahren', 'Weitere Registriernummer']),
                'leit_col_reg': find_col(df_leit, ['Registriernummer Folgeverfahren']),
                'anmeldeart_col': find_col(df_leit, ['Anmeldeart Folgeverfahren']),
                'gestell_col': find_col(df_leit, ['Datum Überlassung - CUSTST']),
                'import_eza_col': find_col(data_sources['df_import_eza'], ['Registriernummer/MRN', 'Registriernummer / MRN', 'MRN'], required=not data_sources['df_import_eza'].empty) if not data_sources['df_import_eza'].empty else None,
                'import_zl_col': find_col(data_sources['df_import_zl'], ['Registriernummer/MRN', 'Registriernummer / MRN', 'MRN', 'Registrienummer/MRN'], required=not data_sources['df_import_zl'].empty) if not data_sources['df_import_zl'].empty else None,
                'pos_field_eza': find_col(data_sources['df_import_eza'], ['PositionNo'], required=not data_sources['df_import_eza'].empty) if not data_sources['df_import_eza'].empty else None,
                'pos_field_zl': find_col(data_sources['df_import_zl'], ['PositionNo'], required=not data_sources['df_import_zl'].empty) if not data_sources['df_import_zl'].empty else None,
                'ncts_mrn_col': 'MRN' if not data_sources['df_ncts'].empty and 'MRN' in data_sources['df_ncts'].columns else None,
                'suma_pos_col': None
            }
        except ValueError as e:
            raise e  # Weitergeben an übergeordneten Exception Handler
        
        # SUMA-Position finden
        suma_pos_candidates = ['Position SumA', 'Pos. SumA', 'PositionNo SumA', 'Position', 'Pos', 'PositionNo']
        for candidate in suma_pos_candidates:
            if candidate in df_leit.columns:
                field_mappings['suma_pos_col'] = candidate
                break
        
        if not field_mappings['suma_pos_col']:
            st.warning("⚠️ SUMA-Position-Spalte nicht gefunden. Verwende leeres Feld.")
        
        # MRN-Bereinigung
        df_leit[field_mappings['leit_col_weitere']] = df_leit[field_mappings['leit_col_weitere']].apply(clean_mrn)
        df_leit[field_mappings['leit_col_reg']] = df_leit[field_mappings['leit_col_reg']].apply(clean_mrn)
        
        for source, col in [('df_import_eza', 'import_eza_col'), ('df_import_zl', 'import_zl_col'), ('df_ncts', 'ncts_mrn_col')]:
            if field_mappings[col] and not data_sources[source].empty:
                data_sources[source][field_mappings[col]] = data_sources[source][field_mappings[col]].apply(clean_mrn)
        
        # Statistiken initialisieren
        stats = {
            'processed_imdc': 0, 'processed_ipdc': 0, 'processed_ncdp': 0, 'processed_wids': 0,
            'imdc_match': 0, 'imdc_no_match': 0,
            'imdc_3criteria_match': 0,
            'imdc_fallback_match': 0,
            'imdc_be_anteil_rows': 0,
            'ipdc_with_zollwert': 0, 'ipdc_without_zollwert': 0,
            'ncdp_match': 0, 'ncdp_no_match': 0,
            'wids_match': 0, 'wids_no_match': 0,
            '(leer)_processed': 0,
            'apdc_processed': 0,
            'avdc_processed': 0,
            'ncar_processed': 0,
            'atb_skipped': 0
        }
        
        results = []
        
        anmeldearten = ['IMDC', 'WIDS', 'IPDC', 'NCDP']
        
        total_steps = len(anmeldearten) + 4  # +4 für leer, APDC, AVDC, NCAR
        
        for i, anmeldeart in enumerate(anmeldearten):
            if df_leit[field_mappings['anmeldeart_col']].eq(anmeldeart).any():
                if anmeldeart in ['IMDC', 'WIDS']:
                    import_source = 'df_import_eza' if anmeldeart == 'IMDC' else 'df_import_zl'
                    if not data_sources[import_source].empty:
                        results.extend(process_anmeldeart_generic(
                            anmeldeart, df_leit, data_sources, field_mappings, stats
                        ))
                elif anmeldeart == 'IPDC':
                    results.extend(process_anmeldeart_generic(
                        anmeldeart, df_leit, data_sources, field_mappings, stats
                    ))
                elif anmeldeart == 'NCDP' and not data_sources['df_ncts'].empty:
                    results.extend(process_anmeldeart_generic(
                        anmeldeart, df_leit, data_sources, field_mappings, stats
                    ))
            
            progress_bar.progress((i + 1) / total_steps)
        
        # Leere Anmeldearten verarbeiten
        results.extend(process_pauschale_anmeldeart(
            df_leit, field_mappings, stats, None, '(leer)'
        ))
        progress_bar.progress((len(anmeldearten) + 1) / total_steps)
        
        # APDC verarbeiten
        if st.session_state.stats.get("APDC", 0) > 0:
            results.extend(process_pauschale_anmeldeart(
                df_leit, field_mappings, stats, 'APDC', 'APDC'
            ))
        progress_bar.progress((len(anmeldearten) + 2) / total_steps)
        
        # AVDC verarbeiten
        if st.session_state.stats.get("AVDC", 0) > 0:
            results.extend(process_pauschale_anmeldeart(
                df_leit, field_mappings, stats, 'AVDC', 'AVDC'
            ))
        progress_bar.progress((len(anmeldearten) + 3) / total_steps)
        
        # NCAR verarbeiten
        if st.session_state.stats.get("NCAR", 0) > 0:
            results.extend(process_pauschale_anmeldeart(
                df_leit, field_mappings, stats, 'NCAR', 'NCAR'
            ))
        progress_bar.progress(1.0)
        
        # ATB-Skip Info speichern
        st.session_state['atb_filtered_count'] = stats.get('atb_skipped', 0)
        
        results = apply_zoelle_rule(results)
        
        if results:
            ziel = pd.DataFrame(results)
            ziel = prepare_dataframe_for_sorting(ziel)
            ziel_sorted = sort_dataframe_standard(ziel).reset_index(drop=True)
            
            display_results(ziel_sorted, stats)
            
            # Bürgschaftssaldo immer verarbeiten
            process_buergschaft(ziel_sorted)
        else:
            st.warning("⚠️ Keine Daten zum Verarbeiten gefunden.")
            
    except Exception as e:
        # Fehler aufgetreten - speichere Fehlermeldung
        error_msg = f"{type(e).__name__}: {str(e)}"
        st.session_state['processing_error'] = error_msg
        st.error(f"❌ Fehler bei der Verarbeitung: {error_msg}")
        
        # Debug-Info in Expander
        with st.expander("🔍 Debug-Informationen", expanded=False):
            st.code(traceback.format_exc())
            
    finally:
        # WICHTIG: Flag immer zurücksetzen!
        st.session_state['processing_active'] = False
        
        # Progress Bar entfernen
        if 'progress_bar' in locals():
            progress_bar.empty()

# ================== ERGEBNIS-ANZEIGE ==================

def display_results(ziel, stats):
    """Zeigt Verarbeitungsergebnisse an"""
    st.success(f"✅ Verarbeitung erfolgreich! {len(ziel)} Zeilen erstellt.")
    
    # ATB-Filter Info
    if st.session_state.get('atb_filtered_count', 0) > 0:
        st.info(f"""
        ℹ️ **ATB-Filter:** {st.session_state['atb_filtered_count']} Zeilen mit ATB in 'Weitere Registriernummer Folgeverfahren' 
        wurden übersprungen (S-Anmeldearten und andere interne Vorgänge).
        """)
    
    s_arten_summe = sum(st.session_state.stats.get(art, 0) for art in ['SUSP', 'SUDC', 'SUCO', 'SUCF'])
    if s_arten_summe > 0:
        st.info(f"""
        ℹ️ **Hinweis:** {s_arten_summe} S-Anmeldearten (SUSP, SUDC, SUCO, SUCF) wurden in der Leitdatei gefunden, 
        aber nicht verarbeitet, da sie keine Bürgschaftsrelevanz haben (interne Konsolidierungen/Aufteilungen).
        """)
    
    col1, col2, col3, col4 = st.columns(4)
    col5, col6, col7, col8 = st.columns(4)
    
    metrics = [
        ("Gesamtzeilen", len(ziel)),
        ("IMDC-Zeilen", len(ziel[ziel['Anmeldeart'] == 'IMDC'])),
        ("WIDS-Zeilen", len(ziel[ziel['Anmeldeart'] == 'WIDS'])),
        ("IPDC-Zeilen", len(ziel[ziel['Anmeldeart'] == 'IPDC'])),
        ("NCDP-Zeilen", len(ziel[ziel['Anmeldeart'] == 'NCDP'])),
        ("(leer)-Zeilen", len(ziel[ziel['Anmeldeart'] == '(leer)'])),
        ("APDC-Zeilen", len(ziel[ziel['Anmeldeart'] == 'APDC'])),
        ("AVDC-Zeilen", len(ziel[ziel['Anmeldeart'] == 'AVDC']))
    ]
    
    for col, (label, value) in zip([col1, col2, col3, col4, col5, col6, col7, col8], metrics):
        with col:
            st.metric(label, value)
    
    # NCAR extra anzeigen
    ncar_count = len(ziel[ziel['Anmeldeart'] == 'NCAR'])
    if ncar_count > 0:
        st.metric("NCAR-Zeilen", ncar_count)
    
    display_processing_protocol(stats)
    display_financial_summary(ziel)

def display_processing_protocol(stats):
    """Zeigt Verarbeitungsprotokoll als kompakte Tabelle"""
    with st.expander("📊 Verarbeitungsprotokoll", expanded=True):
        protocol_data = []
        
        if st.session_state.stats.get("IMDC", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'IMDC',
                'Leitdatei': st.session_state.stats.get("IMDC", 0),
                'Verarbeitet': stats.get('processed_imdc', 0),
                'Mit Match': stats.get('imdc_match', 0),
                'Ohne Match': stats.get('imdc_no_match', 0),
                'Details': f"{stats.get('imdc_3criteria_match', 0)} präzise, {stats.get('imdc_fallback_match', 0)} Fallback"
            })
        
        if st.session_state.stats.get("WIDS", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'WIDS',
                'Leitdatei': st.session_state.stats.get("WIDS", 0),
                'Verarbeitet': stats.get('processed_wids', 0),
                'Mit Match': stats.get('wids_match', 0),
                'Ohne Match': stats.get('wids_no_match', 0),
                'Details': st.session_state.get('wids_aggregation', 'Position mit höchstem Zollwert')
            })
        
        if st.session_state.stats.get("IPDC", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'IPDC',
                'Leitdatei': st.session_state.stats.get("IPDC", 0),
                'Verarbeitet': stats.get('processed_ipdc', 0),
                'Mit Match': '—',
                'Ohne Match': '—',
                'Details': f"{stats.get('ipdc_with_zollwert', 0)} mit Zollwert, {stats.get('ipdc_without_zollwert', 0)} ohne"
            })
        
        if st.session_state.stats.get("NCDP", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'NCDP',
                'Leitdatei': st.session_state.stats.get("NCDP", 0),
                'Verarbeitet': stats.get('processed_ncdp', 0),
                'Mit Match': stats.get('ncdp_match', 0),
                'Ohne Match': stats.get('ncdp_no_match', 0),
                'Details': 'Sicherheitsbetrag aus NCTS'
            })
        
        if st.session_state.stats.get("(leer)", 0) > 0:
            protocol_data.append({
                'Anmeldeart': '(leer)',
                'Leitdatei': st.session_state.stats.get("(leer)", 0),
                'Verarbeitet': stats.get('(leer)_processed', 0),
                'Mit Match': '—',
                'Ohne Match': '—',
                'Details': st.session_state.get('leere_anmeldeart_option', 'Alle Zeilen (wie andere Anmeldearten)')
            })
        
        if st.session_state.stats.get("APDC", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'APDC',
                'Leitdatei': st.session_state.stats.get("APDC", 0),
                'Verarbeitet': stats.get('apdc_processed', 0),
                'Mit Match': '—',
                'Ohne Match': '—',
                'Details': 'Pauschale (wie leere)'
            })
        
        if st.session_state.stats.get("AVDC", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'AVDC',
                'Leitdatei': st.session_state.stats.get("AVDC", 0),
                'Verarbeitet': stats.get('avdc_processed', 0),
                'Mit Match': '—',
                'Ohne Match': '—',
                'Details': 'Pauschale (wie leere)'
            })
        
        if st.session_state.stats.get("NCAR", 0) > 0:
            protocol_data.append({
                'Anmeldeart': 'NCAR',
                'Leitdatei': st.session_state.stats.get("NCAR", 0),
                'Verarbeitet': stats.get('ncar_processed', 0),
                'Mit Match': '—',
                'Ohne Match': '—',
                'Details': f'Pauschale {st.session_state.get("pauschalbetrag", 10000):.0f}€'
            })
        
        if protocol_data:
            df_protocol = pd.DataFrame(protocol_data)
            st.dataframe(df_protocol, hide_index=True, use_container_width=True)
            
            if stats.get('imdc_be_anteil_rows', 0) > 0:
                be_prozent = (stats['imdc_be_anteil_rows'] / stats.get('processed_imdc', 1) * 100)
                st.info(f"💡 BE-Anteil: {stats['imdc_be_anteil_rows']} Zeilen ({be_prozent:.1f}%) mit BE-Anteil-Info verarbeitet")
        
        # ATB-Filter Statistik
        if stats.get('atb_skipped', 0) > 0:
            st.caption(f"🔵 {stats['atb_skipped']} Zeilen mit ATB in 'Weitere Registriernummer' wurden übersprungen")
        
        s_arten_summe = sum(st.session_state.stats.get(art, 0) for art in ['SUSP', 'SUDC', 'SUCO', 'SUCF'])
        if s_arten_summe > 0:
            st.caption(f"⚫ {s_arten_summe} S-Anmeldearten (interne Konsolidierungen) wurden nicht verarbeitet")

def display_financial_summary(ziel):
    """Zeigt finanzielle Zusammenfassung"""
    st.subheader("💰 Finanzielle Zusammenfassung")
    
    s_arten_summe = sum(st.session_state.stats.get(art, 0) for art in ['SUSP', 'SUDC', 'SUCO', 'SUCF'])
    if s_arten_summe > 0:
        st.warning(f"""
        ⚠️ **Hinweis:** {s_arten_summe} S-Anmeldearten wurden nicht in die finanzielle Zusammenfassung einbezogen, 
        da sie keine Bürgschaftsrelevanz haben (interne Vorgänge).
        """)
    
    ziel_numeric = ziel.copy()
    ziel_numeric['Zollwert (total)'] = pd.to_numeric(ziel_numeric['Zollwert (total)'], errors='coerce').fillna(0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Gesamt-Zollwert", f"€ {ziel_numeric['Zollwert (total)'].sum():,.2f}")
    with col2:
        st.metric("Gesamt-Zölle", f"€ {ziel['Zölle (total)'].sum():,.2f}")
    with col3:
        st.metric("Gesamt-EUSt", f"€ {ziel['EUSt'].sum():,.2f}")
    with col4:
        st.metric("Gesamtabgaben", f"€ {ziel['Gesamtabgaben'].sum():,.2f}")
    
    st.subheader("📊 Aufschlüsselung nach Anmeldeart")
    
    anmeldearten = ['IMDC', 'WIDS', 'IPDC', 'NCDP', '(leer)', 'APDC', 'AVDC', 'NCAR']
    
    summary_data = []
    
    for art in anmeldearten:
        art_data = ziel[ziel['Anmeldeart'] == art]
        if len(art_data) > 0:
            art_numeric = art_data.copy()
            art_numeric['Zollwert (total)'] = pd.to_numeric(art_numeric['Zollwert (total)'], errors='coerce').fillna(0)
            
            summary_data.append({
                'Anmeldeart': art,
                'Anzahl': len(art_data),
                'Zollwert': art_numeric['Zollwert (total)'].sum(),
                'Zölle': art_data['Zölle (total)'].sum(),
                'EUSt': art_data['EUSt'].sum(),
                'Gesamtabgaben': art_data['Gesamtabgaben'].sum()
            })
    
    if summary_data:
        summary_df = pd.DataFrame(summary_data)
        
        formatted_df = summary_df.copy()
        for col in ['Zollwert', 'Zölle', 'EUSt', 'Gesamtabgaben']:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"€ {x:,.2f}")
        
        st.dataframe(formatted_df, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.write("**GESAMT**")
        with col2:
            st.write(f"**{summary_df['Anzahl'].sum()}**")
        with col3:
            st.write(f"**€ {summary_df['Zollwert'].sum():,.2f}**")
        with col4:
            st.write(f"**€ {summary_df['Zölle'].sum():,.2f}**")
        with col5:
            st.write(f"**€ {summary_df['EUSt'].sum():,.2f}**")
        with col6:
            st.write(f"**€ {summary_df['Gesamtabgaben'].sum():,.2f}**")
    
    st.info(f"""
    ℹ️ **Hinweise:** 
    - Gesamtabgaben zwischen 0,01€ und 0,99€ werden auf 1€ angehoben
    - Bei Gesamtabgaben = 0€: Wenn Zollwert > 0 → 1€, sonst {st.session_state.get('pauschalbetrag', 10000):.0f}€ Pauschale
    - Zölle sind IMMER gleich Gesamtabgaben
    - Die EUSt wird separat ausgewiesen und ist NICHT in den Gesamtabgaben enthalten
    """)

def process_buergschaft(ziel):
    """Verarbeitet Bürgschaftssaldo-Berechnung"""
    st.subheader("💰 Bürgschaftssaldo-Berechnung")
    
    with st.spinner("Bürgschaftssaldo wird berechnet..."):
        bewegungen_df = create_bewegungstabelle(ziel)
        daily_summary = calculate_daily_summary(bewegungen_df, st.session_state.get('startbuergschaft', 0))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Startbürgschaft", f"€ {st.session_state.get('startbuergschaft', 0):,.2f}")
        
        total_belastung = sum(d['Belastung'] for d in daily_summary.values())
        total_entlastung = sum(d['Entlastung'] for d in daily_summary.values())
        end_stand = st.session_state.get('startbuergschaft', 0) - total_belastung + total_entlastung
        
        with col2:
            st.metric("Gesamtbelastung", f"€ {total_belastung:,.2f}")
            st.metric("Gesamtentlastung", f"€ {total_entlastung:,.2f}")
        
        with col3:
            st.metric("Endbürgschaft", f"€ {end_stand:,.2f}")
            auslastung = 0 if st.session_state.get('startbuergschaft', 0) == 0 else ((st.session_state.get('startbuergschaft', 0) - end_stand) / st.session_state.get('startbuergschaft', 0) * 100)
            st.metric("Auslastung", f"{auslastung:.1f}%")
        
        ziel_mit_saldo = add_tagessummen_to_ziel(ziel, daily_summary)
        bewegungsdetails_df = create_bewegungsdetails_df(bewegungen_df, daily_summary, st.session_state.get('startbuergschaft', 0))
        tageszusammenfassung_df = create_tageszusammenfassung_df_mit_extrema(bewegungen_df, daily_summary, st.session_state.get('startbuergschaft', 0))
        
        # NCAR nur für ziel_mit_saldo anwenden
        ncar_info = ""
        if st.session_state.get('ncar_enabled', True) and 'df_ncar' in st.session_state and st.session_state['df_ncar'] is not None:
            ziel_mit_saldo = enhance_ziel_with_ncar(ziel_mit_saldo, st.session_state['df_ncar'])
            
            # Statistiken für Info
            transport_mrn_rows = (ziel_mit_saldo['MRN-Nummer Eingang'] != ziel_mit_saldo['ATB-Nummer']).sum()
            packstuck_rows = (pd.to_numeric(ziel_mit_saldo['Menge'], errors='coerce') > 0).sum()
            
            ncar_info = f" (inkl. NCAR: {transport_mrn_rows} Transport-MRN, {packstuck_rows} mit Packstücken)"
        
        # Bürgschaftserhöhung Info
        buergschaft_info = ""
        if st.session_state.get('buergschaft_erhöhung_aktiv', False):
            betrag = st.session_state.get('buergschaft_erhöhung_betrag', 0)
            datum = st.session_state.get('buergschaft_erhöhung_datum', date.today())
            buergschaft_info = f" | Bürgschaft +{betrag/1000000:.1f} Mio am {datum.strftime('%d.%m.%Y')}"
        
        st.success(f"✅ Bürgschaftssaldo wurde berechnet!{ncar_info}{buergschaft_info}")
        
        st.info(f"""
        **Excel wird 3 Sheets enthalten:**
        1. **Ergebnis** - {len(ziel_mit_saldo)} Zeilen mit Tagessalden{ncar_info}
        2. **Bewegungsdetails** - {len(bewegungsdetails_df)} Zeilen mit allen Ein-/Ausgängen
        3. **Tageszusammenfassung** - {len(tageszusammenfassung_df)} Zeilen mit Höchst-/Tiefstständen pro Tag
        """)
        
        # Direkt Export-Funktion aufrufen
        export_results_with_buergschaft(ziel_mit_saldo, bewegungsdetails_df, tageszusammenfassung_df)

def export_results_with_buergschaft(ziel_mit_saldo, bewegungsdetails_df, tageszusammenfassung_df):
    """Exportiert Ergebnisse mit Bürgschaftssaldo"""
    output = io.BytesIO()
    
    with pd.ExcelWriter(
        output, 
        engine='xlsxwriter',
        date_format='DD.MM.YYYY',
        datetime_format='DD.MM.YYYY HH:MM:SS'
    ) as writer:
        ziel_export = ziel_mit_saldo.copy()
        ziel_export = clean_dataframe_for_export(ziel_export)
        bewegungsdetails_export = clean_dataframe_for_export(bewegungsdetails_df)
        
        ziel_export.to_excel(writer, index=False, sheet_name='Ergebnis')
        bewegungsdetails_export.to_excel(writer, index=False, sheet_name='Bewegungsdetails')
        tageszusammenfassung_df.to_excel(writer, index=False, sheet_name='Tageszusammenfassung')
        
        workbook = writer.book
        currency_format = workbook.add_format({'num_format': '#,##0.00 €'})
        date_format = workbook.add_format({'num_format': 'DD.MM.YYYY'})
        
        for sheet_name, df in [('Ergebnis', ziel_export), ('Bewegungsdetails', bewegungsdetails_df), ('Tageszusammenfassung', tageszusammenfassung_df)]:
            worksheet = writer.sheets[sheet_name]
            for col_idx, col_name in enumerate(df.columns):
                if any(x in col_name for x in ['Zollwert', 'Zölle', 'EUSt', 'abgaben', 'Belastung', 'Entlastung', 'Bürgschaftsstand', 'Tiefststand', 'Höchststand', 'Schlussstand', 'Netto']):
                    worksheet.set_column(col_idx, col_idx, 15, currency_format)
                elif col_name in ['Gestellungsdatum', 'Beendigung der Verwahrung', 'Verwahrungsfrist', 'Datum']:
                    worksheet.set_column(col_idx, col_idx, 12, date_format)
    
    output.seek(0)
    
    st.download_button(
        label="📥 Excel-Datei herunterladen",
        data=output,
        file_name=f"Zolldaten_mit_Buergschaft_{date.today().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ================== UI KOMPONENTEN ==================

def setup_sidebar():
    """Konfiguriert die Sidebar mit richtigen Vorbelegungen"""
    with st.sidebar:
        # Mandanten-Info und Settings-Anzeige
        if 'mandant' in st.session_state:
            # Logo anzeigen wenn vorhanden
            if st.session_state.get('mandant_logo') and os.path.exists(st.session_state.get('mandant_logo', '')):
                try:
                    st.image(st.session_state['mandant_logo'], width=200)
                except:
                    pass
            
            st.markdown(f"### 🏢 {st.session_state['mandant']}")
            
            # Settings-Anzeige mit Zahnrad
            with st.expander("⚙️ Aktuelle Einstellungen", expanded=True):
                settings = load_settings()
                if settings and 'current_config' in settings:
                    config = settings[settings['current_config']]
                    st.info(f"""
                    **Zeitraum:** {config['von']} - {config['bis']}  
                    **Bürgschaft:** {config['buergschaft']:,.0f} €  
                    **Pauschale:** {config['pauschale']:,.0f} €  
                    **Ersatz-Zollsatz:** {config['ersatz_zollsatz']}%
                    """)
                    
                    # Bürgschaftserhöhung anzeigen wenn aktiv
                    if config.get('buergschaft_erhoehung_aktiv', False):
                        st.success(f"""
                        **Bürgschaftserhöhung:** +{config.get('buergschaft_erhoehung_betrag', 0):,.0f} € am {config.get('buergschaft_erhoehung_datum', 'N/A')}
                        """)
            
            # NEUER BUTTON statt Dialog
            if st.button("⚙️ Einstellungen ändern", type="primary", use_container_width=True):
                st.session_state['show_settings'] = True
                st.rerun()
            
            st.markdown("---")
        
        st.header("⚙️ Einstellungen")
        
        # Basis-Einstellungen
        st.session_state['eust_satz'] = st.number_input(
            "EUSt-Satz (%)", 
            min_value=0, 
            max_value=100, 
            value=19,
            disabled=True
        ) / 100
        
        st.session_state['verwahrungsfrist_tage'] = st.number_input(
            "Verwahrungsfrist (Tage)", 
            min_value=1, 
            max_value=365, 
            value=90,
            disabled=True
        )
        
        st.markdown("---")
        
        # WIDS-Aggregation
        st.subheader("📊 WIDS-Verarbeitung")
        st.session_state['wids_aggregation'] = st.radio(
            "Bei mehreren Positionen pro MRN:",
            ["Nur Position 1", "Position mit höchstem Zollwert", "Summe aller Positionen"],
            index=1,  # Position mit höchstem Zollwert vorbelegt
            disabled=True
        )
        st.info("WIDS gibt immer nur 1 Zeile pro Leitdatei-Eintrag aus")
        
        st.markdown("---")
        
        # Bürgschaftssaldo
        st.subheader("💰 Bürgschaftssaldo")
        st.info("✅ Bürgschaftssaldo wird immer berechnet")
        
        # Bürgschaft NUR ANZEIGEN (nicht mehr editierbar in Sidebar!)
        st.metric(
            "Startbürgschaft", 
            f"€ {st.session_state.get('startbuergschaft', 0):,.2f}"
        )
        st.caption("Änderungen über ⚙️ Einstellungen")
        
        # Bürgschaftserhöhung - NUR ANZEIGE
        if st.session_state.get('buergschaft_erhöhung_aktiv', False):
            betrag = st.session_state.get('buergschaft_erhöhung_betrag', 0)
            datum = st.session_state.get('buergschaft_erhöhung_datum', date.today())
            st.info(f"✅ Bürgschaftserhöhung: +{betrag:,.0f} € am {datum.strftime('%d.%m.%Y')}")
        else:
            st.info("❌ Keine Bürgschaftserhöhung konfiguriert")
        
        st.info("Excel erstellt immer 3 Sheets")
        
        st.markdown("---")
        
        # NCAR-Enhancement - IMMER AKTIVIERT
        st.subheader("✨ NCAR-Enhancement")
        st.checkbox(
            "NCAR-Daten hinzufügen (optional)",
            value=True,  # IMMER TRUE
            disabled=True,  # NICHT ÄNDERBAR
            help="NCAR-Datei wird nach der Leitdatei hochgeladen und automatisch verarbeitet"
        )
        st.info("NCAR-Upload erscheint nach Leitdatei-Upload")
        
        st.markdown("---")
        
        # Erweiterte Einstellungen
        st.subheader("🔧 Erweiterte Einstellungen")
        
        # Leere Anmeldearten
        st.checkbox("Leere/APDC/AVDC/NCAR verarbeiten", value=True, disabled=True, key="leere_checkbox_display")
        st.session_state['leere_anmeldeart_option'] = st.radio(
            "Verarbeitungsmodus:",
            ["Eindeutige ATB (eine Zeile pro ATB)", "Alle Zeilen (wie andere Anmeldearten)"],
            index=1,  # Alle Zeilen vorbelegt
            disabled=True
        )
        st.info("Gilt für (leer), APDC, AVDC und NCAR")
        
        st.markdown("---")
        
        # Zollsatz-Ersetzung - Wert aus Session State anzeigen!
        st.checkbox("Bei Zollsatz 0% ersetzen durch:", value=True, disabled=True, key="zollsatz_checkbox_display")
        st.number_input(
            "Ersatz-Zollsatz (%)", 
            min_value=0.0, 
            max_value=100.0, 
            value=st.session_state.get('zollsatz_ersatz', 0.12) * 100,
            step=0.1,
            disabled=True
        )
        
        st.markdown("---")
        
        # EZA-Spalten-Einstellung
        st.subheader("📋 EZA-Verarbeitung")
        st.session_state['eza_auto_reduce'] = st.checkbox(
            "EZA-Spalten automatisch reduzieren",
            value=st.session_state.get('eza_auto_reduce', True),
            help="Reduziert EZA-Dateien automatisch auf 13 Standard-Spalten"
        )
        
        st.markdown("---")
        
        # Automatische Geschäftsregeln
        st.subheader("💡 Automatische Geschäftsregeln")
        st.info(f"""
        **Bürgschaftsberechnung:**
        - **Mindestabgaben:** 1€ (bei allen Werten zwischen 0,01€ und 0,99€)
        - **Bei 0€:** 1€ wenn Zollwert > 0, sonst {st.session_state.get('pauschalbetrag', 10000):.0f}€ Pauschale
        - **Zölle = Gesamtabgaben:** Immer gleich
        
        Diese Regeln werden automatisch angewendet.
        """)
        
        st.markdown("---")
        
        # Statistiken
        if "stats" in st.session_state:
            st.markdown("### 📊 Statistiken")
            if "Gesamt" in st.session_state.stats:
                st.metric("Gesamt-Zeilen", st.session_state.stats["Gesamt"])
                st.markdown("---")
            
            verarbeitbare = ['IMDC', 'WIDS', 'IPDC', 'NCDP', 'APDC', 'AVDC', 'NCAR']
            s_arten = ['SUSP', 'SUDC', 'SUCO', 'SUCF']
            
            st.markdown("**✅ Verarbeitbare Anmeldearten:**")
            for key in verarbeitbare:
                value = st.session_state.stats.get(key, 0)
                if value > 0:
                    st.write(f"{key}: **{value}**")
            
            if st.session_state.stats.get("(leer)", 0) > 0:
                st.write(f"(leer): **{st.session_state.stats.get('(leer)', 0)}**")
            
            s_arten_vorhanden = any(st.session_state.stats.get(key, 0) > 0 for key in s_arten)
            if s_arten_vorhanden:
                st.markdown("**⚫ Interne Anmeldearten (nicht bürgschaftsrelevant):**")
                for key in s_arten:
                    value = st.session_state.stats.get(key, 0)
                    if value > 0:
                        st.write(f"{key}: **{value}** *(wird nicht verarbeitet)*")
        
        # NEU: Processing Status anzeigen
        if st.session_state.get('processing_active', False):
            st.warning("⏳ Verarbeitung läuft...")
        
        if st.session_state.get('processing_error'):
            st.error(f"❌ Fehler: {st.session_state['processing_error']}")

def show_file_upload_section():
    """Zeigt die Datei-Upload-Sektion"""
    # Logo und Titel nebeneinander wenn Logo vorhanden
    if st.session_state.get('mandant_logo') and os.path.exists(st.session_state.get('mandant_logo', '')):
        col1, col2 = st.columns([1, 4])
        with col1:
            try:
                st.image(st.session_state['mandant_logo'], width=150)
            except:
                pass
        with col2:
            st.title("📦 PORT v5.0.1 – Dateiverwaltungs-App")
            if 'mandant' in st.session_state:
                st.caption(f"Mandant: {st.session_state['mandant']}")
    else:
        # Kein Logo - normale Anzeige
        st.title("📦 PORT v5.0.1 – Dateiverwaltungs-App")
        if 'mandant' in st.session_state:
            st.caption(f"Mandant: {st.session_state['mandant']}")
    
    st.header("📁 Dateien hochladen")
    leitdatei = st.file_uploader("Leitdatei", type=["xlsx", "xls"], key="leitdatei")
    
    if leitdatei is not None:
        process_leitdatei(leitdatei)
        
        if st.session_state.df_leit is not None:
            show_all_imports()
            show_processing_button()

def process_leitdatei(leitdatei):
    """Verarbeitet die Leitdatei"""
    try:
        with st.spinner("Leitdatei wird geladen..."):
            df_leit = pd.read_excel(leitdatei)
            
            required_leit_cols = [
                ['Datum Überlassung - CUSTST'],
                ['Weitere Registriernummer Folgeverfahren', 'Weitere Registriernummer'],
                ['Registriernummer Folgeverfahren'],
                ['Anmeldeart Folgeverfahren'],
                ['Bezugsnummer/LRN SumA'],
                ['Registriernummer/MRN SumA'],
                ['Datum Ende - CUSFIN']
            ]
            
            validate_dataframe(df_leit, required_leit_cols, "Leitdatei")
        
        st.session_state.df_leit_unfiltered = df_leit
        
    except Exception as e:
        st.error(f"❌ Fehler beim Laden der Leitdatei: {e}")
        return
    
    st.subheader("📅 Zeitraum auswählen")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        von_datum = st.date_input("Von-Datum", value=st.session_state.get('von_datum', date(2023, 11, 1)))
    with col2:
        bis_datum = st.date_input("Bis-Datum", value=st.session_state.get('bis_datum', date(2024, 4, 30)))
    
    st.session_state['von_datum'] = von_datum
    st.session_state['bis_datum'] = bis_datum
    
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        filter_button = st.button("🔍 Filter anwenden", type="primary", use_container_width=True)
    
    if filter_button or st.session_state.get('datum_filter_confirmed', False):
        st.session_state['datum_filter_confirmed'] = True
        
        gestell_col = find_col(df_leit, ['Datum Überlassung - CUSTST'])
        df_leit['_gestell_date'] = pd.to_datetime(df_leit[gestell_col], errors='coerce').dt.date
        df_leit = df_leit.dropna(subset=['_gestell_date'])
        mask = (df_leit['_gestell_date'] >= von_datum) & (df_leit['_gestell_date'] <= bis_datum)
        df_leit_filtered = df_leit[mask].copy()
        df_leit_filtered = df_leit_filtered.drop(columns=['_gestell_date'])
        
        if df_leit_filtered.empty:
            st.warning("⚠️ Keine Daten im gewählten Zeitraum gefunden!")
            st.stop()
        
        st.session_state.df_leit = df_leit_filtered
        
        anmeldeart_col = find_col(df_leit_filtered, ['Anmeldeart Folgeverfahren'])
        st.session_state.stats = calculate_statistics(df_leit_filtered, anmeldeart_col)
        
        st.success(f"✅ {len(df_leit_filtered)} Einträge im Zeitraum {von_datum.strftime('%d.%m.%Y')} - {bis_datum.strftime('%d.%m.%Y')}")
        display_statistics_table()
        
        # NCAR-Upload direkt hier - IMMER AKTIVIERT
        if st.session_state.get('ncar_enabled', True):
            st.markdown("---")
            st.subheader("📦 NCAR-Versandbeendigung (optional)")
            st.info("Laden Sie eine NCAR-Datei hoch, um Transport-MRN und Packstücke automatisch zu ergänzen")
            
            ncar_file = st.file_uploader(
                "NCAR-Datei", 
                type=["xlsx", "xls"], 
                key="ncar_upfront"
            )
            
            if ncar_file:
                with st.spinner("NCAR-Datei wird verarbeitet..."):
                    ncar_df = process_ncar_file(ncar_file)
                    if ncar_df is not None:
                        st.session_state['df_ncar'] = ncar_df
                        st.success(f"✅ NCAR-Datei geladen: {len(ncar_df)} Einträge")
                    else:
                        st.session_state['df_ncar'] = None
            else:
                st.session_state['df_ncar'] = None
    else:
        st.info("👆 Bitte wählen Sie einen Zeitraum und klicken Sie auf 'Filter anwenden'")

def display_statistics_table():
    """Zeigt Statistik-Tabelle"""
    verarbeitbare_arten = ['IMDC', 'WIDS', 'IPDC', 'NCDP', 'APDC', 'AVDC', 'NCAR']
    interne_arten = ['SUSP', 'SUDC', 'SUCO', 'SUCF']
    
    verarbeitbar_data = []
    intern_data = []
    
    for art in verarbeitbare_arten:
        if st.session_state.stats.get(art, 0) > 0:
            verarbeitbar_data.append({
                "Anmeldeart": art, 
                "Zeilen": st.session_state.stats.get(art, 0),
                "Status": "✅"
            })
    
    for art in interne_arten:
        if st.session_state.stats.get(art, 0) > 0:
            intern_data.append({
                "Anmeldeart": art, 
                "Zeilen": st.session_state.stats.get(art, 0),
                "Status": "⚫"
            })
    
    if st.session_state.stats.get("(leer)", 0) > 0:
        verarbeitbar_data.append({
            "Anmeldeart": "(leer)", 
            "Zeilen": st.session_state.stats.get("(leer)", 0),
            "Status": "✅"
        })
    
    all_data = verarbeitbar_data + intern_data
    
    if all_data:
        col1, col2 = st.columns([3, 1])
        with col1:
            stats_df = pd.DataFrame(all_data)
            st.dataframe(stats_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.metric("Gesamt", st.session_state.stats.get("Gesamt", 0))
            
            verarbeitbar_summe = sum(item["Zeilen"] for item in verarbeitbar_data)
            intern_summe = sum(item["Zeilen"] for item in intern_data)
            
            st.write("**Aufschlüsselung:**")
            st.write(f"- Verarbeitbar: **{verarbeitbar_summe}**")
            if intern_summe > 0:
                st.write(f"- Intern (S-Arten): **{intern_summe}**")
    
    # Zeitraum-Anzeige für benötigte Import-Dateien
    for anmeldeart, file_type in [("IMDC", "Importdatei EZA"), ("WIDS", "Importdatei ZL"), ("NCDP", "NCTS-Datei")]:
        if st.session_state.stats.get(anmeldeart, 0) > 0:
            # Filtere Leitdatei nach dieser Anmeldeart
            anmeldeart_col = find_col(st.session_state.df_leit, ['Anmeldeart Folgeverfahren'])
            anmeldeart_data = st.session_state.df_leit[st.session_state.df_leit[anmeldeart_col] == anmeldeart]
            
            # Hole die Erledigungsdaten (Datum Ende - CUSFIN)
            erledigungs_daten = pd.to_datetime(anmeldeart_data['Datum Ende - CUSFIN'], errors='coerce').dropna()
            
            if not erledigungs_daten.empty:
                # Ermittle ältestes und jüngstes Erledigungsdatum
                von_datum = erledigungs_daten.min()
                bis_datum = erledigungs_daten.max()
                
                # Formatiere als Monat/Jahr
                von_str = von_datum.strftime('%m/%Y')
                bis_str = bis_datum.strftime('%m/%Y')
                
                # Wenn gleicher Monat, nur einmal anzeigen
                if von_str == bis_str:
                    zeitraum_str = von_str
                else:
                    zeitraum_str = f"{von_str} - {bis_str}"
                
                st.info(f"📋 Für {st.session_state.stats.get(anmeldeart, 0)} {anmeldeart}-Zeilen wird eine {file_type} benötigt **({zeitraum_str})**")
            else:
                # Fallback wenn keine gültigen Daten
                st.info(f"📋 Für {st.session_state.stats.get(anmeldeart, 0)} {anmeldeart}-Zeilen wird eine {file_type} benötigt.")

def show_all_imports():
    """Zeigt alle Import-Uploads nebeneinander"""
    st.markdown("---")
    st.subheader("📂 Import-Dateien")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        process_import_upload(
            anmeldeart="IMDC",
            file_type="Import EZA",
            file_key="importdatei_eza",
            session_key="df_import_eza",
            required_cols=[
                ['Registriernummer/MRN', 'Registriernummer / MRN', 'MRN'],
                ['PositionNo'],
                ['Warentarifnummer'],
                ['Zollwert'],
                ['AbgabeZollsatz']
            ],
            special_processing="eza"
        )
    
    with col2:
        process_import_upload(
            anmeldeart="WIDS",
            file_type="Import ZL",
            file_key="importdatei_zl",
            session_key="df_import_zl",
            required_cols=[
                ['Registriernummer/MRN', 'Registriernummer / MRN', 'MRN', 'Registrienummer/MRN'],
                ['PositionNo'],
                ['Warentarifnummer'],
                ['Vorraussichtliche Zollabgabe', 'Voraussichtliche Zollabgabe'],
                ['Vorraussichtliche Zollsatzabgabe', 'Voraussichtliche Zollsatzabgabe'],
                ['DV1UmgerechnerterRechnungsbetrag']
            ],
            special_processing=None
        )
    
    with col3:
        process_import_upload(
            anmeldeart="NCDP",
            file_type="NCTS",
            file_key="nctsdatei",
            session_key="df_ncts",
            required_cols=[
                ['MRN'],
                ['Sicherheit']
            ],
            special_processing=None
        )

def process_import_upload(anmeldeart, file_type, file_key, session_key, required_cols, special_processing=None):
    """Generische Funktion für Import-Uploads mit optimierter EZA-Verarbeitung"""
    count = st.session_state.stats.get(anmeldeart, 0)
    
    if count > 0:
        st.write(f"**{file_type}** ({count} {anmeldeart})")
        
        uploaded_file = st.file_uploader(
            file_type.split()[-1],
            type=["xlsx", "xls"],
            key=file_key
        )
        
        if uploaded_file is not None:
            with st.spinner("Wird geladen..."):
                df_import = pd.read_excel(uploaded_file)
                
                # EZA-Verarbeitung - nutzt Sidebar-Einstellung
                if special_processing == "eza":
                    original_col_count = len(df_import.columns)
                    
                    # Prüfe Sidebar-Einstellung für automatische Reduzierung
                    if st.session_state.get('eza_auto_reduce', True) and original_col_count > len(EXAKTE_EZA_SPALTEN):
                        # Finde vorhandene Spalten
                        found_columns = [col for col in EXAKTE_EZA_SPALTEN if col in df_import.columns]
                        if len(found_columns) >= 5:
                            df_import = df_import[found_columns].copy()
                            st.success(f"✅ Spalten automatisch reduziert: {original_col_count} → {len(found_columns)}")
                        else:
                            st.warning(f"⚠️ Zu wenige Standard-Spalten gefunden ({len(found_columns)}/13) - keine Reduzierung")
                    elif not st.session_state.get('eza_auto_reduce', True) and original_col_count > len(EXAKTE_EZA_SPALTEN):
                        st.info(f"ℹ️ EZA-Datei hat {original_col_count} Spalten (automatische Reduzierung deaktiviert)")
                    
                    # Duplikate entfernen
                    original_count = len(df_import)
                    if len(df_import.columns) >= 6:
                        col_E = df_import.columns[4]
                        col_F = df_import.columns[5]
                        df_import = df_import.drop_duplicates(subset=[col_E, col_F], keep='first')
                        removed_count = original_count - len(df_import)
                    else:
                        removed_count = 0
                    
                    unique_count = len(df_import)
                    
                    # BE Anteil verarbeiten
                    df_import = process_eza_be_anteil(df_import)
                    multiplied_count = len(df_import) - unique_count
                
                # Validierung
                try:
                    validate_dataframe(df_import, required_cols, file_type)
                    st.session_state[session_key] = df_import
                    st.success(f"✅ {len(df_import)} Einträge")
                    
                    # Zusatzinfo für EZA
                    if special_processing == "eza" and (removed_count > 0 or multiplied_count > 0):
                        st.caption(f"Duplikate: -{removed_count}, BE: +{multiplied_count}")
                        
                except Exception as e:
                    st.error(f"❌ Fehler in {file_type}: {e}")
                    st.session_state[session_key] = None
    else:
        st.write(f"**{file_type}**")
        st.info("Nicht benötigt")
        st.session_state[session_key] = None if anmeldeart != "NCDP" else pd.DataFrame()

def show_processing_button():
    """Zeigt Verarbeitungs-Button wenn alle Dateien vorhanden"""
    if (st.session_state.df_import_eza is not None or st.session_state.df_import_zl is not None or 
        (st.session_state.stats.get("IMDC", 0) == 0 and st.session_state.stats.get("WIDS", 0) == 0) or 
        st.session_state.stats.get("IPDC", 0) > 0 or 
        st.session_state.stats.get("(leer)", 0) > 0 or
        st.session_state.stats.get("APDC", 0) > 0 or
        st.session_state.stats.get("AVDC", 0) > 0 or
        st.session_state.stats.get("NCAR", 0) > 0):
        
        st.markdown("---")
        st.subheader("⚙️ Datenverarbeitung")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.write("**Leitdatei:**")
            for anmeldeart in ['IMDC', 'WIDS', 'IPDC', 'NCDP', 'APDC', 'AVDC', 'NCAR']:
                if st.session_state.stats.get(anmeldeart, 0) > 0:
                    st.write(f"{anmeldeart}: {st.session_state.stats.get(anmeldeart, 0)}")
            if st.session_state.stats.get('(leer)', 0) > 0:
                st.write(f"(leer): {st.session_state.stats.get('(leer)', 0)}")
        
        with col2:
            st.write("**Import EZA:**")
            if st.session_state.df_import_eza is not None:
                st.write(f"{len(st.session_state.df_import_eza)} Einträge")
            else:
                st.write("—")
        
        with col3:
            st.write("**Import ZL:**")
            if st.session_state.df_import_zl is not None:
                st.write(f"{len(st.session_state.df_import_zl)} Einträge")
            else:
                st.write("—")
        
        with col4:
            st.write("**NCTS:**")
            if is_dataframe_valid(st.session_state.get('df_ncts')):
                st.write(f"{len(st.session_state.df_ncts)} Einträge")
            else:
                st.write("—")
        
        # NCAR-Status hinzufügen - IMMER ANZEIGEN
        if st.session_state.get('ncar_enabled', True):
            st.write("")
            if 'df_ncar' in st.session_state and st.session_state['df_ncar'] is not None:
                st.info(f"✨ NCAR-Datei: {len(st.session_state['df_ncar'])} Einträge")
            else:
                st.info("✨ NCAR-Datei: Nicht hochgeladen (optional)")
        
        # Bürgschaftserhöhung Status
        if st.session_state.get('buergschaft_erhöhung_aktiv', False):
            betrag = st.session_state.get('buergschaft_erhöhung_betrag', 0)
            datum = st.session_state.get('buergschaft_erhöhung_datum', date.today())
            st.info(f"💰 Bürgschaftserhöhung: +{betrag:,.0f} € am {datum.strftime('%d.%m.%Y')} aktiviert")
        
        can_process = True
        missing_files = []
        
        if st.session_state.stats.get("IMDC", 0) > 0 and st.session_state.df_import_eza is None:
            can_process = False
            missing_files.append("Import EZA")
        
        if st.session_state.stats.get("WIDS", 0) > 0 and st.session_state.df_import_zl is None:
            can_process = False
            missing_files.append("Import ZL")
        
        if st.session_state.stats.get("NCDP", 0) > 0 and not is_dataframe_valid(st.session_state.get('df_ncts')):
            can_process = False
            missing_files.append("NCTS")
        
        if not can_process:
            st.error(f"Fehlende Dateien: {', '.join(missing_files)}")
        else:
            st.markdown("")
            if st.button("🚀 Verarbeitung starten", type="primary", use_container_width=True):
                process_data()

# ================== HAUPTFUNKTION ==================

def main():
    """Hauptfunktion der App"""
    show_login()
    
    # Nach erfolgreichem Login
    if st.session_state.get('authenticated', False):
        # Ersteinrichtung prüfen
        if not check_initial_setup():
            return
        
        init_session_state()
        setup_sidebar()
        
        # NEUE LOGIK: Zeige Settings ODER normale Ansicht
        if st.session_state.get('show_settings', False):
            show_settings_page()
        else:
            show_file_upload_section()

if __name__ == "__main__":
    main()