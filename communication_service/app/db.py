import sqlite3
import os
import datetime
import pathlib

# Ensure data directory exists
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(data_dir, exist_ok=True)

DB_PATH = os.path.join(data_dir, 'communication.db')

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables"""
    # Check if database exists
    db_exists = pathlib.Path(DB_PATH).exists()
    
    conn = get_db_connection()
    
    print(f"Initializing communication database at {DB_PATH}")
    
    # Create tables
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS Messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_department_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL
        );
        
        CREATE TABLE IF NOT EXISTS MessageRecipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            recipient_department_id INTEGER NOT NULL,
            FOREIGN KEY (message_id) REFERENCES Messages (id),
            UNIQUE (message_id, recipient_department_id)
        );
    ''')
    
    conn.commit()
    conn.close()
    print("Communication database initialized successfully")

def create_message(sender_dept_id, recipients_dept_ids, subject, body):
    """Create a new message and associate it with recipients"""
    conn = get_db_connection()
    now = datetime.datetime.now().isoformat()
    
    try:
        # Insert the message
        cursor = conn.execute(
            'INSERT INTO Messages (sender_department_id, subject, body, timestamp) VALUES (?, ?, ?, ?)',
            (sender_dept_id, subject, body, now)
        )
        message_id = cursor.lastrowid
        
        # Associate with recipients
        for dept_id in recipients_dept_ids:
            conn.execute(
                'INSERT INTO MessageRecipients (message_id, recipient_department_id) VALUES (?, ?)',
                (message_id, dept_id)
            )
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error creating message: {e}")
        return False
    finally:
        conn.close()

def get_inbox_messages(department_id, department_hierarchy):
    """
    Get messages received by a department or its parent departments
    department_hierarchy: list of parent department IDs
    """
    conn = get_db_connection()
    
    # Include department and all its parents in the query
    dept_ids = [department_id] + department_hierarchy
    placeholders = ', '.join(['?'] * len(dept_ids))
    
    query = f'''
        SELECT 
            m.id,
            m.subject,
            m.timestamp,
            m.sender_department_id,
            (SELECT COUNT(*) FROM MessageRecipients WHERE message_id = m.id) AS recipient_count
        FROM Messages m
        JOIN MessageRecipients mr ON m.id = mr.message_id
        WHERE mr.recipient_department_id IN ({placeholders})
        ORDER BY m.timestamp DESC
    '''
    
    messages = conn.execute(query, dept_ids).fetchall()
    conn.close()
    
    return messages

def get_sent_messages(department_id):
    """Get messages sent by a department"""
    conn = get_db_connection()
    
    query = '''
        SELECT 
            m.id,
            m.subject,
            m.timestamp,
            (SELECT COUNT(*) FROM MessageRecipients WHERE message_id = m.id) AS recipient_count
        FROM Messages m
        WHERE m.sender_department_id = ?
        ORDER BY m.timestamp DESC
    '''
    
    messages = conn.execute(query, (department_id,)).fetchall()
    conn.close()
    
    return messages

def get_message_details(message_id):
    """Get full message details including sender, recipients, subject, body"""
    conn = get_db_connection()
    
    # Get message content
    message = conn.execute('''
        SELECT 
            m.id,
            m.sender_department_id,
            m.subject,
            m.body,
            m.timestamp
        FROM Messages m
        WHERE m.id = ?
    ''', (message_id,)).fetchone()
    
    if not message:
        conn.close()
        return None
    
    # Get message recipients
    recipients = conn.execute('''
        SELECT recipient_department_id
        FROM MessageRecipients
        WHERE message_id = ?
    ''', (message_id,)).fetchall()
    
    conn.close()
    
    result = dict(message)
    result['recipient_dept_ids'] = [r['recipient_department_id'] for r in recipients]
    
    return result

# Initialize the database when this module is imported
init_db() 