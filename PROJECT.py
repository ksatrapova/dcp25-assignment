import os
import re
import sqlite3
import pandas as pd
from pathlib import Path
import py5

# =============================================================================
# DATABASE AND PARSING CLASSES 
# =============================================================================

class ABCParser:
    def __init__(self):
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
            for block in tune_blocks:
                title = self.title_pattern.search(block)
                if not title: continue     # Skip if no title found
            # Create tune dictionary
                tunes.append({
                    'title': title.group(1).strip(),
                    'rhythm_type': self.rhythm_pattern.search(block).group(1).strip() if self.rhythm_pattern.search(block) else 'Unknown',
                    'key': self.key_pattern.search(block).group(1).strip() if self.key_pattern.search(block) else 'Unknown',
                    'composer': self.composer_pattern.search(block).group(1).strip() if self.composer_pattern.search(block) else 'Unknown',
                    'source': self.source_pattern.search(block).group(1).strip() if self.source_pattern.search(block) else None,
                    'book_number': book_number,
                    'file_name': os.path.basename(file_path),
                    'content': block.strip()
                })
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        return tunes

class TuneDatabase:
    def __init__(self, db_path='tunes.db'):
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
                tune['title'], tune['rhythm_type'], tune['key'], tune['composer'], tune['source'],
                tune['book_number'], tune['file_name'], tune['content']
            ))
        self.conn.commit()
    def get_dataframe(self):
        return pd.read_sql("SELECT * FROM tunes ORDER BY id", self.conn)
    def close(self):
        self.conn.close()   #Close database connection
# =============================================================================
# FILE LOADING UTILITIES 
# =============================================================================

def load_all_abc_files(base_dir='abc_books'):
    parser = ABCParser()
    all_tunes = []
    base_path = Path(base_dir)
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
    #Filter by book number
    return df[df['book_number'] == book_number]

def get_tunes_by_type(df, tune_type):
    #Filter by rhythm type - case insensitive 
    return df[df['rhythm_type'].str.contains(tune_type, case=False, na=False)]

def search_tunes(df, search_term):
    #Search by title 
    return df[df['title'].str.contains(search_term, case=False, na=False)]

# =============================================================================
# UI - external (bude ruzove)
# =============================================================================


search_text = ""
status_message = "Welcome to ABC Tune Explorer "
query_mode = "all"   # all, book, type, title
query_value = ""     # Value used in search for book/type/title

tunes_df = None      # Main DataFrame, loaded from DB

def setup():
    py5.size(800, 860)
    py5.text_size(17)
    py5.background(245, 225, 235)  

def draw():
    py5.background(245, 225, 235)

    # Header
    py5.fill(255, 175, 215)
    py5.rect(0, 0, py5.width, 60)
    py5.fill(80)
    py5.text("ABC Tune Explorer ", 24, 38)

    # Buttons
    btn_y = 72
    btn_w = 110
    btn_h = 32
    modes = [("All", "all"), ("By Book", "book"), ("By Type", "type"), ("By Title", "title")]
    for i, (label, mode) in enumerate(modes):
        py5.fill(255, 215, 230) if query_mode == mode else py5.fill(235)
        py5.rect(30 + i * (btn_w + 10), btn_y, btn_w, btn_h, 12)
        py5.fill(120)
        py5.text(label, 30 + 15 + i * (btn_w + 10), btn_y + 20)



    # Footer
    py5.fill(255, 175, 215)
    py5.rect(0, py5.height - 48, py5.width, 48)
    py5.fill(80)
    py5.text(status_message, 32, py5.height - 18)

def key_pressed():
    global query_value, status_message
    if py5.key == py5.BACKSPACE:
        query_value = query_value[:-1]
    elif py5.key.isprintable() and len(query_value) < 30:
        query_value += py5.key
    

def mouse_pressed():
    global query_mode, query_value, status_message
    # button areas:
    btn_y = 72
    btn_w = 110
    btn_h = 32
    for i, mode in enumerate(["all", "book", "type", "title"]):
        btn_x = 30 + i * (btn_w + 10)
        if btn_x <= py5.mouse_x <= btn_x + btn_w and btn_y <= py5.mouse_y <= btn_y + btn_h:
            query_mode = mode
            query_value = ""
            status_message = f"Mode switched to '{mode}'"
            break

if __name__ == "__main__":
    # Load tunes from DB before running py5
    all_tunes = load_all_abc_files()
    db = TuneDatabase()
    db.insert_tunes(all_tunes)
    tunes_df = db.get_dataframe()
    db.close()
    py5.run_sketch()
