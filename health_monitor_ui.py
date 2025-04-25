import streamlit as st
import requests
import time
import datetime
import pandas as pd
import json
import os

# Configure the page
st.set_page_config(
    page_title="Microservices Health Monitor",
    page_icon="🔍",
    layout="wide"
)

# Service endpoints to check
SERVICES = [
    {
        "name": "Budgeting Service API",
        "url": "http://localhost:5000/api/health",
        "description": "Handles authentication, departments, and budgeting data",
        "last_status": None,
        "last_checked": None,
        "uptime": 0,
        "response_time": 0
    },
    {
        "name": "Budgeting Service UI",
        "url": "http://localhost:8501",
        "description": "User interface for budgeting management",
        "last_status": None,
        "last_checked": None,
        "uptime": 0,
        "response_time": 0
    },
    {
        "name": "Communication Service UI",
        "url": "http://localhost:8502",
        "description": "User interface for interdepartmental communication",
        "last_status": None,
        "last_checked": None,
        "uptime": 0,
        "response_time": 0
    }
]

# Initialize session state for storing service status history
if 'status_history' not in st.session_state:
    st.session_state.status_history = {service['name']: [] for service in SERVICES}
    
if 'incident_log' not in st.session_state:
    st.session_state.incident_log = []
    
if 'check_count' not in st.session_state:
    st.session_state.check_count = 0
    
if 'last_check_time' not in st.session_state:
    st.session_state.last_check_time = None
    
if 'paused' not in st.session_state:
    st.session_state.paused = False
    
# Maximum history points to keep
MAX_HISTORY_POINTS = 100

def check_service(service):
    """Check if a service is available and update its status"""
    now = datetime.datetime.now()
    service["last_checked"] = now
    
    try:
        start_time = time.time()
        response = requests.get(service["url"], timeout=2)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        service["response_time"] = response_time
        
        if response.status_code == 200:
            # Service is up
            was_down = service["last_status"] is False
            service["last_status"] = True
            
            if was_down:
                # Service was down but is now up
                incident = {
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "service": service["name"],
                    "event": "RECOVERED",
                    "details": f"Service is now UP"
                }
                st.session_state.incident_log.insert(0, incident)
            
            # Extract uptime from health response if available
            if service["name"] == "Budgeting Service API":
                try:
                    data = response.json()
                    if "uptime_seconds" in data:
                        service["uptime"] = data["uptime_seconds"]
                except:
                    pass
                    
            return True
        else:
            # Service returned non-200 status
            was_up = service["last_status"] is True
            service["last_status"] = False
            
            if was_up or service["last_status"] is None:
                # Service was up but is now down, or first check
                incident = {
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "service": service["name"],
                    "event": "DOWN",
                    "details": f"Status code: {response.status_code}"
                }
                st.session_state.incident_log.insert(0, incident)
            return False
            
    except requests.RequestException as e:
        # Service is not responding
        was_up = service["last_status"] is True
        service["last_status"] = False
        
        if was_up or service["last_status"] is None:
            # Service was up but is now down, or first check
            incident = {
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "service": service["name"],
                "event": "DOWN",
                "details": f"Error: {str(e)[:100]}"
            }
            st.session_state.incident_log.insert(0, incident)
        return False

def update_service_status():
    """Update status for all services"""
    if not st.session_state.paused:
        for service in SERVICES:
            check_service(service)
            
            # Add current status to history
            history_point = {
                "timestamp": datetime.datetime.now(),
                "status": service["last_status"]
            }
            st.session_state.status_history[service['name']].append(history_point)
            
            # Trim history if too long
            if len(st.session_state.status_history[service['name']]) > MAX_HISTORY_POINTS:
                st.session_state.status_history[service['name']] = st.session_state.status_history[service['name']][-MAX_HISTORY_POINTS:]
        
        st.session_state.check_count += 1
        st.session_state.last_check_time = datetime.datetime.now()

def toggle_monitoring():
    """Toggle monitoring on/off"""
    st.session_state.paused = not st.session_state.paused

