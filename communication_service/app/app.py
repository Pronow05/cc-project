import streamlit as st
import pandas as pd
from datetime import datetime
import db
import auth
import os

# Set page config
st.set_page_config(page_title="University Communication System", layout="wide")

# Initialize session state variables if they don't exist
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'department_id' not in st.session_state:
    st.session_state.department_id = None
if 'departments' not in st.session_state:
    st.session_state.departments = None
if 'department_hierarchy' not in st.session_state:
    st.session_state.department_hierarchy = None
if 'selected_message' not in st.session_state:
    st.session_state.selected_message = None
if 'current_view' not in st.session_state:
    st.session_state.current_view = "inbox"

# Login page
def login_page():
    st.title("University Communication System")
    
    # Add debug info about the budgeting service connection
    budgeting_api_url = os.environ.get('BUDGETING_API_URL', 'http://localhost:5000')
    st.info(f"Connecting to budgeting service at: {budgeting_api_url}")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            st.info(f"Attempting to authenticate user: {username}")
            user_data = auth.authenticate(username, password)
            
            if user_data:
                st.session_state.authenticated = True
                st.session_state.user_id = user_data['user_id']
                st.session_state.username = user_data['username']
                st.session_state.department_id = user_data['department_id']
                
                # Get departments from budgeting service
                st.info("Fetching departments from budgeting service...")
                departments = auth.get_departments()
                
                if not departments:
                    st.error("Could not fetch departments from budgeting service. Please check if it's running.")
                    return
                
                st.session_state.departments = departments
                
                # Build department hierarchy
                st.session_state.department_hierarchy = auth.build_department_hierarchy(departments)
                
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

# Logout function
def logout():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.session_state.authenticated = False
    st.session_state.current_view = "inbox"

# Helper function to format department hierarchy for display
def format_department_hierarchy(departments, parent_id=None, level=0):
    formatted = []
    hierarchy = st.session_state.department_hierarchy
    
    children = hierarchy["children_mapping"].get(parent_id, [])
    
    for dept_id in children:
        dept_name = hierarchy["department_names"].get(dept_id)
        formatted.append({
            'id': dept_id,
            'name': ('  ' * level) + dept_name,
        })
        # Add children recursively
        formatted.extend(format_department_hierarchy(departments, dept_id, level + 1))
    
    return formatted

# Helper function to get department name by ID
def get_department_name(dept_id):
    if not st.session_state.department_hierarchy:
        return f"Department {dept_id}"
    
    return st.session_state.department_hierarchy["department_names"].get(dept_id, f"Department {dept_id}")

# Compose message page
def compose_message():
    st.subheader("Compose New Message")
    
    # Get department hierarchy for selecting recipients
    hierarchy = st.session_state.department_hierarchy
    
    # Current user's department (sender)
    sender_dept_id = st.session_state.department_id
    sender_dept_name = get_department_name(sender_dept_id)
    
    st.write(f"**From:** {sender_dept_name}")
    
    # Format departments for selection
    formatted_depts = []
    for dept in st.session_state.departments:
        dept_id = dept.get('id')
        if dept_id != sender_dept_id:  # Don't show own department
            formatted_depts.append({
                'id': dept_id,
                'name': dept.get('name')
            })
    
    # Sort departments by name
    formatted_depts = sorted(formatted_depts, key=lambda x: x['name'])
    
    # Compose form
    with st.form("compose_form"):
        # Select recipients (multiselect)
        recipient_options = {d['name']: d['id'] for d in formatted_depts}
        selected_recipients = st.multiselect(
            "To:",
            options=list(recipient_options.keys())
        )
        
        subject = st.text_input("Subject")
        message_body = st.text_area("Message", height=200)
        
        submit = st.form_submit_button("Send Message")
        
        if submit:
            if not selected_recipients:
                st.error("Please select at least one recipient department.")
            elif not subject:
                st.error("Please enter a subject.")
            elif not message_body:
                st.error("Please enter a message.")
            else:
                # Get recipient department IDs
                recipient_dept_ids = [recipient_options[name] for name in selected_recipients]
                
                # Create message
                success = db.create_message(sender_dept_id, recipient_dept_ids, subject, message_body)
                
                if success:
                    st.success("Message sent successfully!")
                    st.session_state.current_view = "inbox"
                    st.experimental_rerun()
                else:
                    st.error("Error sending message. Please try again.")

