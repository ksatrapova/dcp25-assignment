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
    Parses ABC notation files A UZ MI JEBE Z TOHO
    
    """
    
    def __init__(self):
        # Compile regex patterns for extracting tune metadata
        self.title_pattern = re.compile(r'^T:(.+)$', re.MULTILINE)
        self.rhythm_pattern = re.compile(r'^R:(.+)$', re.MULTILINE)
        self.key_pattern = re.compile(r'^K:(.+)$', re.MULTILINE)
        self.composer_pattern = re.compile(r'^C:(.+)$', re.MULTILINE)
        self.source_pattern = re.compile(r'^S:(.+)$', re.MULTILINE)
    
    def parse_file(self, file_path, book_number):
        
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
    SQLite database manager for storing and querying ABC tunes.
    """
    
    def __init__(self, db_path='tunes.db'):
        """Initialize database connection and create table if needed."""
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
# TESTING CODE
# =============================================================================

if __name__ == "__main__":
    print("\nDatabase Foundation")
    print("=" * 50)
    
    # Test with sample data
    sample_tune = [{
        'title': 'Test Jig',
        'rhythm_type': 'Jig',
        'key': 'Gmaj',
        'composer': 'Trad.',
        'source': 'Test Collection',
        'book_number': 1,
        'file_name': 'test.abc',
        'content': 'X:1\nT:Test Jig\nR:Jig\nK:Gmaj'
    }]
    
    # Initialize database
    db = TuneDatabase('test_day1.db')
    
    # Insert sample tune
    db.insert_tunes(sample_tune)
    
    # Retrieve and display
    df = db.get_dataframe()
    print(f"\nDatabase initialized with {len(df)} tune(s)")
    print("\nSample data:")
    print(df[['title', 'rhythm_type', 'key', 'composer']].to_string())
    
    db.close()
    print("\n hahahahaha Database foundation working")