def clear_incident_log():
    """Clear the incident log"""
    st.session_state.incident_log = []

# Main title
st.title("University Microservices Health Monitor")

# Top metrics row
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Services", len(SERVICES))
    
with col2:
    healthy_count = sum(1 for service in SERVICES if service["last_status"] is True)
    st.metric("Healthy Services", healthy_count, f"{healthy_count - len(SERVICES)}" if healthy_count < len(SERVICES) else "")
    
with col3:
    last_check_time = st.session_state.last_check_time.strftime("%H:%M:%S") if st.session_state.last_check_time else "Never"
    st.metric("Last Check", last_check_time, f"Checks: {st.session_state.check_count}")

# Services status cards
st.subheader("Service Status")

# Create a row of cards for services
service_cols = st.columns(len(SERVICES))

for i, service in enumerate(SERVICES):
    with service_cols[i]:
        if service["last_status"] is True:
            status_color = "green"
            status_text = "ONLINE"
            icon = "✅"
        elif service["last_status"] is False:
            status_color = "red"
            status_text = "OFFLINE"
            icon = "❌"
        else:
            status_color = "gray"
            status_text = "UNKNOWN"
            icon = "❓"
            
        # Card title with status
        st.markdown(f"### {icon} {service['name']}")
        
        # Status indicator
        st.markdown(
            f"""
            <div style="background-color: {status_color}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-weight: bold;">
                {status_text}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Service details
        st.markdown(f"**Description:** {service['description']}")
        
        if service["last_checked"]:
            st.markdown(f"**Last checked:** {service['last_checked'].strftime('%H:%M:%S')}")
        
        if service["last_status"] is True:
            st.markdown(f"**Response time:** {service['response_time']:.2f} ms")
            
            if service["uptime"] > 0:
                uptime_minutes = service["uptime"] / 60
                uptime_hours = uptime_minutes / 60
                
                if uptime_hours >= 1:
                    st.markdown(f"**Uptime:** {uptime_hours:.2f} hours")
                else:
                    st.markdown(f"**Uptime:** {uptime_minutes:.2f} minutes")

# Status history charts
st.subheader("Status History")

# Prepare data for charts
for service_name, history in st.session_state.status_history.items():
    if history:
        # Convert status to 1 (up) or 0 (down)
        df = pd.DataFrame([
            {"timestamp": point["timestamp"], "status": 1 if point["status"] else 0}
            for point in history
        ])
        
        st.markdown(f"**{service_name}**")
        st.line_chart(df.set_index("timestamp")["status"], use_container_width=True, height=100)

# Incident log
st.subheader("Incident Log")

if st.session_state.incident_log:
    # Create a DataFrame for the incident log
    incident_df = pd.DataFrame(st.session_state.incident_log)
    
    # Display with custom formatting
    st.dataframe(
        incident_df,
        column_config={
            "timestamp": st.column_config.TextColumn("Time"),
            "service": st.column_config.TextColumn("Service"),
            "event": st.column_config.TextColumn("Event"),
            "details": st.column_config.TextColumn("Details")
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("No incidents recorded yet.")

# Controls section
st.subheader("Monitor Controls")

col1, col2 = st.columns(2)

with col1:
    if st.session_state.paused:
        if st.button("Resume Monitoring"):
            toggle_monitoring()
    else:
        if st.button("Pause Monitoring"):
            toggle_monitoring()
            
with col2:
    if st.button("Clear Incident Log"):
        clear_incident_log()

# Add information about refresh rate
st.info("The monitor automatically refreshes every few seconds. Click the button below to manually check services now.")

if st.button("Check Services Now"):
    update_service_status()

# Use st.empty() to create a placeholder for the auto-refresh
refresh_placeholder = st.empty()

# Automatically update services every 5 seconds if not paused
if not st.session_state.paused:
    update_service_status()

# Footer
st.markdown("---")
st.markdown("University Microservices Health Monitor | © 2023") 