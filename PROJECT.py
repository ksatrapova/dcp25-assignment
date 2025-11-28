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
    """Parser for ABC notation files and extraction of tune metadata."""
    def __init__(self):
        self.title_pattern = re.compile(r'^T:(.+)$', re.MULTILINE)
        self.rhythm_pattern = re.compile(r'^R:(.+)$', re.MULTILINE)
        self.key_pattern = re.compile(r'^K:(.+)$', re.MULTILINE)
        self.composer_pattern = re.compile(r'^C:(.+)$', re.MULTILINE)
        self.source_pattern = re.compile(r'^S:(.+)$', re.MULTILINE)
    def parse_file(self, file_path, book_number):
        """Parse a file into a list of tune dictionaries"""
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
    """ SQLite database for storing and querying tunes"""
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
        """Insert tune dictionaries into the database"""
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
        """Return all tunes as a pandas DataFrame"""
        return pd.read_sql("SELECT * FROM tunes ORDER BY id", self.conn)
    def close(self):
        """Close the  database conection"""
        self.conn.close()   
# =============================================================================
# FILE LOADING UTILITIES 
# =============================================================================

def load_all_abc_files(base_dir='abc_books'):
    """looad and parse all files under the directory"""
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
    """Filter by book number"""
    return df[df['book_number'] == book_number]

def get_tunes_by_type(df, tune_type):
    """Filter by rhythm type"""
    return df[df['rhythm_type'].str.contains(tune_type, case=False, na=False)]

def search_tunes(df, search_term):
    """Search by title""" 
    return df[df['title'].str.contains(search_term, case=False, na=False)]

# =============================================================================
# UI - external (bude ruzove)
# =============================================================================


 # DataFrame containing all tunes
tunes_df = None         

# UI state
query_mode = "all"       # Current filter mode: "all", "book", "type", or "title"
query_value = ""         # Current search/filter text
scroll_offset = 0        # Vertical scroll position for tune list
status_message = "ABC Tune Explorer - Select a filter mode"
is_dragging_scrollbar = False  # Track if user is dragging scrollbar
drag_start_y = 0         # Y position where drag started
drag_start_scroll = 0    # Scroll offset when drag started

# UI dimensions
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700
HEADER_HEIGHT = 50
FILTER_SECTION_HEIGHT = 120
RESULTS_HEADER_HEIGHT = 40
FOOTER_HEIGHT = 40
ITEM_HEIGHT = 70
SCROLL_SPEED = 20
SCROLLBAR_WIDTH = 12
SCROLLBAR_MARGIN = 5

# Colors 
COLOR_BG = 	(253,228,242)      
COLOR_HEADER = (218,150,155)          
COLOR_BUTTON = (218,150,155)       
COLOR_BUTTON_ACTIVE = (255,179,179) 
COLOR_TEXT = (50, 50, 50)           
COLOR_TEXT_LIGHT = (120, 120, 120)   
COLOR_ITEM_BG = (253,228,242)     
COLOR_ITEM_ALT = (249,206,231)     


# =============================================================================
# PY5 SETUP AND DRAW FUNCTIONS
# =============================================================================

def setup():
    """Initialize the py5 sketch"""
    py5.size(WINDOW_WIDTH, WINDOW_HEIGHT)
    py5.background(*COLOR_BG)


def draw():
    """Main draw loop which renders the entire UI"""
    py5.background(*COLOR_BG)
    
    # Draw header bar
    draw_header()
    
    # Draw filter mode buttons
    draw_filter_buttons()
    
    # Draw search input area
    draw_search_input()
    
    # Draw results list (scrollable)
    draw_results_list()
    
    # Draw scrollbar
    draw_scrollbar()
    
    # Draw footer with status message
    draw_footer()


def draw_header():
    """Draw the top header bar + title"""
    py5.fill(*COLOR_HEADER)
    py5.no_stroke()
    py5.rect(0, 0, WINDOW_WIDTH, HEADER_HEIGHT)
    
    py5.fill(255)
    py5.text_size(20)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.text("ABC Tune Explorer", 20, HEADER_HEIGHT / 2)


