import streamlit as st
import pandas as pd
from datetime import datetime
import db
import sqlite3

# Set page config
st.set_page_config(page_title="University Budgeting System", layout="wide")

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'department_id' not in st.session_state:
    st.session_state.department_id = None

# Authentication function
def authenticate(username, password):
    """Authenticate a user with username and password"""
    conn = db.get_db_connection()
    user = conn.execute(
        'SELECT id, username, department_id FROM Users WHERE username = ?', 
        (username,)
    ).fetchone()
    conn.close()
    
    if user:
        from passlib.hash import pbkdf2_sha256
        conn = db.get_db_connection()
        stored_hash = conn.execute(
            'SELECT hashed_password FROM Users WHERE id = ?', (user['id'],)
        ).fetchone()['hashed_password']
        conn.close()
        
        if pbkdf2_sha256.verify(password, stored_hash):
            st.session_state.authenticated = True
            st.session_state.user_id = user['id']
            st.session_state.username = user['username']
            st.session_state.department_id = user['department_id']
            return True
    
    return False

# Logout function
def logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.username = None
    st.session_state.department_id = None

# Login page
def login_page():
    st.title("University Budgeting System")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if authenticate(username, password):
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# Helper function to get departments
def get_departments():
    conn = db.get_db_connection()
    departments = conn.execute('SELECT id, name, parent_id FROM Departments').fetchall()
    conn.close()
    return departments

# Helper function to get current fiscal year
def get_active_fiscal_year():
    conn = db.get_db_connection()
    fiscal_year = conn.execute('SELECT id, year_name FROM FiscalYears WHERE is_active = 1').fetchone()
    conn.close()
    return fiscal_year

# Helper function to format departments as a hierarchical tree for display
def format_department_hierarchy(departments, parent_id=None, level=0):
    formatted = []
    for dept in departments:
        if dept['parent_id'] == parent_id:
            formatted.append({
                'id': dept['id'],
                'name': ('  ' * level) + dept['name'],
                'parent_id': dept['parent_id']
            })
            # Add children recursively
            formatted.extend(format_department_hierarchy(departments, dept['id'], level + 1))
    return formatted

# Main application
def main_app():
    # Sidebar with navigation
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
        st.experimental_rerun()
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigate to",
        ["Department Management", "Fiscal Years", "Budget Categories", 
         "Allocations", "Expenditures", "Budget Overview"]
    )
    
    if page == "Department Management":
        department_page()
    elif page == "Fiscal Years":
        fiscal_year_page()
    elif page == "Budget Categories":
        budget_category_page()
    elif page == "Allocations":
        allocation_page()
    elif page == "Expenditures":
        expenditure_page()
    elif page == "Budget Overview":
        budget_overview_page()

# Department Management page
def department_page():
    st.title("Department Management")
    
    # Add new department
    with st.expander("Add New Department"):
        with st.form("add_department_form"):
            name = st.text_input("Department Name")
            
            # Get departments for parent selection
            departments = get_departments()
            formatted_depts = format_department_hierarchy(departments)
            
            dept_options = ["None"] + [d['name'] for d in formatted_depts]
            selected_parent = st.selectbox("Parent Department", dept_options)
            
            submit = st.form_submit_button("Add Department")
            
            if submit and name:
                parent_id = None
                if selected_parent != "None":
                    # Extract the actual department name (without the indentation spaces)
                    selected_name = selected_parent.strip()
                    for dept in departments:
                        if dept['name'] == selected_name:
                            parent_id = dept['id']
                            break
                
                conn = db.get_db_connection()
                conn.execute(
                    'INSERT INTO Departments (name, parent_id) VALUES (?, ?)',
                    (name, parent_id)
                )
                conn.commit()
                conn.close()
                st.success(f"Department '{name}' added successfully!")
                st.experimental_rerun()
    
    # View departments
    st.subheader("Department Hierarchy")
    departments = get_departments()
    formatted_depts = format_department_hierarchy(departments)
    
    if formatted_depts:
        df = pd.DataFrame(formatted_depts)
        st.dataframe(df[['id', 'name']], hide_index=True)
    else:
        st.info("No departments found.")

