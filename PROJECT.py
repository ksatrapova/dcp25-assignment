"""
ABC Tune Explorer 
"""

import os
import re
import sqlite3
import pandas as pd
from pathlib import Path

# =============================================================================
# DATABASE AND PARSING CLASSES 
# =============================================================================

class ABCParser:
    """
    Parses ABC notation files and extracts tune metadata
    """
    
    def __init__(self):
        # Compile regex patterns for extracting tune metadata
        self.title_pattern = re.compile(r'^T:(.+)$', re.MULTILINE)
        self.rhythm_pattern = re.compile(r'^R:(.+)$', re.MULTILINE)
        self.key_pattern = re.compile(r'^K:(.+)$', re.MULTILINE)
        self.composer_pattern = re.compile(r'^C:(.+)$', re.MULTILINE)
        self.source_pattern = re.compile(r'^S:(.+)$', re.MULTILINE)
    
    def parse_file(self, file_path, book_number):
        """
        Parse a single ABC file and extract all tunes
        """
        tunes = []
        
        try:
            # Read the entire file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split file into individual tunes (each starts with X: followed by a number)
            tune_blocks = re.split(r'^X:\s*\d+', content, flags=re.MULTILINE)[1:]
            
            # Extract metadata from each tune block
            for block in tune_blocks:
                title_match = self.title_pattern.search(block)
                if not title_match:
                    continue  # Skip if no title found
                
                # Extract rhythm type (or default to 'Unknown')
                rhythm_match = self.rhythm_pattern.search(block)
                rhythm_type = rhythm_match.group(1).strip() if rhythm_match else 'Unknown'
                
                # Extract key signature
                key_match = self.key_pattern.search(block)
                key = key_match.group(1).strip() if key_match else 'Unknown'
                
                # Extract composer
                composer_match = self.composer_pattern.search(block)
                composer = composer_match.group(1).strip() if composer_match else 'Unknown'
                
                # Extract source
                source_match = self.source_pattern.search(block)
                source = source_match.group(1).strip() if source_match else None
                
                # Create tune dictionary
                tunes.append({
                    'title': title_match.group(1).strip(),
                    'rhythm_type': rhythm_type,
                    'key': key,
                    'composer': composer,
                    'source': source,
                    'book_number': book_number,
                    'file_name': os.path.basename(file_path),
                    'content': block.strip()
                })
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        return tunes


class TuneDatabase:
    """
    SQLite database manager for storing and querying ABC tunes
    """
    
    def __init__(self, db_path='tunes.db'):
        """Initialize database connection and create table if needed"""
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS tunes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                rhythm_type TEXT,
                key TEXT,
                composer TEXT,
                source TEXT,
                book_number INTEGER,
                file_name TEXT,
                content TEXT
            )
        ''')
        self.conn.commit()
    
    def insert_tunes(self, tunes):
        """
        Insert multiple tunes into the database
        """
        cursor = self.conn.cursor()
        for tune in tunes:
            cursor.execute('''
                INSERT INTO tunes 
                (title, rhythm_type, key, composer, source, book_number, file_name, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tune['title'], 
                tune['rhythm_type'], 
                tune['key'], 
                tune['composer'], 
                tune['source'],
                tune['book_number'], 
                tune['file_name'], 
                tune['content']
            ))
        self.conn.commit()
    
    def get_dataframe(self):
        
        return pd.read_sql("SELECT * FROM tunes ORDER BY id", self.conn)
    
    def close(self):
        """Close database connection."""
        self.conn.close()


# =============================================================================
# FILE LOADING UTILITIES 
# =============================================================================

def load_all_abc_files(base_dir='abc_books'):

    parser = ABCParser()
    all_tunes = []
    base_path = Path(base_dir)
    
    # Check if directory exists
    if not base_path.exists():
        print(f"Warning: Directory '{base_dir}' not found")
        return all_tunes
    
    # Iterate through numbered directories
    for item in sorted(base_path.iterdir()):
        if item.is_dir() and item.name.isdigit():
            book_number = int(item.name)
            print(f"  Loading book {book_number}...")
            
            # Parse all .abc files in this book directory
            for abc_file in item.glob('*.abc'):
                tunes = parser.parse_file(str(abc_file), book_number)
                all_tunes.extend(tunes)
                print(f"    - {abc_file.name}: {len(tunes)} tunes")
    
    return all_tunes


# =============================================================================
# DATA FILTERING FUNCTIONS 
# =============================================================================

def get_tunes_by_book(df, book_number):
    """
    Filter by book number.
    """
    
    return df[df['book_number'] == book_number]


def get_tunes_by_type(df, tune_type):
    """
    Filter by rhythm type (case-insensitive partial match)
    
    """
    return df[df['rhythm_type'].str.contains(tune_type, case=False, na=False)]


def search_tunes(df, search_term):
    """
    Search by title 

    """
    return df[df['title'].str.contains(search_term, case=False, na=False)]