def draw_filter_buttons():
    """Draw the filter buttons"""
    button_y = HEADER_HEIGHT + 20
    button_width = 120
    button_height = 40
    button_spacing = 15
    
    modes = [
        ("All Tunes", "all"),
        ("By Book", "book"),
        ("By Type", "type"),
        ("By Title", "title")
    ]
    
    py5.text_size(14)
    py5.text_align(py5.CENTER, py5.CENTER)
    
    for i, (label, mode) in enumerate(modes):
        x = 20 + i * (button_width + button_spacing)
        
        # Determine button color
        if query_mode == mode:
            py5.fill(*COLOR_BUTTON_ACTIVE)
        else:
            py5.fill(*COLOR_BUTTON)
        
        # Draw button, rounded corners
        py5.stroke(200)
        py5.stroke_weight(1)
        py5.rect(x, button_y, button_width, button_height, 5)
        
        # Draw button text
        if query_mode == mode:
            py5.fill(255)  # White text on active button
        else:
            py5.fill(*COLOR_TEXT)
        
        py5.text(label, x + button_width / 2, button_y + button_height / 2)


def draw_search_input():
    """search input box and instructions"""
    input_y = HEADER_HEIGHT + 75
    input_height = 35
    
    #input box background
    py5.fill(255)
    py5.stroke(200)
    py5.stroke_weight(1)
    py5.rect(20, input_y, WINDOW_WIDTH - 40, input_height, 5)
    
    # Display placeholder or input text
    py5.fill(*COLOR_TEXT_LIGHT)
    py5.text_size(13)
    py5.text_align(py5.LEFT, py5.CENTER)
    
    if query_mode == "all":
        py5.text("Showing all tunes (use buttons above to filter)", 30, input_y + input_height / 2)
    elif query_mode == "book":
        display_text = query_value if query_value else "Type book number and press Enter..."
        py5.text(display_text, 30, input_y + input_height / 2)
    elif query_mode == "type":
        display_text = query_value if query_value else "Type tune type (e.g., jig, reel, waltz)..."
        py5.text(display_text, 30, input_y + input_height / 2)
    elif query_mode == "title":
        display_text = query_value if query_value else "Type part of the title..."
        py5.text(display_text, 30, input_y + input_height / 2)


def draw_results_list():
    """Draw the scrollable list of filtered tunes accordin to filters"""
    global tunes_df
    
    # Calculate results area position
    results_y = HEADER_HEIGHT + FILTER_SECTION_HEIGHT
    results_height = WINDOW_HEIGHT - HEADER_HEIGHT - FILTER_SECTION_HEIGHT - FOOTER_HEIGHT
    
    # Apply filters based on current mode
    filtered_df = get_filtered_tunes()
    
    #results header with count
    py5.fill(244,224,225)
    py5.no_stroke()
    py5.rect(0, results_y, WINDOW_WIDTH, RESULTS_HEADER_HEIGHT)
    
    py5.fill(*COLOR_TEXT)
    py5.text_size(14)
    py5.text_align(py5.LEFT, py5.CENTER)
    count_text = f"{len(filtered_df)} tune{'s' if len(filtered_df) != 1 else ''} found"
    py5.text(count_text, 20, results_y + RESULTS_HEADER_HEIGHT / 2)
    
    # Setup clipping region for scrollable area
    list_y = results_y + RESULTS_HEADER_HEIGHT
    list_height = results_height - RESULTS_HEADER_HEIGHT
    
    py5.clip(0, list_y, WINDOW_WIDTH, list_height)
    
    # Draw each tune item
    y = list_y - scroll_offset
    
    for i, row in enumerate(filtered_df.itertuples()):
        # Only draw visible items 
        if y + ITEM_HEIGHT < list_y or y > list_y + list_height:
            y += ITEM_HEIGHT
            continue
        
        # Alternate row colors 
        if i % 2 == 0:
            py5.fill(*COLOR_ITEM_BG)
        else:
            py5.fill(*COLOR_ITEM_ALT)
        
        py5.no_stroke()
        py5.rect(20, y, WINDOW_WIDTH - 40, ITEM_HEIGHT - 5, 3)
        
        # tune title 
        py5.fill(*COLOR_TEXT)
        py5.text_size(15)
        py5.text_align(py5.LEFT, py5.TOP)
        py5.text(row.title, 30, y + 10)
        
        #tune metadata 
        py5.fill(*COLOR_TEXT_LIGHT)
        py5.text_size(12)
        metadata = f"Type: {row.rhythm_type}  |  Key: {row.key}  |  Composer: {row.composer}  |  Book: {row.book_number}"
        py5.text(metadata, 30, y + 35)
        
        y += ITEM_HEIGHT
    
    # Remove clipping
    py5.no_clip()