# View message details
def view_message(message_id):
    message = db.get_message_details(message_id)
    
    if not message:
        st.error("Message not found.")
        st.session_state.selected_message = None
        st.experimental_rerun()
        return
    
    # Display message details
    st.subheader(message['subject'])
    
    # Message metadata
    sender_name = get_department_name(message['sender_department_id'])
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.write("**From:**")
        st.write("**To:**")
        st.write("**Date:**")
    
    with col2:
        st.write(sender_name)
        
        # Format recipients
        recipient_names = [get_department_name(dept_id) for dept_id in message['recipient_dept_ids']]
        st.write(", ".join(recipient_names))
        
        # Format timestamp
        timestamp = datetime.fromisoformat(message['timestamp'])
        st.write(timestamp.strftime("%Y-%m-%d %H:%M:%S"))
    
    # Message body
    st.markdown("---")
    st.write(message['body'])
    
    # Back button
    if st.button("Back to " + ("Inbox" if st.session_state.current_view == "inbox" else "Sent Messages")):
        st.session_state.selected_message = None
        st.experimental_rerun()

# Inbox page
def inbox_page():
    st.subheader("Inbox")
    
    # Get user's department
    dept_id = st.session_state.department_id
    
    # Get parent departments
    parent_depts = st.session_state.department_hierarchy["all_parents"].get(dept_id, [])
    
    # Get messages
    messages = db.get_inbox_messages(dept_id, parent_depts)
    
    if not messages:
        st.info("Your inbox is empty.")
        return
    
    # Display messages as a table
    data = []
    for msg in messages:
        sender_name = get_department_name(msg['sender_department_id'])
        
        # Format timestamp
        timestamp = datetime.fromisoformat(msg['timestamp'])
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
        
        # Add to data
        data.append({
            "ID": msg['id'],
            "From": sender_name,
            "Subject": msg['subject'],
            "Date": formatted_time,
            "Recipients": msg['recipient_count']
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Display as a clickable table
    selected_indices = st.dataframe(
        df,
        column_config={
            "ID": None,  # Hide ID column
            "From": st.column_config.TextColumn("From"),
            "Subject": st.column_config.TextColumn("Subject"),
            "Date": st.column_config.TextColumn("Date"),
            "Recipients": st.column_config.NumberColumn("Recipients")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Handle message selection
    for i, row in enumerate(data):
        col1 = st.container()
        is_clicked = col1.button(f"View", key=f"view_inbox_{row['ID']}")
        if is_clicked:
            st.session_state.selected_message = row['ID']
            st.experimental_rerun()

# Sent messages page
def sent_page():
    st.subheader("Sent Messages")
    
    # Get user's department
    dept_id = st.session_state.department_id
    
    # Get messages
    messages = db.get_sent_messages(dept_id)
    
    if not messages:
        st.info("You haven't sent any messages yet.")
        return
    
    # Display messages as a table
    data = []
    for msg in messages:
        # Format timestamp
        timestamp = datetime.fromisoformat(msg['timestamp'])
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M")
        
        # Add to data
        data.append({
            "ID": msg['id'],
            "To": f"{msg['recipient_count']} recipient(s)",
            "Subject": msg['subject'],
            "Date": formatted_time
        })
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Display as a clickable table
    st.dataframe(
        df,
        column_config={
            "ID": None,  # Hide ID column
            "To": st.column_config.TextColumn("To"),
            "Subject": st.column_config.TextColumn("Subject"),
            "Date": st.column_config.TextColumn("Date")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Handle message selection
    for i, row in enumerate(data):
        col1 = st.container()
        is_clicked = col1.button(f"View", key=f"view_sent_{row['ID']}")
        if is_clicked:
            st.session_state.selected_message = row['ID']
            st.experimental_rerun()

# Main application
def main_app():
    # Sidebar
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.write(f"Department: {get_department_name(st.session_state.department_id)}")
    
    # Navigation
    st.sidebar.markdown("## Navigation")
    
    if st.sidebar.button("📥 Inbox"):
        st.session_state.current_view = "inbox"
        st.session_state.selected_message = None
        st.experimental_rerun()
    
    if st.sidebar.button("📤 Sent Messages"):
        st.session_state.current_view = "sent"
        st.session_state.selected_message = None
        st.experimental_rerun()
    
    if st.sidebar.button("✏️ Compose New Message"):
        st.session_state.current_view = "compose"
        st.session_state.selected_message = None
        st.experimental_rerun()
    
    # Logout button
    if st.sidebar.button("Logout"):
        logout()
        st.experimental_rerun()
    
    # Main content area
    if st.session_state.selected_message:
        view_message(st.session_state.selected_message)
    elif st.session_state.current_view == "inbox":
        inbox_page()
    elif st.session_state.current_view == "sent":
        sent_page()
    elif st.session_state.current_view == "compose":
        compose_message()

# Application entry point
if st.session_state.authenticated:
    main_app()
else:
    login_page() 