import sqlite3
import json
import numpy as np
from datetime import datetime

DATABASE_NAME = 'database/threat_db.sqlite'

def init_db():
    """Initializes the database with the complete schema for all advanced features."""
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pulses (
                id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, title TEXT NOT NULL UNIQUE,
                url TEXT, threat_name TEXT, threat_category TEXT, severity TEXT,
                targeted_industries TEXT, targeted_countries TEXT, summary TEXT, published_at DATETIME,
                embedding BLOB,
                collection_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE TABLE IF NOT EXISTS indicators (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, value TEXT NOT NULL UNIQUE, enrichment_data TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS pulse_indicators (pulse_id INTEGER, indicator_id INTEGER, FOREIGN KEY(pulse_id) REFERENCES pulses(id), FOREIGN KEY(indicator_id) REFERENCES indicators(id), PRIMARY KEY (pulse_id, indicator_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS pulse_correlations (source_pulse_id INTEGER, related_pulse_id INTEGER, reason TEXT, FOREIGN KEY(source_pulse_id) REFERENCES pulses(id), FOREIGN KEY(related_pulse_id) REFERENCES pulses(id), PRIMARY KEY (source_pulse_id, related_pulse_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS dynamic_sources (domain TEXT PRIMARY KEY, last_scraped DATETIME, added_at DATETIME DEFAULT CURRENT_TIMESTAMP)')
        conn.commit()

# --- All helper functions for getting/adding data ---
def add_correlation(source_id, related_id, reason):
    if source_id == related_id: return
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO pulse_correlations VALUES (?, ?, ?)", (source_id, related_id, reason))
        cursor.execute("INSERT OR IGNORE INTO pulse_correlations VALUES (?, ?, ?)", (related_id, source_id, reason))
        conn.commit()

def get_all_pulses_for_vector_search():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, embedding FROM pulses WHERE embedding IS NOT NULL")
        return [{"id": row[0], "embedding": np.frombuffer(row[1], dtype=np.float32)} for row in cursor.fetchall()]

def add_dynamic_source(domain):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO dynamic_sources (domain, last_scraped) VALUES (?, ?)", (domain, None))
        conn.commit()

# --- THE DEFINITIVE FIX IS IN THIS FUNCTION ---
def insert_pulse_and_indicators(pulse_data):
    """
    Inserts a pulse, defensively serializing any fields that might be lists
    into JSON strings before saving to the database.
    """
    pulse_title = pulse_data.get('title')
    if not pulse_title or pulse_title == "N/A":
        print(f"  ERROR: Skipping insertion due to invalid title.")
        return None

    # --- DEFENSIVE SERIALIZATION ---
    # Helper function to ensure a value is a string, serializing lists if needed.
    def to_db_string(value):
        if isinstance(value, list):
            # If it's a list, dump it to a JSON string.
            return json.dumps(value)
        # If it's anything else (string, None, etc.), it's safe.
        return value

    # Convert embedding to bytes if it exists
    embedding_blob = pulse_data.get('embedding').tobytes() if isinstance(pulse_data.get('embedding'), np.ndarray) else None
    
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO pulses (source, title, url, threat_name, threat_category, severity, targeted_industries, targeted_countries, summary, published_at, embedding)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pulse_data.get('source'),
                pulse_title,
                pulse_data.get('url'),
                to_db_string(pulse_data.get('threat_name')),       # Defensive serialization
                to_db_string(pulse_data.get('threat_category')),   # Defensive serialization
                to_db_string(pulse_data.get('severity')),          # Defensive serialization
                json.dumps(pulse_data.get('targeted_industries', [])), # Always expects a list
                json.dumps(pulse_data.get('targeted_countries', [])),  # Always expects a list
                pulse_data.get('summary'),
                pulse_data.get('published_at'),
                embedding_blob
            ))
            pulse_id = cursor.lastrowid
            
            # --- Indicator handling (unchanged but verified) ---
            indicators = pulse_data.get('indicators', [])
            if indicators:
                for ioc in indicators:
                    if isinstance(ioc, dict) and 'type' in ioc and 'value' in ioc:
                        cursor.execute("INSERT OR IGNORE INTO indicators (type, value, enrichment_data) VALUES (?, ?, ?)",
                                       (ioc.get('type'), ioc.get('value'), json.dumps(ioc.get('enrichment'))))
                        cursor.execute("SELECT id FROM indicators WHERE value = ?", (ioc.get('value'),))
                        indicator_id_row = cursor.fetchone()
                        if indicator_id_row:
                            indicator_id = indicator_id_row[0]
                            cursor.execute("INSERT OR IGNORE INTO pulse_indicators (pulse_id, indicator_id) VALUES (?, ?)",
                                           (pulse_id, indicator_id))
            conn.commit()
            print(f"  -> Successfully inserted pulse: {pulse_title}")
            return pulse_id
        except sqlite3.IntegrityError:
            return None # Expected for duplicates
        except Exception as e:
            conn.rollback()
            print(f"  CRITICAL DB ERROR inserting pulse data: {e}")
            return None

# --- Standard functions to get data for the frontend (unchanged) ---
def get_pulses(limit=200): # Increased limit to provide more data for the map
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        cursor.execute("SELECT id, source, title, threat_category, severity, published_at, targeted_countries FROM pulses ORDER BY published_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_pulse_details(pulse_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.row_factory = sqlite3.Row; cursor = conn.cursor()
        cursor.execute("SELECT * FROM pulses WHERE id = ?", (pulse_id,))
        pulse_row = cursor.fetchone()
        if not pulse_row: return None
        pulse = dict(pulse_row)
        cursor.execute('SELECT i.type, i.value, i.enrichment_data FROM indicators i JOIN pulse_indicators pi ON i.id = pi.indicator_id WHERE pi.pulse_id = ?', (pulse_id,))
        pulse['indicators'] = [dict(row) for row in cursor.fetchall()]
        return pulse
