import sqlite3
import os
import pathlib
from passlib.hash import pbkdf2_sha256

# Ensure data directory exists
data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(data_dir, exist_ok=True)

DB_PATH = os.path.join(data_dir, 'budgeting.db')

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
    
    # Create tables
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS Departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER NULL,
            FOREIGN KEY (parent_id) REFERENCES Departments (id)
        );
        
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hashed_password TEXT NOT NULL,
            department_id INTEGER NOT NULL,
            FOREIGN KEY (department_id) REFERENCES Departments (id)
        );
        
        CREATE TABLE IF NOT EXISTS FiscalYears (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year_name TEXT NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT 0
        );
        
        CREATE TABLE IF NOT EXISTS BudgetCategories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        
        CREATE TABLE IF NOT EXISTS Allocations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_id INTEGER NOT NULL,
            category_id INTEGER NOT NULL,
            fiscal_year_id INTEGER NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            FOREIGN KEY (department_id) REFERENCES Departments (id),
            FOREIGN KEY (category_id) REFERENCES BudgetCategories (id),
            FOREIGN KEY (fiscal_year_id) REFERENCES FiscalYears (id),
            UNIQUE(department_id, category_id, fiscal_year_id)
        );
        
        CREATE TABLE IF NOT EXISTS Expenditures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            allocation_id INTEGER NOT NULL,
            amount DECIMAL(15, 2) NOT NULL,
            description TEXT NOT NULL,
            date DATE NOT NULL,
            FOREIGN KEY (allocation_id) REFERENCES Allocations (id)
        );
    ''')
    
    # Checking if departments table is empty
    dept_count = conn.execute("SELECT COUNT(*) FROM Departments").fetchone()[0]
    
    # Seed initial data if departments table is empty
    if dept_count == 0:
        print("Initializing database with sample data...")
        try:
            # Create initial department structure
            conn.executescript('''
                -- Main departments
                INSERT INTO Departments (name, parent_id) VALUES ('Administration', NULL);
                INSERT INTO Departments (name, parent_id) VALUES ('BTech', NULL);
                INSERT INTO Departments (name, parent_id) VALUES ('MTech', NULL);
                
                -- BTech Subdepartments
                INSERT INTO Departments (name, parent_id) 
                VALUES ('CSE', (SELECT id FROM Departments WHERE name = 'BTech'));
                
                INSERT INTO Departments (name, parent_id) 
                VALUES ('ECE', (SELECT id FROM Departments WHERE name = 'BTech'));
                
                -- MTech Subdepartments
                INSERT INTO Departments (name, parent_id) 
                VALUES ('AI', (SELECT id FROM Departments WHERE name = 'MTech'));
                
                INSERT INTO Departments (name, parent_id) 
                VALUES ('Robotics', (SELECT id FROM Departments WHERE name = 'MTech'));
            ''')
            
            # Create initial users (admin:admin123, user1:pass123, user2:pass123)
            admin_hash = pbkdf2_sha256.hash("admin123")
            user1_hash = pbkdf2_sha256.hash("pass123")
            user2_hash = pbkdf2_sha256.hash("pass123")
            
            conn.execute('''
                INSERT INTO Users (username, hashed_password, department_id)
                VALUES (?, ?, (SELECT id FROM Departments WHERE name = 'Administration'))
            ''', ('admin', admin_hash))
            
            conn.execute('''
                INSERT INTO Users (username, hashed_password, department_id)
                VALUES (?, ?, (SELECT id FROM Departments WHERE name = 'CSE'))
            ''', ('user1', user1_hash))
            
            conn.execute('''
                INSERT INTO Users (username, hashed_password, department_id)
                VALUES (?, ?, (SELECT id FROM Departments WHERE name = 'AI'))
            ''', ('user2', user2_hash))
            
            # Create initial fiscal years
            conn.execute('''
                INSERT INTO FiscalYears (year_name, is_active)
                VALUES ('2023-2024', 0)
            ''')
            
            conn.execute('''
                INSERT INTO FiscalYears (year_name, is_active)
                VALUES ('2024-2025', 1)
            ''')
            
            # Create initial budget categories
            categories = ['Salaries', 'Equipment', 'Infrastructure', 'Research', 'Miscellaneous']
            for category in categories:
                conn.execute('INSERT INTO BudgetCategories (name) VALUES (?)', (category,))
                
            print("Sample data created successfully!")
        except Exception as e:
            print(f"Error creating sample data: {e}")
    
    # Checking if users table is empty even if departments exist
    user_count = conn.execute("SELECT COUNT(*) FROM Users").fetchone()[0]
    if user_count == 0:
        print("No users found. Creating default users...")
        try:
            # Create a default admin user if departments exist
            admin_hash = pbkdf2_sha256.hash("admin123")
            
            # Get administration department ID
            admin_dept = conn.execute("SELECT id FROM Departments WHERE name = 'Administration'").fetchone()
            if admin_dept:
                admin_dept_id = admin_dept['id']
                conn.execute('''
                    INSERT INTO Users (username, hashed_password, department_id)
                    VALUES (?, ?, ?)
                ''', ('admin', admin_hash, admin_dept_id))
                print("Default admin user created!")
            else:
                # If Administration department doesn't exist, create it first
                conn.execute("INSERT INTO Departments (name, parent_id) VALUES ('Administration', NULL)")
                dept_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.execute('''
                    INSERT INTO Users (username, hashed_password, department_id)
                    VALUES (?, ?, ?)
                ''', ('admin', admin_hash, dept_id))
                print("Created Administration department and default admin user!")
        except Exception as e:
            print(f"Error creating default user: {e}")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

print("About to initialize database...")
# Initialize the database when this module is imported
init_db()
print("Database initialization complete!") 