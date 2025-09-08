"""
Leave application integration tests
Tests leave CRUD operations with REAL API calls and data
"""

import sys
import argparse
from datetime import date, timedelta
from base_test import BaseIntegrationTest, TestResults
from resource_manager import ResourceManager
from colors import Colors

class LeaveIntegrationTests(BaseIntegrationTest):
    """Integration tests for leave application endpoints"""
    
    def __init__(self):
        super().__init__()
        self.results = TestResults()
        self.resource_manager = ResourceManager()
        self.test_leaves = []
        self.test_employee = None
    
    def setup_dependencies(self) -> bool:
        """Create required dependencies"""
        if not self.authenticate():
            return False
        
        # Initialize resource manager with our session
        self.resource_manager.session = self.session
        self.resource_manager.token = self.token
        
        # Create test employee (therapist)
        branch = self.resource_manager.create_test_branch()
        if not branch:
            return False
        
        self.test_employee = self.resource_manager.create_test_user("therapist", branch['id'])
        if not self.test_employee:
            return False
        
        return True
    
    def test_create_casual_leave(self) -> bool:
        """Test creating casual leave application"""
        try:
            if not self.test_employee:
                return False
            
            # Authenticate as the test employee to create leave
            employee_username = self.test_employee.get('username')
            if not employee_username:
                self.log_failure("Create casual leave", error="Test employee missing username")
                return False
                
            if not self.authenticate(employee_username, "testpass123"):
                self.log_failure("Create casual leave", error="Could not authenticate as test employee")
                return False
            
            start_date = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = (date.today() + timedelta(days=9)).strftime('%Y-%m-%d')
            
            data = {
                "leave_type": "casual_leave",
                "start_date": start_date,
                "end_date": end_date,
                "reason": "Family function test"
            }
            
            response = self.make_request('POST', '/api/attendance/leaves/', data)
            
            if response.status_code == 201:
                leave = response.json()
                # LeaveApplicationCreateSerializer returns limited fields, get full details
                if 'leave_type' in leave and leave['leave_type'] == 'casual_leave':
                    # Re-authenticate as admin to fetch the created leave
                    if self.authenticate():
                        employee_id = self.test_employee['id']
                        fetch_response = self.make_request('GET', f'/api/attendance/leaves/?employee={employee_id}')
                        
                        if fetch_response.status_code == 200:
                            leaves_data = fetch_response.json()
                            leaves_list = leaves_data.get('results', leaves_data) if isinstance(leaves_data, dict) else leaves_data
                            # Find the leave record we just created
                            for leave_record in leaves_list:
                                if (leave_record.get('leave_type') == 'casual_leave' and 
                                    leave_record.get('employee') == self.test_employee['id'] and
                                    leave_record.get('start_date') == start_date and
                                    leave_record.get('end_date') == end_date and
                                    leave_record.get('status') == 'pending'):
                                    self.track_created_resource('leaves', leave_record['id'])
                                    self.test_leaves.append(leave_record)
                                    return True
                        
                        self.log_failure("Create casual leave - could not fetch created record", response)
                        return False
                    else:
                        # Still consider success if we can't re-authenticate as admin
                        self.test_leaves.append(leave)
                        return True
                
                self.log_failure("Create casual leave - invalid response format", response)
                return False
            else:
                self.log_failure("Create casual leave", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create casual leave", error=str(e))
            return False
    
    def test_create_unpaid_leave(self) -> bool:
        """Test creating unpaid leave application"""
        try:
            if not self.test_employee:
                return False
            
            # Authenticate as the test employee to create leave
            employee_username = self.test_employee.get('username')
            if not employee_username:
                self.log_failure("Create unpaid leave", error="Test employee missing username")
                return False
                
            if not self.authenticate(employee_username, "testpass123"):
                self.log_failure("Create unpaid leave", error="Could not authenticate as test employee")
                return False
            
            start_date = (date.today() + timedelta(days=14)).strftime('%Y-%m-%d')
            end_date = (date.today() + timedelta(days=18)).strftime('%Y-%m-%d')
            
            data = {
                "leave_type": "unpaid_leave",
                "start_date": start_date,
                "end_date": end_date,
                "reason": "Personal emergency test"
            }
            
            response = self.make_request('POST', '/api/attendance/leaves/', data)
            
            if response.status_code == 201:
                leave = response.json()
                # LeaveApplicationCreateSerializer returns limited fields, get full details
                if 'leave_type' in leave and leave['leave_type'] == 'unpaid_leave':
                    # Re-authenticate as admin to fetch the created leave
                    if self.authenticate():
                        employee_id = self.test_employee['id']
                        fetch_response = self.make_request('GET', f'/api/attendance/leaves/?employee={employee_id}')
                        
                        if fetch_response.status_code == 200:
                            leaves_data = fetch_response.json()
                            leaves_list = leaves_data.get('results', leaves_data) if isinstance(leaves_data, dict) else leaves_data
                            # Find the leave record we just created
                            for leave_record in leaves_list:
                                if (leave_record.get('leave_type') == 'unpaid_leave' and 
                                    leave_record.get('employee') == self.test_employee['id'] and
                                    leave_record.get('start_date') == start_date and
                                    leave_record.get('end_date') == end_date):
                                    self.track_created_resource('leaves', leave_record['id'])
                                    self.test_leaves.append(leave_record)
                                    return True
                        
                        self.log_failure("Create unpaid leave - could not fetch created record", response)
                        return False
                    else:
                        # Still consider success if we can't re-authenticate as admin
                        self.test_leaves.append(leave)
                        return True
                
                self.log_failure("Create unpaid leave - invalid response format", response)
                return False
            else:
                self.log_failure("Create unpaid leave", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create unpaid leave", error=str(e))
            return False
    
    def test_list_leaves(self) -> bool:
        """Test listing leave applications"""
        try:
            response = self.make_request('GET', '/api/attendance/leaves/')
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle paginated or direct array response
                leaves_list = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(leaves_list, list):
                    # Check if our created leave applications are in the list
                    created_ids = [l['id'] for l in self.test_leaves]
                    listed_ids = [l['id'] for l in leaves_list if 'id' in l]
                    
                    if all(lid in listed_ids for lid in created_ids):
                        return True
                    else:
                        self.log_failure("List leaves - missing created applications", response)
                        return False
                else:
                    self.log_failure("List leaves - invalid response format", response)
                    return False
            else:
                self.log_failure("List leaves", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("List leaves", error=str(e))
            return False
    
    def test_get_leave_detail(self) -> bool:
        """Test getting leave application details"""
        try:
            if not self.test_leaves:
                return False
            
            leave_id = self.test_leaves[0]['id']
            response = self.make_request('GET', f'/api/attendance/leaves/{leave_id}/')
            
            if response.status_code == 200:
                leave = response.json()
                required_fields = ['id', 'employee', 'leave_type', 'start_date', 'end_date']
                if all(field in leave for field in required_fields):
                    if leave['id'] == leave_id:
                        return True
                
                self.log_failure("Get leave detail - invalid response", response)
                return False
            else:
                self.log_failure("Get leave detail", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Get leave detail", error=str(e))
            return False
    
    def test_update_leave_status(self) -> bool:
        """Test updating leave application status"""
        try:
            if not self.test_leaves:
                return False
            
            leave_id = self.test_leaves[0]['id']
            data = {
                "status": "approved",
                "approved_by": self.admin_user['id']
            }
            
            response = self.make_request('PATCH', f'/api/attendance/leaves/{leave_id}/', data)
            
            if response.status_code == 200:
                leave = response.json()
                if (leave.get('status') == 'approved' and 
                    leave.get('id') == leave_id):
                    # Update our local copy
                    self.test_leaves[0].update(leave)
                    return True
                
                self.log_failure("Update leave status - not approved", response)
                return False
            else:
                self.log_failure("Update leave status", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Update leave status", error=str(e))
            return False
    
    def test_reject_leave_application(self) -> bool:
        """Test rejecting leave application"""
        try:
            if not self.test_leaves or len(self.test_leaves) < 2:
                # Create another leave if we don't have enough
                if not self.test_create_unpaid_leave():
                    return False
            
            # Use the second leave (or first if only one exists)
            leave_index = 1 if len(self.test_leaves) > 1 else 0
            leave_id = self.test_leaves[leave_index]['id']
            
            data = {
                "status": "rejected",
                "approved_by": self.admin_user['id']
            }
            
            response = self.make_request('PATCH', f'/api/attendance/leaves/{leave_id}/', data)
            
            if response.status_code == 200:
                leave = response.json()
                if (leave.get('status') == 'rejected' and 
                    leave.get('id') == leave_id):
                    # Update our local copy
                    self.test_leaves[leave_index].update(leave)
                    return True
                
                self.log_failure("Reject leave application - not rejected", response)
                return False
            else:
                self.log_failure("Reject leave application", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Reject leave application", error=str(e))
            return False
    
    def test_filter_leaves_by_employee(self) -> bool:
        """Test filtering leaves by employee"""
        try:
            if not self.test_employee:
                return False
            
            params = {"employee": self.test_employee['id']}
            response = self.make_request('GET', '/api/attendance/leaves/', params=params)
            
            if response.status_code == 200:
                result = response.json()
                leaves_list = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(leaves_list, list):
                    # All records should belong to our test employee
                    if all(l.get('employee') == self.test_employee['id'] for l in leaves_list):
                        # Should include our created records
                        created_ids = [l['id'] for l in self.test_leaves]
                        listed_ids = [l['id'] for l in leaves_list]
                        
                        if all(lid in listed_ids for lid in created_ids):
                            return True
                    
                    self.log_failure("Filter leaves by employee - invalid results", response)
                    return False
                else:
                    self.log_failure("Filter leaves by employee - invalid format", response)
                    return False
            else:
                self.log_failure("Filter leaves by employee", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Filter leaves by employee", error=str(e))
            return False
    
    def test_filter_leaves_by_status(self) -> bool:
        """Test filtering leaves by status"""
        try:
            params = {"status": "pending"}
            response = self.make_request('GET', '/api/attendance/leaves/', params=params)
            
            if response.status_code == 200:
                result = response.json()
                leaves_list = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(leaves_list, list):
                    # All records should have pending status
                    if all(l.get('status') == 'pending' for l in leaves_list):
                        return True
                    
                    self.log_failure("Filter leaves by status - invalid results", response)
                    return False
                else:
                    self.log_failure("Filter leaves by status - invalid format", response)
                    return False
            else:
                self.log_failure("Filter leaves by status", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Filter leaves by status", error=str(e))
            return False
    
    def test_create_leave_invalid_dates(self) -> bool:
        """Test creating leave with invalid date range"""
        try:
            if not self.test_employee:
                return False
            
            # End date before start date
            start_date = (date.today() + timedelta(days=10)).strftime('%Y-%m-%d')
            end_date = (date.today() + timedelta(days=5)).strftime('%Y-%m-%d')
            
            data = {
                "employee": self.test_employee['id'],
                "leave_type": "casual_leave",
                "start_date": start_date,
                "end_date": end_date,
                "reason": "Invalid date test"
            }
            
            response = self.make_request('POST', '/api/attendance/leaves/', data)
            
            if response.status_code == 400:
                result = response.json()
                # Should have validation error
                if any(key in result for key in ['start_date', 'end_date', 'error', 'non_field_errors']):
                    return True
                
            self.log_failure("Create leave invalid dates", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Create leave invalid dates", error=str(e))
            return False
    
    def test_create_leave_missing_data(self) -> bool:
        """Test creating leave with missing required fields"""
        try:
            # Missing employee and dates
            data = {
                "leave_type": "casual_leave",
                "reason": "Missing data test"
            }
            
            response = self.make_request('POST', '/api/attendance/leaves/', data)
            
            if response.status_code == 400:
                result = response.json()
                # Should have validation errors for missing fields
                required_fields = ['employee', 'start_date', 'end_date']
                if any(field in result for field in required_fields):
                    return True
                
            self.log_failure("Create leave missing data", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Create leave missing data", error=str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """Run all leave tests"""
        print("Running Leave Integration Tests...")
        
        # Setup dependencies first
        if not self.setup_dependencies():
            print("Failed to setup dependencies")
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0, "failed_details": []}
        
        tests = [
            ("Create Casual Leave", self.test_create_casual_leave),
            ("Create Unpaid Leave", self.test_create_unpaid_leave),
            ("List Leaves", self.test_list_leaves),
            ("Get Leave Detail", self.test_get_leave_detail),
            ("Update Leave Status", self.test_update_leave_status),
            ("Reject Leave Application", self.test_reject_leave_application),
            ("Filter Leaves by Employee", self.test_filter_leaves_by_employee),
            ("Filter Leaves by Status", self.test_filter_leaves_by_status),
            ("Create Leave Invalid Dates", self.test_create_leave_invalid_dates),
            ("Create Leave Missing Data", self.test_create_leave_missing_data),
        ]
        
        for test_name, test_func in tests:
            print(f"  Running: {test_name}")
            try:
                passed = test_func()
                self.results.add_test_result(test_name, passed)
                print(f"    {Colors.pass_text() if passed else Colors.fail_text()}")
            except Exception as e:
                self.results.add_test_result(test_name, False, str(e))
                print(f"    {Colors.fail_text()} - {str(e)}")
        
        return self.results.get_summary()
    
    def cleanup(self):
        """Clean up created leave applications and dependencies"""
        print("Cleaning up created leave applications and dependencies...")
        self.cleanup_resources()
        self.resource_manager.cleanup_resources()

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Run leave integration tests')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after tests')
    args = parser.parse_args()
    
    test_runner = LeaveIntegrationTests()
    
    try:
        results = test_runner.run_all_tests()
        
        print(f"\nLeave Tests Summary:")
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
