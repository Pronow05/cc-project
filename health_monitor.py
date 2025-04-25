#!/usr/bin/env python3
import requests
import time
import os
import sys
import datetime
from colorama import init, Fore, Back, Style

# Initialize colorama for colored terminal output
init()

# Service endpoints to check
SERVICES = [
    {
        "name": "Budgeting Service API",
        "url": "http://localhost:5000/api/health",
        "last_status": None,
        "last_checked": None
    },
    {
        "name": "Budgeting Service UI",
        "url": "http://localhost:8501",
        "last_status": None,
        "last_checked": None
    },
    {
        "name": "Communication Service UI",
        "url": "http://localhost:8502",
        "last_status": None,
        "last_checked": None
    }
]

def check_service(service):
    """Check if a service is available and update its status"""
    now = datetime.datetime.now()
    service["last_checked"] = now
    
    try:
        response = requests.get(service["url"], timeout=2)
        
        if response.status_code == 200:
            # Service is up
            was_down = service["last_status"] is False
            service["last_status"] = True
            
            if was_down:
                # Service was down but is now up
                print(f"{Fore.GREEN}[{now}] {service['name']} is now UP{Style.RESET_ALL}")
            return True
        else:
            # Service returned non-200 status
            was_up = service["last_status"] is True
            service["last_status"] = False
            
            if was_up or service["last_status"] is None:
                # Service was up but is now down, or first check
                print(f"{Fore.RED}[{now}] {service['name']} is DOWN (Status code: {response.status_code}){Style.RESET_ALL}")
            return False
            
    except requests.RequestException as e:
        # Service is not responding
        was_up = service["last_status"] is True
        service["last_status"] = False
        
        if was_up or service["last_status"] is None:
            # Service was up but is now down, or first check
            print(f"{Fore.RED}[{now}] {service['name']} is DOWN (Error: {e}){Style.RESET_ALL}")
        return False

def display_status():
    """Display current status of all services"""
    now = datetime.datetime.now()
    print(f"\n{Fore.CYAN}===== Service Status at {now} ====={Style.RESET_ALL}")
    
    for service in SERVICES:
        if service["last_status"] is True:
            status = f"{Fore.GREEN}UP{Style.RESET_ALL}"
        elif service["last_status"] is False:
            status = f"{Fore.RED}DOWN{Style.RESET_ALL}"
        else:
            status = f"{Fore.YELLOW}UNKNOWN{Style.RESET_ALL}"
        
        print(f"{service['name']}: {status}")
    
    print(f"{Fore.CYAN}================================={Style.RESET_ALL}\n")

def main():
    """Main monitoring loop"""
    try:
        check_interval = 5  # seconds
        
        print(f"{Fore.CYAN}Starting University Microservices Health Monitor{Style.RESET_ALL}")
        print(f"Checking services every {check_interval} seconds. Press Ctrl+C to exit.")
        
        # Initial check
        for service in SERVICES:
            check_service(service)
        
        display_status()
        
        # Continuous monitoring
        while True:
            time.sleep(check_interval)
            
            # Check all services
            for service in SERVICES:
                check_service(service)
                
            # Periodically display full status (every minute)
            if datetime.datetime.now().second < check_interval:
                display_status()
                
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Health monitor stopped.{Style.RESET_ALL}")
        sys.exit(0)

if __name__ == "__main__":
    main() 