# Fiscal Year Management page
def fiscal_year_page():
    st.title("Fiscal Year Management")
    
    # Add new fiscal year
    with st.expander("Add New Fiscal Year"):
        with st.form("add_fiscal_year_form"):
            year_name = st.text_input("Fiscal Year (e.g., 2024-2025)")
            is_active = st.checkbox("Set as Active")
            
            submit = st.form_submit_button("Add Fiscal Year")
            
            if submit and year_name:
                conn = db.get_db_connection()
                
                # If setting as active, deactivate all other fiscal years
                if is_active:
                    conn.execute('UPDATE FiscalYears SET is_active = 0')
                
                conn.execute(
                    'INSERT INTO FiscalYears (year_name, is_active) VALUES (?, ?)',
                    (year_name, 1 if is_active else 0)
                )
                conn.commit()
                conn.close()
                st.success(f"Fiscal Year '{year_name}' added successfully!")
                st.experimental_rerun()
    
    # View and manage fiscal years
    st.subheader("Fiscal Years")
    
    conn = db.get_db_connection()
    fiscal_years = conn.execute('SELECT id, year_name, is_active FROM FiscalYears').fetchall()
    conn.close()
    
    if fiscal_years:
        for fy in fiscal_years:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"{fy['year_name']} {'(Active)' if fy['is_active'] else ''}")
            
            with col2:
                if not fy['is_active']:
                    if st.button(f"Set Active", key=f"activate_{fy['id']}"):
                        conn = db.get_db_connection()
                        conn.execute('UPDATE FiscalYears SET is_active = 0')
                        conn.execute('UPDATE FiscalYears SET is_active = 1 WHERE id = ?', (fy['id'],))
                        conn.commit()
                        conn.close()
                        st.success(f"Fiscal Year '{fy['year_name']}' set as active!")
                        st.experimental_rerun()
    else:
        st.info("No fiscal years found.")

# Budget Categories page
def budget_category_page():
    st.title("Budget Categories")
    
    # Add new budget category
    with st.expander("Add New Budget Category"):
        with st.form("add_category_form"):
            name = st.text_input("Category Name")
            submit = st.form_submit_button("Add Category")
            
            if submit and name:
                conn = db.get_db_connection()
                try:
                    conn.execute('INSERT INTO BudgetCategories (name) VALUES (?)', (name,))
                    conn.commit()
                    st.success(f"Category '{name}' added successfully!")
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    st.error(f"Category '{name}' already exists!")
                finally:
                    conn.close()
    
    # View categories
    st.subheader("Existing Categories")
    
    conn = db.get_db_connection()
    categories = conn.execute('SELECT id, name FROM BudgetCategories').fetchall()
    conn.close()
    
    if categories:
        df = pd.DataFrame(categories)
        st.dataframe(df, hide_index=True)
    else:
        st.info("No budget categories found.")

# Allocation page
def allocation_page():
    st.title("Budget Allocations")
    
    # Get active fiscal year
    active_fiscal_year = get_active_fiscal_year()
    if not active_fiscal_year:
        st.warning("No active fiscal year found. Please set an active fiscal year first.")
        return
    
    st.subheader(f"Manage Allocations for {active_fiscal_year['year_name']}")
    
    # Add new allocation
    with st.expander("Add New Allocation"):
        with st.form("add_allocation_form"):
            # Get departments
            departments = get_departments()
            formatted_depts = format_department_hierarchy(departments)
            dept_options = [d['name'] for d in formatted_depts]
            selected_dept = st.selectbox("Department", dept_options)
            
            # Get the actual department ID
            dept_id = None
            for dept in departments:
                if dept['name'] == selected_dept.strip():
                    dept_id = dept['id']
                    break
            
            # Get budget categories
            conn = db.get_db_connection()
            categories = conn.execute('SELECT id, name FROM BudgetCategories').fetchall()
            conn.close()
            
            category_options = [c['name'] for c in categories]
            selected_category = st.selectbox("Budget Category", category_options)
            
            # Get the category ID
            category_id = None
            for cat in categories:
                if cat['name'] == selected_category:
                    category_id = cat['id']
                    break
            
            amount = st.number_input("Amount", min_value=0.0, format="%f")
            
            submit = st.form_submit_button("Add Allocation")
            
            if submit and dept_id and category_id and amount > 0:
                conn = db.get_db_connection()
                try:
                    conn.execute('''
                        INSERT INTO Allocations 
                        (department_id, category_id, fiscal_year_id, amount) 
                        VALUES (?, ?, ?, ?)
                    ''', (dept_id, category_id, active_fiscal_year['id'], amount))
                    conn.commit()
                    st.success("Allocation added successfully!")
                    st.experimental_rerun()
                except sqlite3.IntegrityError:
                    # Update existing allocation
                    conn.execute('''
                        UPDATE Allocations 
                        SET amount = ?
                        WHERE department_id = ? AND category_id = ? AND fiscal_year_id = ?
                    ''', (amount, dept_id, category_id, active_fiscal_year['id']))
                    conn.commit()
                    st.success("Allocation updated successfully!")
                    st.experimental_rerun()
                finally:
                    conn.close()
    
    # View current allocations
    st.subheader("Current Allocations")
    
    conn = db.get_db_connection()
    allocations = conn.execute('''
        SELECT 
            a.id, 
            d.name AS department, 
            c.name AS category, 
            a.amount 
        FROM Allocations a
        JOIN Departments d ON a.department_id = d.id
        JOIN BudgetCategories c ON a.category_id = c.id
        WHERE a.fiscal_year_id = ?
    ''', (active_fiscal_year['id'],)).fetchall()
    conn.close()
    
    if allocations:
        # Convert to DataFrame
        allocation_data = [{
            'ID': a['id'],
            'Department': a['department'],
            'Category': a['category'],
            'Amount': f"${a['amount']:,.2f}"
        } for a in allocations]
        
        df = pd.DataFrame(allocation_data)
        st.dataframe(df, hide_index=True)
    else:
        st.info(f"No allocations found for {active_fiscal_year['year_name']}.")

