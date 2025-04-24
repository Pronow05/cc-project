import os
import requests
import json
from passlib.hash import pbkdf2_sha256

# Get the budgeting API URL from environment variable or use a default for local development
BUDGETING_API_URL = os.environ.get('BUDGETING_API_URL', 'http://localhost:5000')
print(f"Using Budgeting API URL: {BUDGETING_API_URL}")

# Direct authentication fallback
# These are the same default users as in the budgeting service
DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "department_id": 1, "department_name": "Administration"},
    {"username": "user1", "password": "pass123", "department_id": 4, "department_name": "CSE"},
    {"username": "user2", "password": "pass123", "department_id": 6, "department_name": "AI"}
]

def direct_authenticate(username, password):
    """Direct authentication as a fallback when the budgeting API is unavailable"""
    print(f"Attempting direct authentication for user: {username}")
    
    for user in DEFAULT_USERS:
        if user["username"] == username and user["password"] == password:
            print(f"Direct authentication successful for user: {username}")
            return {
                "user_id": DEFAULT_USERS.index(user) + 1,
                "username": user["username"],
                "department_id": user["department_id"]
            }
    
    print(f"Direct authentication failed for user: {username}")
    return None

def authenticate(username, password):
    """Authenticate a user by calling the Budgeting service's API"""
    endpoint = f"{BUDGETING_API_URL}/api/authenticate"
    print(f"Authenticating user '{username}' against endpoint: {endpoint}")
    
    try:
        response = requests.post(
            endpoint, 
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10  # Add timeout to prevent hanging
        )
        
        print(f"Authentication response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Authentication successful for user: {username}")
            return data
        else:
            print(f"Authentication failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
            
            # Try direct authentication as fallback
            print("Trying direct authentication as fallback...")
            return direct_authenticate(username, password)
        
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error when authenticating: {e}")
        print(f"Could not connect to {endpoint}. Trying direct authentication...")
        return direct_authenticate(username, password)
    except Exception as e:
        print(f"Authentication error: {e}")
        print("Trying direct authentication as fallback...")
        return direct_authenticate(username, password)

def get_departments():
    """Get the list of departments from the Budgeting service's API"""
    endpoint = f"{BUDGETING_API_URL}/api/departments"
    print(f"Fetching departments from: {endpoint}")
    
    try:
        response = requests.get(endpoint, timeout=10)
        
        print(f"Departments response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Received {len(data)} departments")
            return data
        else:
            print(f"Failed to fetch departments with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print(f"Response text: {response.text}")
            
            # Return default departments as fallback
            print("Returning default departments as fallback")
            return DEFAULT_DEPARTMENTS
        
        return []
    except requests.exceptions.ConnectionError as e:
        print(f"Connection error when fetching departments: {e}")
        print(f"Could not connect to {endpoint}. Returning default departments.")
        return DEFAULT_DEPARTMENTS
    except Exception as e:
        print(f"Error getting departments: {e}")
        print("Returning default departments as fallback")
        return DEFAULT_DEPARTMENTS

def build_department_hierarchy(departments):
    """
    Build a department hierarchy mapping
    Returns:
    - department_names: dict mapping dept_id to name
    - parent_mapping: dict mapping dept_id to parent_id
    - children_mapping: dict mapping parent_id to list of child dept_ids
    - all_parents: dict mapping dept_id to list of all ancestor dept_ids
    """
    department_names = {}
    parent_mapping = {}
    children_mapping = {}
    
    # Build basic mappings
    for dept in departments:
        dept_id = dept.get('id')
        parent_id = dept.get('parent_id')
        name = dept.get('name')
        
        department_names[dept_id] = name
        parent_mapping[dept_id] = parent_id
        
        if parent_id not in children_mapping:
            children_mapping[parent_id] = []
        children_mapping[parent_id].append(dept_id)
    
    # Build list of all parent ancestors for each department
    all_parents = {}
    
    def get_all_parents(dept_id):
        if dept_id in all_parents:
            return all_parents[dept_id]
        
        result = []
        parent_id = parent_mapping.get(dept_id)
        
        if parent_id:
            result.append(parent_id)
            result.extend(get_all_parents(parent_id))
        
        all_parents[dept_id] = result
        return result
    
    # Calculate all parents for each department
    for dept_id in department_names.keys():
        all_parents[dept_id] = get_all_parents(dept_id)
    
    return {
        "department_names": department_names,
        "parent_mapping": parent_mapping,
        "children_mapping": children_mapping,
        "all_parents": all_parents
    }

# Default departments when API is not available
DEFAULT_DEPARTMENTS = [
    {"id": 1, "name": "Administration", "parent_id": None},
    {"id": 2, "name": "BTech", "parent_id": None},
    {"id": 3, "name": "MTech", "parent_id": None},
    {"id": 4, "name": "CSE", "parent_id": 2},
    {"id": 5, "name": "ECE", "parent_id": 2},
    {"id": 6, "name": "AI", "parent_id": 3},
    {"id": 7, "name": "Robotics", "parent_id": 3}
] 