def draw_scrollbar():
    """Draw scrollbar"""
    
    # Calculate results area position
    results_y = HEADER_HEIGHT + FILTER_SECTION_HEIGHT + RESULTS_HEADER_HEIGHT
    results_height = WINDOW_HEIGHT - HEADER_HEIGHT - FILTER_SECTION_HEIGHT - FOOTER_HEIGHT - RESULTS_HEADER_HEIGHT
    
    # Get filtered data to calculate scrollbar size
    filtered_df = get_filtered_tunes()
    total_content_height = len(filtered_df) * ITEM_HEIGHT
    
    # Only show scrollbar if content is scrollable
    if total_content_height <= results_height:
        return
    
    # Calculate scrollbar track position
    scrollbar_x = WINDOW_WIDTH - SCROLLBAR_WIDTH - SCROLLBAR_MARGIN
    scrollbar_track_height = results_height
    
    # Draw scrollbar track
    py5.fill(244,224,225)
    py5.no_stroke()
    py5.rect(scrollbar_x, results_y, SCROLLBAR_WIDTH, scrollbar_track_height, 6)
    
    # Calculate scrollbar thumb size and position
    visible_ratio = results_height / total_content_height
    thumb_height = max(30, scrollbar_track_height * visible_ratio)  
    
    max_scroll = total_content_height - results_height
    scroll_ratio = scroll_offset / max_scroll if max_scroll > 0 else 0
    
    max_thumb_travel = scrollbar_track_height - thumb_height
    thumb_y = results_y + (max_thumb_travel * scroll_ratio)
    
    # Draw scrollbar thumb
    if is_dragging_scrollbar:
        py5.fill(109,75,78)  # when dragging
    else:
        py5.fill(174,120,124)  
    
    py5.rect(scrollbar_x, thumb_y, SCROLLBAR_WIDTH, thumb_height, 6)


def draw_footer():
    """footer with status message"""
    footer_y = WINDOW_HEIGHT - FOOTER_HEIGHT
    
    py5.fill(244,224,225)
    py5.no_stroke()
    py5.rect(0, footer_y, WINDOW_WIDTH, FOOTER_HEIGHT)
    
    py5.fill(*COLOR_TEXT_LIGHT)
    py5.text_size(12)
    py5.text_align(py5.LEFT, py5.CENTER)
    py5.text(status_message, 20, footer_y + FOOTER_HEIGHT / 2)


def get_filtered_tunes():
    """return filtered tunes thru mode and value"""
    
    global tunes_df
    
    if query_mode == "all":
        return tunes_df
    
    elif query_mode == "book" and query_value:
        try:
            book_num = int(query_value)
            return get_tunes_by_book(tunes_df, book_num)
        except ValueError:
            return pd.DataFrame()  # Return empty if invalid number
    
    elif query_mode == "type" and query_value:
        return get_tunes_by_type(tunes_df, query_value)
    
    elif query_mode == "title" and query_value:
        return search_tunes(tunes_df, query_value)
    
    return tunes_df


# =============================================================================
# PY5 EVENT HANDLERS
# =============================================================================

def key_pressed():
    """handle keyboard input, updates"""
    global query_value, status_message, scroll_offset
    
    # Only process input for modes that need it
    if query_mode in ["book", "type", "title"]:
        if py5.key == py5.BACKSPACE:
            query_value = query_value[:-1]
        elif py5.key == py5.ENTER or py5.key == py5.RETURN:
            status_message = f"Searching for: {query_value}"
        elif hasattr(py5, 'key') and py5.key and len(str(py5.key)) == 1 and py5.key.isprintable():
            if len(query_value) < 50:  # Limit input length
                query_value += py5.key
        
        # Reset scroll when query changes
        scroll_offset = 0


