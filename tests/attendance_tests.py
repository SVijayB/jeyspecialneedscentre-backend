"""
Attendance integration tests
Tests attendance CRUD operations with REAL API calls and data
"""

import sys
import argparse
from datetime import date, datetime, timedelta
from base_test import BaseIntegrationTest, TestResults
from resource_manager import ResourceManager
from colors import Colors
from colors import Colors

class AttendanceIntegrationTests(BaseIntegrationTest):
    """Integration tests for attendance management endpoints"""
    
    def __init__(self):
        super().__init__()
        self.results = TestResults()
        self.resource_manager = ResourceManager()
        self.test_attendance = []
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
    
    def test_create_attendance_present(self) -> bool:
        """Test creating attendance record with present status"""
        try:
            if not self.test_employee:
                return False
            
            today = date.today().strftime('%Y-%m-%d')
            data = {
                "employee_id": self.test_employee['employee_id'],
                "date": today,
                "check_in_time": f"{today}T09:30:00Z",
                "check_out_time": f"{today}T17:30:00Z"
            }
            
            response = self.make_request('POST', '/api/attendance/attendance/', data)
            
            if response.status_code == 201:
                # API uses limited serializer that doesn't return ID, fetch the created record
                employee_id = self.test_employee['id']
                fetch_response = self.make_request('GET', f'/api/attendance/attendance/?employee={employee_id}&date={today}')
                
                if fetch_response.status_code == 200:
                    attendance_data = fetch_response.json()
                    # Handle paginated response
                    if isinstance(attendance_data, dict) and 'results' in attendance_data:
                        attendance_list = attendance_data['results']
                    else:
                        attendance_list = attendance_data if isinstance(attendance_data, list) else []
                    
                    # Find the attendance record we just created
                    for attendance in attendance_list:
                        if (attendance.get('employee') == self.test_employee['id'] and
                            attendance.get('date') == today and
                            attendance.get('check_in_time') is not None):
                            self.track_created_resource('attendance', attendance['id'])
                            self.test_attendance.append(attendance)
                            return True
                
                self.log_failure("Create attendance present - could not find created record", response)
                return False
            else:
                self.log_failure("Create attendance present", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create attendance present", error=str(e))
            return False
    
    def test_create_attendance_absent(self) -> bool:
        """Test creating attendance record with absent status"""
        try:
            if not self.test_employee:
                return False
            
            yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')
            data = {
                "employee_id": self.test_employee['employee_id'],
                "date": yesterday
            }
            
            response = self.make_request('POST', '/api/attendance/attendance/', data)
            
            if response.status_code == 201:
                # API uses limited serializer that doesn't return ID, fetch the created record
                employee_id = self.test_employee['id']
                fetch_response = self.make_request('GET', f'/api/attendance/attendance/?employee={employee_id}&date={yesterday}')
                
                if fetch_response.status_code == 200:
                    attendance_data = fetch_response.json()
                    # Handle paginated response
                    if isinstance(attendance_data, dict) and 'results' in attendance_data:
                        attendance_list = attendance_data['results']
                    else:
                        attendance_list = attendance_data if isinstance(attendance_data, list) else []
                    
                    # Find the attendance record we just created (absent record has no check_in_time)
                    for attendance in attendance_list:
                        if (attendance.get('employee') == self.test_employee['id'] and
                            attendance.get('date') == yesterday and
                            attendance.get('check_in_time') is None):
                            self.track_created_resource('attendance', attendance['id'])
                            self.test_attendance.append(attendance)
                            return True
                
                self.log_failure("Create attendance absent - could not find created record", response)
                return False
            else:
                self.log_failure("Create attendance absent", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create attendance absent", error=str(e))
            return False
    
    def test_list_attendance(self) -> bool:
        """Test listing attendance records"""
        try:
            response = self.make_request('GET', '/api/attendance/attendance/')
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle paginated or direct array response
                attendance_list = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(attendance_list, list):
                    # Check if our created attendance records are in the list
                    created_ids = [a['id'] for a in self.test_attendance]
                    listed_ids = [a['id'] for a in attendance_list if 'id' in a]
                    
                    if all(aid in listed_ids for aid in created_ids):
                        return True
                    else:
                        self.log_failure("List attendance - missing created records", response)
                        return False
                else:
                    self.log_failure("List attendance - invalid response format", response)
                    return False
            else:
                self.log_failure("List attendance", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("List attendance", error=str(e))
            return False
    
    def test_get_attendance_detail(self) -> bool:
        """Test getting attendance record details"""
        try:
            if not self.test_attendance:
                return False
            
            attendance_id = self.test_attendance[0]['id']
            response = self.make_request('GET', f'/api/attendance/attendance/{attendance_id}/')
            
            if response.status_code == 200:
                attendance = response.json()
                required_fields = ['id', 'employee', 'date', 'status']
                if all(field in attendance for field in required_fields):
                    if attendance['id'] == attendance_id:
                        return True
                
                self.log_failure("Get attendance detail - invalid response", response)
                return False
            else:
                self.log_failure("Get attendance detail", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Get attendance detail", error=str(e))
            return False
    
    def test_update_attendance(self) -> bool:
        """Test updating attendance record"""
        try:
            if not self.test_attendance:
                return False
            
            attendance_id = self.test_attendance[0]['id']
            # Update checkout time
            updated_date = self.test_attendance[0]['date']
            data = {
                "check_out_time": f"{updated_date}T18:00:00Z"
            }
            
            response = self.make_request('PATCH', f'/api/attendance/attendance/{attendance_id}/', data)
            
            if response.status_code == 200:
                attendance = response.json()
                if attendance.get('id') == attendance_id:
                    # Update our local copy
                    self.test_attendance[0].update(attendance)
                    return True
                
                self.log_failure("Update attendance - invalid response", response)
                return False
            else:
                self.log_failure("Update attendance", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Update attendance", error=str(e))
            return False
    
    def test_filter_attendance_by_employee(self) -> bool:
        """Test filtering attendance by employee"""
        try:
            if not self.test_employee:
                return False
            
            params = {"employee": self.test_employee['id']}
            response = self.make_request('GET', '/api/attendance/attendance/', params=params)
            
            if response.status_code == 200:
                result = response.json()
                attendance_list = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(attendance_list, list):
                    # All records should belong to our test employee
                    if all(a.get('employee') == self.test_employee['id'] for a in attendance_list):
                        # Should include our created records
                        created_ids = [a['id'] for a in self.test_attendance]
                        listed_ids = [a['id'] for a in attendance_list]
                        
                        if all(aid in listed_ids for aid in created_ids):
                            return True
                    
                    self.log_failure("Filter attendance by employee - invalid results", response)
                    return False
                else:
                    self.log_failure("Filter attendance by employee - invalid format", response)
                    return False
            else:
                self.log_failure("Filter attendance by employee", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Filter attendance by employee", error=str(e))
            return False
    
    def test_filter_attendance_by_date(self) -> bool:
        """Test filtering attendance by date"""
        try:
            today = date.today().strftime('%Y-%m-%d')
            params = {"date": today}
            response = self.make_request('GET', '/api/attendance/attendance/', params=params)
            
            if response.status_code == 200:
                result = response.json()
                attendance_list = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(attendance_list, list):
                    # All records should be for today
                    if all(a.get('date') == today for a in attendance_list):
                        return True
                    
                    self.log_failure("Filter attendance by date - invalid results", response)
                    return False
                else:
                    self.log_failure("Filter attendance by date - invalid format", response)
                    return False
            else:
                self.log_failure("Filter attendance by date", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Filter attendance by date", error=str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """Run all attendance tests"""
        print("Running Attendance Integration Tests...")
        
        # Setup dependencies first
        if not self.setup_dependencies():
            print("Failed to setup dependencies")
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0, "failed_details": []}
        
        tests = [
            ("Create Attendance Present", self.test_create_attendance_present),
            ("Create Attendance Absent", self.test_create_attendance_absent),
            ("List Attendance", self.test_list_attendance),
            ("Get Attendance Detail", self.test_get_attendance_detail),
            ("Update Attendance", self.test_update_attendance),
            ("Filter Attendance by Employee", self.test_filter_attendance_by_employee),
            ("Filter Attendance by Date", self.test_filter_attendance_by_date),
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
        """Clean up created attendance records and dependencies"""
        print("Cleaning up created attendance records and dependencies...")
        self.cleanup_resources()
        self.resource_manager.cleanup_resources()

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Run attendance integration tests')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after tests')
    args = parser.parse_args()
    
    test_runner = AttendanceIntegrationTests()
    
    try:
        results = test_runner.run_all_tests()
        
        print(f"\nAttendance Tests Summary:")
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
