"""
User integration tests
Tests user CRUD operations with REAL API calls and data
"""

import sys
import argparse
from base_test import BaseIntegrationTest, TestResults
from resource_manager import ResourceManager
from colors import Colors

class UserIntegrationTests(BaseIntegrationTest):
    """Integration tests for user management endpoints"""
    
    def __init__(self):
        super().__init__()
        self.results = TestResults()
        self.resource_manager = ResourceManager()
        self.test_users = []
        self.test_branch = None
    
    def setup_dependencies(self) -> bool:
        """Create required dependencies"""
        if not self.authenticate():
            return False
        
        # Initialize resource manager with our session
        self.resource_manager.session = self.session
        self.resource_manager.token = self.token
        
        # Create test branch
        self.test_branch = self.resource_manager.create_test_branch()
        if not self.test_branch:
            return False
        
        return True
    
    def test_create_therapist(self) -> bool:
        """Test creating a therapist user"""
        try:
            if not self.test_branch:
                self.log_failure("Create therapist", error="No test branch available - setup failed")
                return False
            
            unique_id = self.generate_unique_id()
            short_id = unique_id[-8:]  # Use last 8 characters to keep it short
            clean_id = short_id.replace('_', '').replace('-', '')[-6:]  # Remove special chars for phone
            data = {
                "username": f"therapist_{short_id}",
                "email": f"therapist_{short_id}@test.com",
                "employee_id": f"TH_{short_id}",  # Keep under 20 chars
                "role": "therapist",
                "branch": self.test_branch['id'],
                "password": "testpass123",
                "mobile_number": f"+919876{clean_id}",  # Valid phone format
                "first_name": "Test",
                "last_name": "Therapist"
            }
            
            response = self.make_request('POST', '/api/auth/users/', data)
            
            if response.status_code == 201:
                user = response.json()
                # UserCreateSerializer only returns submitted fields (no ID)
                required_fields = ['username', 'employee_id', 'role', 'email']
                if all(field in user for field in required_fields):
                    if user['role'] == 'therapist' and user['employee_id'] == data['employee_id']:
                        # Get the user ID by fetching the created user
                        list_response = self.make_request('GET', '/api/auth/users/')
                        if list_response.status_code == 200:
                            users_data = list_response.json()
                            users = users_data.get('results', users_data) if isinstance(users_data, dict) else users_data
                            created_user = next((u for u in users if u.get('employee_id') == user['employee_id']), None)
                            if created_user and 'id' in created_user:
                                user['id'] = created_user['id']
                                self.track_created_resource('users', user['id'])
                                self.test_users.append(user)
                                return True
                        
                        # If we can't get the ID from list, still consider success
                        self.test_users.append(user)
                        return True
                
                self.log_failure("Create therapist - invalid response", response)
                return False
            else:
                self.log_failure("Create therapist", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create therapist", error=str(e))
            return False
    
    def test_create_supervisor(self) -> bool:
        """Test creating a supervisor user"""
        try:
            if not self.test_branch:
                return False
            
            unique_id = self.generate_unique_id()
            short_id = unique_id[-8:]  # Use last 8 characters to keep it short
            clean_id = short_id.replace('_', '').replace('-', '')[-6:]  # Remove special chars for phone
            data = {
                "username": f"supervisor_{short_id}",
                "email": f"supervisor_{short_id}@test.com",
                "employee_id": f"SU_{short_id}",  # Keep under 20 chars
                "role": "supervisor",
                "branch": self.test_branch['id'],
                "password": "testpass123",
                "mobile_number": f"+919876{clean_id}",  # Valid phone format
                "first_name": "Test",
                "last_name": "Supervisor"
            }
            
            response = self.make_request('POST', '/api/auth/users/', data)
            
            if response.status_code == 201:
                user = response.json()
                if user['role'] == 'supervisor' and user['employee_id'] == data['employee_id']:
                    # Get the user ID by fetching the created user
                    list_response = self.make_request('GET', '/api/auth/users/')
                    if list_response.status_code == 200:
                        users_data = list_response.json()
                        users = users_data.get('results', users_data) if isinstance(users_data, dict) else users_data
                        created_user = next((u for u in users if u.get('employee_id') == user['employee_id']), None)
                        if created_user and 'id' in created_user:
                            user['id'] = created_user['id']
                            self.track_created_resource('users', user['id'])
                            self.test_users.append(user)
                            return True
                    
                    # If we can't get the ID from list, still consider success
                    self.test_users.append(user)
                    return True
                
                self.log_failure("Create supervisor - invalid response", response)
                return False
            else:
                self.log_failure("Create supervisor", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create supervisor", error=str(e))
            return False
    
    def test_list_users(self) -> bool:
        """Test listing all users"""
        try:
            response = self.make_request('GET', '/api/auth/users/')
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle paginated or direct array response
                users = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(users, list):
                    # Check if our created users are in the list by employee_id
                    created_employee_ids = [u['employee_id'] for u in self.test_users if 'employee_id' in u]
                    
                    # Get all users from all pages
                    all_users = users[:]
                    next_url = result.get('next') if isinstance(result, dict) else None
                    
                    while next_url:
                        # Extract just the query part for next page
                        import urllib.parse
                        parsed = urllib.parse.urlparse(next_url)
                        query = parsed.query
                        page_response = self.make_request('GET', f'/api/auth/users/?{query}')
                        if page_response.status_code == 200:
                            page_result = page_response.json()
                            page_users = page_result.get('results', [])
                            all_users.extend(page_users)
                            next_url = page_result.get('next')
                        else:
                            break
                    
                    listed_employee_ids = [u['employee_id'] for u in all_users if 'employee_id' in u]
                    
                    if all(emp_id in listed_employee_ids for emp_id in created_employee_ids):
                        return True
                    else:
                        self.log_failure("List users - missing created users", response)
                        return False
                else:
                    self.log_failure("List users - invalid response format", response)
                    return False
            else:
                self.log_failure("List users", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("List users", error=str(e))
            return False
    
    def test_get_user_detail(self) -> bool:
        """Test getting user details"""
        try:
            if not self.test_users:
                return False
            
            # Get user ID, might need to look it up if not available
            user = self.test_users[0]
            user_id = user.get('id')
            
            if not user_id:
                # Look up user by employee_id
                list_response = self.make_request('GET', '/api/auth/users/')
                if list_response.status_code == 200:
                    users_data = list_response.json()
                    users = users_data.get('results', users_data) if isinstance(users_data, dict) else users_data
                    found_user = next((u for u in users if u.get('employee_id') == user['employee_id']), None)
                    if found_user:
                        user_id = found_user['id']
                    else:
                        return False
                else:
                    return False
            
            response = self.make_request('GET', f'/api/auth/users/{user_id}/')
            
            if response.status_code == 200:
                user_detail = response.json()
                required_fields = ['id', 'username', 'employee_id', 'role', 'email']
                if all(field in user_detail for field in required_fields):
                    if user_detail['id'] == user_id:
                        return True
                
                self.log_failure("Get user detail - invalid response", response)
                return False
            else:
                self.log_failure("Get user detail", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Get user detail", error=str(e))
            return False
    
    def test_update_user(self) -> bool:
        """Test updating user information"""
        try:
            if not self.test_users:
                return False
            
            # Get user ID, might need to look it up if not available
            user = self.test_users[0]
            user_id = user.get('id')
            
            if not user_id:
                # Look up user by employee_id
                list_response = self.make_request('GET', '/api/auth/users/')
                if list_response.status_code == 200:
                    users_data = list_response.json()
                    users = users_data.get('results', users_data) if isinstance(users_data, dict) else users_data
                    found_user = next((u for u in users if u.get('employee_id') == user['employee_id']), None)
                    if found_user:
                        user_id = found_user['id']
                    else:
                        return False
                else:
                    return False
            
            new_email = f"updated_{self.generate_unique_id()}@test.com"
            data = {"email": new_email}
            
            response = self.make_request('PATCH', f'/api/auth/users/{user_id}/', data)
            
            if response.status_code == 200:
                updated_user = response.json()
                if updated_user.get('email') == new_email and updated_user.get('id') == user_id:
                    # Update our local copy
                    self.test_users[0]['email'] = new_email
                    return True
                
                self.log_failure("Update user - email not updated", response)
                return False
            else:
                self.log_failure("Update user", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Update user", error=str(e))
            return False
    
    def test_create_user_duplicate_employee_id(self) -> bool:
        """Test creating user with duplicate employee_id"""
        try:
            if not self.test_users or not self.test_branch:
                return False
            
            # Try to create user with same employee_id
            existing_emp_id = self.test_users[0]['employee_id']
            unique_id = self.generate_unique_id()
            
            data = {
                "username": f"duplicate_{unique_id}",
                "email": f"duplicate_{unique_id}@test.com",
                "employee_id": existing_emp_id,  # Duplicate
                "role": "therapist",
                "branch": self.test_branch['id'],
                "password": "testpass123",
                "mobile_number": f"+91{unique_id[-10:]}",
                "first_name": "Test",
                "last_name": "Duplicate"
            }
            
            response = self.make_request('POST', '/api/auth/users/', data)
            
            if response.status_code == 400:
                result = response.json()
                if 'employee_id' in result or 'error' in result:
                    return True
                
            self.log_failure("Create user duplicate employee_id", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Create user duplicate employee_id", error=str(e))
            return False
    
    def test_create_user_invalid_data(self) -> bool:
        """Test creating user with missing required fields"""
        try:
            # Missing required fields
            data = {"username": "incomplete_user"}
            
            response = self.make_request('POST', '/api/auth/users/', data)
            
            if response.status_code == 400:
                result = response.json()
                # Should have validation errors for missing fields
                required_fields = ['email', 'employee_id', 'role', 'branch']
                if any(field in result for field in required_fields):
                    return True
                
            self.log_failure("Create user invalid data", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Create user invalid data", error=str(e))
            return False
    
    def test_get_current_user_profile(self) -> bool:
        """Test getting current user profile (/me endpoint)"""
        try:
            response = self.make_request('GET', '/api/auth/users/me/')
            
            if response.status_code == 200:
                user = response.json()
                required_fields = ['id', 'username', 'role']
                if all(field in user for field in required_fields):
                    # Should return admin user info
                    if user.get('username') == 'admin':
                        return True
                
                self.log_failure("Get current user - invalid response", response)
                return False
            else:
                self.log_failure("Get current user", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Get current user", error=str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """Run all user tests"""
        print("Running User Integration Tests...")
        
        # Setup dependencies first
        if not self.setup_dependencies():
            print("Failed to setup dependencies")
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0, "failed_details": []}
        
        tests = [
            ("Create Therapist", self.test_create_therapist),
            ("Create Supervisor", self.test_create_supervisor),
            ("List Users", self.test_list_users),
            ("Get User Detail", self.test_get_user_detail),
            ("Update User", self.test_update_user),
            ("Create User Duplicate Employee ID", self.test_create_user_duplicate_employee_id),
            ("Create User Invalid Data", self.test_create_user_invalid_data),
            ("Get Current User Profile", self.test_get_current_user_profile),
        ]
        
        for test_name, test_func in tests:
            print(f"  Running: {test_name}")
            try:
                passed = test_func()
                self.results.add_test_result(test_name, passed)
                if passed:
                    print(f"    {Colors.pass_text()}")
                else:
                    print(f"    {Colors.fail_text()} - Check test_logs/integration_test_failures.log")
            except Exception as e:
                self.results.add_test_result(test_name, False, str(e))
                print(f"    {Colors.fail_text()} - {str(e)}")
        
        return self.results.get_summary()
    
    def cleanup(self):
        """Clean up created users and dependencies"""
        print("Cleaning up created users and branches...")
        self.cleanup_resources()
        self.resource_manager.cleanup_resources()

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Run user integration tests')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after tests')
    args = parser.parse_args()
    
    test_runner = UserIntegrationTests()
    
    try:
        results = test_runner.run_all_tests()
        
        print(f"\nUser Tests Summary:")
        print(f"Total: {results['total']}, Passed: {results['passed']}, Failed: {results['failed']}")
        print(f"Pass Rate: {results['pass_rate']}%")
        
        if results['failed_details']:
            print("\nFailed Tests:")
            for failure in results['failed_details']:
                print(f"  - {failure['test']}: {failure['error']}")
        
        if args.cleanup:
            test_runner.cleanup()
            print("\nCleanup completed.")
        
        return results['failed'] == 0
        
    except Exception as e:
        print(f"Test execution failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