# Expenditure page
def expenditure_page():
    st.title("Expenditures")
    
    # Get active fiscal year
    active_fiscal_year = get_active_fiscal_year()
    if not active_fiscal_year:
        st.warning("No active fiscal year found. Please set an active fiscal year first.")
        return
    
    st.subheader(f"Record Expenditures for {active_fiscal_year['year_name']}")
    
    # Add new expenditure
    with st.expander("Add New Expenditure"):
        with st.form("add_expenditure_form"):
            # Get departments
            departments = get_departments()
            formatted_depts = format_department_hierarchy(departments)
            dept_options = [d['name'] for d in formatted_depts]
            selected_dept = st.selectbox("Department", dept_options)
            
            # Get the actual department ID
            dept_id = None
            for dept in departments:
                if dept['name'] == selected_dept.strip():
                    dept_id = dept['id']
                    break
            
            # Get budget categories
            conn = db.get_db_connection()
            categories = conn.execute('SELECT id, name FROM BudgetCategories').fetchall()
            conn.close()
            
            category_options = [c['name'] for c in categories]
            selected_category = st.selectbox("Budget Category", category_options)
            
            # Get the category ID
            category_id = None
            for cat in categories:
                if cat['name'] == selected_category:
                    category_id = cat['id']
                    break
            
            # Get allocation ID if exists
            conn = db.get_db_connection()
            allocation = conn.execute('''
                SELECT id FROM Allocations 
                WHERE department_id = ? AND category_id = ? AND fiscal_year_id = ?
            ''', (dept_id, category_id, active_fiscal_year['id'])).fetchone()
            conn.close()
            
            if not allocation:
                st.warning("No allocation exists for this department and category. Please create an allocation first.")
                submit_disabled = True
            else:
                submit_disabled = False
                allocation_id = allocation['id']
            
            amount = st.number_input("Amount", min_value=0.0, format="%f")
            description = st.text_area("Description")
            date = st.date_input("Date", value=datetime.now().date())
            
            submit = st.form_submit_button("Record Expenditure", disabled=submit_disabled)
            
            if submit and amount > 0 and description and not submit_disabled:
                conn = db.get_db_connection()
                conn.execute('''
                    INSERT INTO Expenditures 
                    (allocation_id, amount, description, date) 
                    VALUES (?, ?, ?, ?)
                ''', (allocation_id, amount, description, date))
                conn.commit()
                conn.close()
                st.success("Expenditure recorded successfully!")
                st.experimental_rerun()
    
    # View expenditures
    st.subheader("Recent Expenditures")
    
    conn = db.get_db_connection()
    expenditures = conn.execute('''
        SELECT 
            e.id,
            d.name AS department,
            c.name AS category,
            e.amount,
            e.description,
            e.date
        FROM Expenditures e
        JOIN Allocations a ON e.allocation_id = a.id
        JOIN Departments d ON a.department_id = d.id
        JOIN BudgetCategories c ON a.category_id = c.id
        WHERE a.fiscal_year_id = ?
        ORDER BY e.date DESC
        LIMIT 20
    ''', (active_fiscal_year['id'],)).fetchall()
    conn.close()
    
    if expenditures:
        # Convert to DataFrame
        expenditure_data = [{
            'ID': e['id'],
            'Department': e['department'],
            'Category': e['category'],
            'Amount': f"${e['amount']:,.2f}",
            'Description': e['description'],
            'Date': e['date']
        } for e in expenditures]
        
        df = pd.DataFrame(expenditure_data)
        st.dataframe(df, hide_index=True)
    else:
        st.info(f"No expenditures found for {active_fiscal_year['year_name']}.")

