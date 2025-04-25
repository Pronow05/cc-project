# University Administration Microservices

This project implements two independent but integrated microservices for a university administration website:

1. **University Budgeting**: Handles allocation and tracking of funds for university departments
2. **Interdepartmental Communication**: Facilitates messaging between university departments

## Architecture

The system uses:
- Python backend with Streamlit for frontend UI
- SQLite for databases
- Docker for containerization
- Flask for API endpoints

## Microservices

### Budgeting Service (Port 8501)

This service manages:
- Departmental hierarchies (e.g., BTech → CSE)
- Fiscal years
- Budget categories
- Fund allocations
- Expenditure tracking
- User authentication

The budgeting service acts as the source of truth for Department definitions and User authentication.

#### API Endpoints:
- `GET /api/departments`: Returns a list of all departments
- `POST /api/authenticate`: Authenticates users

### Communication Service (Port 8502)

This service enables:
- Sending messages between departments
- Viewing received messages
- Maintaining message history

The communication service relies on the budgeting service for:
- Department information
- User authentication

## Data Models

### Budgeting Service
- **Departments**: Hierarchical structure of university departments
- **Users**: Authentication and department association
- **FiscalYears**: Budget periods
- **BudgetCategories**: Types of budget allocations
- **Allocations**: Budget amounts per department, category, and fiscal year
- **Expenditures**: Spending against allocations

### Communication Service
- **Messages**: Sent messages with subject, body, sender, timestamp
- **MessageRecipients**: Message recipients (supports multiple recipients)

## Running the Application

### Prerequisites
- Docker and Docker Compose

### Steps
1. Clone the repository
2. Run the application:
   ```
   docker-compose up --build
   ```
3. Access the services:
   - Budgeting: http://localhost:8501
   - Communication: http://localhost:8502

### Default Users
- **Admin**: Username: `admin`, Password: `admin123`, Department: Administration
- **User1**: Username: `user1`, Password: `pass123`, Department: CSE
- **User2**: Username: `user2`, Password: `pass123`, Department: AI

## Demo Workflow

1. Log in to the budgeting service and set up departments, fiscal years, and budget categories
2. Allocate funds to departments
3. Record expenditures against allocations
4. View department budget summaries
5. Log in to the communication service
6. Send messages between departments
7. View received messages in your department's inbox

## Health Monitoring

The project includes both a command-line and visual health monitoring system that checks the status of all services and alerts when one goes down.

### Prerequisites
- Python 3.x
- Additional packages: `pip install -r monitor_requirements.txt`

### Command-Line Health Monitor
```bash
python health_monitor.py
```

This will:
- Check all services every 5 seconds
- Display the current status of all services in the terminal
- Alert with red text when a service goes down
- Alert with green text when a service comes back up

### Visual Health Monitoring Dashboard
```bash
streamlit run health_monitor_ui.py
```

This will launch a browser-based dashboard that provides:
- Visual status cards for each service showing whether they're online or offline
- Real-time status history charts
- Incident log with timestamps
- Service response time measurements
- Controls to pause/resume monitoring or clear the incident log

The dashboard automatically refreshes and provides a complete picture of your microservices health.

### Testing Service Failures

To test how the system handles service failures:

1. Start all services with `docker-compose up`
2. Start either health monitor in a separate terminal
3. To stop only the budgeting service:
   ```bash
   docker-compose stop budgeting
   ```
4. The health monitor will immediately show alerts that the budgeting service is down
5. The communication service will continue to function in fallback mode
6. To restart the budgeting service:
   ```bash
   docker-compose start budgeting
   ```
7. The health monitor will show alerts when the budgeting service comes back online 