def mouse_pressed():
    """Handle mouse clicks on buttons and scrollbar"""
    global query_mode, query_value, status_message, scroll_offset
    global is_dragging_scrollbar, drag_start_y, drag_start_scroll
    
    # Calculate scrollbar position
    results_y = HEADER_HEIGHT + FILTER_SECTION_HEIGHT + RESULTS_HEADER_HEIGHT
    results_height = WINDOW_HEIGHT - HEADER_HEIGHT - FILTER_SECTION_HEIGHT - FOOTER_HEIGHT - RESULTS_HEADER_HEIGHT
    scrollbar_x = WINDOW_WIDTH - SCROLLBAR_WIDTH - SCROLLBAR_MARGIN
    
    # Check if clicking on scrollbar
    filtered_df = get_filtered_tunes()
    total_content_height = len(filtered_df) * ITEM_HEIGHT
    
    if total_content_height > results_height:  # Scrollbar is visible
        # Calculate thumb position
        visible_ratio = results_height / total_content_height
        thumb_height = max(30, results_height * visible_ratio)
        max_scroll = total_content_height - results_height
        scroll_ratio = scroll_offset / max_scroll if max_scroll > 0 else 0
        max_thumb_travel = results_height - thumb_height
        thumb_y = results_y + (max_thumb_travel * scroll_ratio)
        
        # Check if mouse is over scrollbar thumb
        if (scrollbar_x <= py5.mouse_x <= scrollbar_x + SCROLLBAR_WIDTH and
            thumb_y <= py5.mouse_y <= thumb_y + thumb_height):
            is_dragging_scrollbar = True
            drag_start_y = py5.mouse_y
            drag_start_scroll = scroll_offset
            return  # Don't process button clicks
        
        # Check if clicking on scrollbar track, jump to position
        if (scrollbar_x <= py5.mouse_x <= scrollbar_x + SCROLLBAR_WIDTH and
            results_y <= py5.mouse_y <= results_y + results_height):
            # Jump scroll to clicked position
            click_ratio = (py5.mouse_y - results_y) / results_height
            scroll_offset = click_ratio * max_scroll
            scroll_offset = max(0, min(scroll_offset, max_scroll))
            is_dragging_scrollbar = True
            drag_start_y = py5.mouse_y
            drag_start_scroll = scroll_offset
            return
    
    # Check if clicking on filter buttons
    button_y = HEADER_HEIGHT + 20
    button_width = 120
    button_height = 40
    button_spacing = 15
    
    modes = ["all", "book", "type", "title"]
    mode_labels = {
        "all": "Showing all tunes",
        "book": "Filter by book number",
        "type": "Filter by tune type",
        "title": "Search by title"
    }
    
    for i, mode in enumerate(modes):
        x = 20 + i * (button_width + button_spacing)
        
        if (x <= py5.mouse_x <= x + button_width and 
            button_y <= py5.mouse_y <= button_y + button_height):
            query_mode = mode
            query_value = ""
            scroll_offset = 0
            status_message = mode_labels[mode]
            break


def mouse_dragged():
    """Handle mouse dragging for scrollbar"""
    global scroll_offset, is_dragging_scrollbar
    
    if not is_dragging_scrollbar:
        return
    
    # Calculate how much to scroll based on drag distance
    results_y = HEADER_HEIGHT + FILTER_SECTION_HEIGHT + RESULTS_HEADER_HEIGHT
    results_height = WINDOW_HEIGHT - HEADER_HEIGHT - FILTER_SECTION_HEIGHT - FOOTER_HEIGHT - RESULTS_HEADER_HEIGHT
    
    filtered_df = get_filtered_tunes()
    total_content_height = len(filtered_df) * ITEM_HEIGHT
    max_scroll = max(0, total_content_height - results_height)
    
    if max_scroll == 0:
        return
    
    # Calculate thumb dimensions
    visible_ratio = results_height / total_content_height
    thumb_height = max(30, results_height * visible_ratio)
    max_thumb_travel = results_height - thumb_height
    
    # Calculate drag distance
    drag_distance = py5.mouse_y - drag_start_y
    
    # Convert drag distance to scroll offset
    if max_thumb_travel > 0:
        scroll_change = (drag_distance / max_thumb_travel) * max_scroll
        scroll_offset = drag_start_scroll + scroll_change
        scroll_offset = max(0, min(scroll_offset, max_scroll))


def mouse_released():
    """WHEN mouse releaseD stop scrollbar dragging"""
    global is_dragging_scrollbar
    is_dragging_scrollbar = False


def mouse_wheel(event):
    """Handle mouse wheel scrolling"""
    global scroll_offset
    
    # Get the filtered results to calculate max scroll
    filtered_df = get_filtered_tunes()
    
    # Calculate maximum scroll offset
    results_height = WINDOW_HEIGHT - HEADER_HEIGHT - FILTER_SECTION_HEIGHT - FOOTER_HEIGHT - RESULTS_HEADER_HEIGHT
    total_content_height = len(filtered_df) * ITEM_HEIGHT
    max_scroll = max(0, total_content_height - results_height)
    
    # Update scroll offset
    scroll_offset -= event.count * SCROLL_SPEED
    scroll_offset = max(0, min(scroll_offset, max_scroll))


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    """"DOES ALL THE WORK, entry point"""
    
    print("Loading ABC tune database...")
    
    # Load all files from directory structure
    all_tunes = load_all_abc_files()
    
    # Store tunes in database
    db = TuneDatabase()

    # Clear existing tunes so each run
    db.conn.execute("DELETE FROM tunes")
    db.conn.commit()
    
    db.insert_tunes(all_tunes)
    
    # Load tunes into DataFrame for UI
    tunes_df = db.get_dataframe()
    db.close()
    
    print(f"Loaded {len(tunes_df)} tunes")
    print("Starting UI...")
    
    # Launch py5 sketch
    py5.run_sketch()