# Budget Overview page
def budget_overview_page():
    st.title("Budget Overview")
    
    # Get active fiscal year
    active_fiscal_year = get_active_fiscal_year()
    if not active_fiscal_year:
        st.warning("No active fiscal year found. Please set an active fiscal year first.")
        return
    
    st.subheader(f"Budget Overview for {active_fiscal_year['year_name']}")
    
    # Get departments
    departments = get_departments()
    formatted_depts = format_department_hierarchy(departments)
    dept_options = ["All Departments"] + [d['name'] for d in formatted_depts]
    selected_dept = st.selectbox("Select Department", dept_options)
    
    # Calculate budget summary
    if selected_dept == "All Departments":
        # University-wide budget summary
        conn = db.get_db_connection()
        summary = conn.execute('''
            SELECT 
                c.name AS category,
                SUM(a.amount) AS allocated,
                COALESCE(SUM(e.amount), 0) AS spent
            FROM BudgetCategories c
            LEFT JOIN Allocations a ON c.id = a.category_id AND a.fiscal_year_id = ?
            LEFT JOIN Expenditures e ON a.id = e.allocation_id
            GROUP BY c.name
        ''', (active_fiscal_year['id'],)).fetchall()
        conn.close()
        
        title = "University-wide Budget Summary"
    else:
        # Department-specific budget summary
        # Get the department ID
        dept_id = None
        for dept in departments:
            if dept['name'] == selected_dept.strip():
                dept_id = dept['id']
                break
        
        conn = db.get_db_connection()
        
        # Get all child departments (recursive)
        all_depts = [dept_id]
        
        def get_child_departments(parent_id):
            children = conn.execute(
                'SELECT id FROM Departments WHERE parent_id = ?', 
                (parent_id,)
            ).fetchall()
            
            child_ids = [c['id'] for c in children]
            all_depts.extend(child_ids)
            
            for child_id in child_ids:
                get_child_departments(child_id)
        
        get_child_departments(dept_id)
        
        # Get budget summary including all child departments
        placeholders = ', '.join(['?'] * len(all_depts))
        query = f'''
            SELECT 
                c.name AS category,
                SUM(a.amount) AS allocated,
                COALESCE(SUM(e.amount), 0) AS spent
            FROM BudgetCategories c
            LEFT JOIN Allocations a ON c.id = a.category_id AND a.fiscal_year_id = ? AND a.department_id IN ({placeholders})
            LEFT JOIN Expenditures e ON a.id = e.allocation_id
            GROUP BY c.name
        '''
        
        params = [active_fiscal_year['id']] + all_depts
        summary = conn.execute(query, params).fetchall()
        conn.close()
        
        title = f"Budget Summary for {selected_dept}"
    
    # Display summary
    st.subheader(title)
    
    if summary:
        summary_data = []
        total_allocated = 0
        total_spent = 0
        
        for s in summary:
            allocated = s['allocated'] or 0
            spent = s['spent'] or 0
            remaining = allocated - spent
            
            total_allocated += allocated
            total_spent += spent
            
            if allocated > 0:  # Only show categories with allocations
                summary_data.append({
                    'Category': s['category'],
                    'Allocated': f"${allocated:,.2f}",
                    'Spent': f"${spent:,.2f}",
                    'Remaining': f"${remaining:,.2f}",
                    'Usage (%)': f"{(spent / allocated * 100) if allocated > 0 else 0:.1f}%"
                })
        
        # Add total row
        summary_data.append({
            'Category': 'TOTAL',
            'Allocated': f"${total_allocated:,.2f}",
            'Spent': f"${total_spent:,.2f}",
            'Remaining': f"${(total_allocated - total_spent):,.2f}",
            'Usage (%)': f"{(total_spent / total_allocated * 100) if total_allocated > 0 else 0:.1f}%"
        })
        
        df = pd.DataFrame(summary_data)
        st.dataframe(df, hide_index=True)
        
        # Budget usage visualization
        st.subheader("Budget Usage")
        
        progress = total_spent / total_allocated if total_allocated > 0 else 0
        st.progress(min(progress, 1.0))
        st.write(f"Overall Budget Usage: {progress * 100:.1f}%")
    else:
        st.info("No budget data available for the selected criteria.")

# Main application flow
if st.session_state.authenticated:
    main_app()
else:
    login_page()