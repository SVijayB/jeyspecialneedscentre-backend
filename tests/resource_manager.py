"""
Resource manager for creating and managing shared test resources
Handles dependencies like branches before users, users before attendance
"""

from base_test import BaseIntegrationTest
from datetime import datetime, date, timedelta

class ResourceManager(BaseIntegrationTest):
    """Manages creation and cleanup of shared test resources"""
    
    def __init__(self):
        super().__init__()
        self.shared_branch = None
        self.shared_supervisor = None
        self.shared_therapist = None
    
    def create_test_branch(self, name: str = None) -> dict:
        """Create a test branch"""
        if not name:
            name = f"TestBranch_{self.generate_unique_id()}"
        
        data = {"name": name}
        response = self.make_request('POST', '/api/auth/branches/', data)
        
        if response.status_code == 201:
            branch = response.json()
            self.track_created_resource('branches', branch['id'])
            return branch
        else:
            self.log_failure(f"Create branch {name}", response, 201)
            return None
    
    def create_test_user(self, role: str = "therapist", branch_id: int = None, 
                        supervisor_id: int = None) -> dict:
        """Create a test user with required fields"""
        unique_id = self.generate_unique_id()
        short_id = unique_id[-8:]  # Use last 8 characters to keep under 20 char limit
        clean_id = short_id.replace('_', '').replace('-', '')[-6:]  # Remove special chars for phone
        
        if not branch_id and self.shared_branch:
            branch_id = self.shared_branch['id']
        elif not branch_id:
            # Create a branch if none exists
            self.shared_branch = self.create_test_branch()
            branch_id = self.shared_branch['id'] if self.shared_branch else None
        
        if not branch_id:
            return None
        
        data = {
            "username": f"testuser_{short_id}",
            "email": f"test_{short_id}@example.com", 
            "employee_id": f"EMP_{short_id}",  # Keep under 20 chars
            "role": role,
            "branch": branch_id,
            "password": "testpass123",
            "mobile_number": f"+919876{clean_id}",  # Valid phone format
            "first_name": f"Test",
            "last_name": f"User_{short_id[-4:]}"
        }
        
        response = self.make_request('POST', '/api/auth/users/', data)
        
        if response.status_code == 201:
            user = response.json()
            # Get the user ID by fetching the created user since API doesn't return ID
            list_response = self.make_request('GET', '/api/auth/users/')
            if list_response.status_code == 200:
                users_data = list_response.json()
                users = users_data.get('results', users_data) if isinstance(users_data, dict) else users_data
                created_user = next((u for u in users if u.get('employee_id') == user['employee_id']), None)
                if created_user and 'id' in created_user:
                    user['id'] = created_user['id']
                    self.track_created_resource('users', user['id'])
                    return user
            
            self.log_failure(f"Create user {role} - could not get user ID", response, 201)
            return None
        else:
            self.log_failure(f"Create user {role}", response, 201)
            return None
    
    def create_shared_resources(self) -> bool:
        """Create shared resources needed across tests"""
        # Create shared branch
        self.shared_branch = self.create_test_branch("SharedTestBranch")
        if not self.shared_branch:
            return False
        
        # Create shared supervisor
        self.shared_supervisor = self.create_test_user("supervisor", self.shared_branch['id'])
        if not self.shared_supervisor:
            return False
        
        # Create shared therapist
        self.shared_therapist = self.create_test_user("therapist", self.shared_branch['id'])
        if not self.shared_therapist:
            return False
        
        return True
    
    def create_test_attendance(self, employee_id: int, attendance_date: str = None, 
                             status: str = "present") -> dict:
        """Create test attendance record"""
        if not attendance_date:
            attendance_date = date.today().strftime('%Y-%m-%d')
        
        data = {
            "employee": employee_id,
            "date": attendance_date,
            "status": status
        }
        
        # Add check_in_time for present status
        if status == "present":
            data["check_in_time"] = f"{attendance_date}T09:30:00Z"
            data["check_out_time"] = f"{attendance_date}T17:30:00Z"
        
        response = self.make_request('POST', '/api/attendance/attendance/', data)
        
        if response.status_code == 201:
            attendance = response.json()
            self.track_created_resource('attendance', attendance['id'])
            return attendance
        else:
            self.log_failure(f"Create attendance for employee {employee_id}", response, 201)
            return None
    
    def create_test_leave(self, employee_id: int, leave_type: str = "casual_leave",
                         days_offset: int = 7) -> dict:
        """Create test leave application"""
        start_date = (date.today() + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        end_date = (date.today() + timedelta(days=days_offset + 2)).strftime('%Y-%m-%d')
        
        data = {
            "employee": employee_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": f"Test {leave_type} application"
        }
        
        response = self.make_request('POST', '/api/attendance/leaves/', data)
        
        if response.status_code == 201:
            leave = response.json()
            self.track_created_resource('leaves', leave['id'])
            return leave
        else:
            self.log_failure(f"Create leave for employee {employee_id}", response, 201)
            return None
