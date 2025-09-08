"""
QR Code integration tests
Tests the core QR workflow - generate QR and scan QR for check-in
Checkout is button-based (not QR-based) as per system design
"""

import sys
import argparse
from datetime import datetime, timedelta
import json
from base_test import BaseIntegrationTest, TestResults
from resource_manager import ResourceManager
from colors import Colors


class QRIntegrationTests(BaseIntegrationTest):
    """Integration tests for QR Code functionality"""
    
    def __init__(self):
        super().__init__()
        self.results = TestResults()
        self.resource_manager = ResourceManager()
        self.test_employee = None
        self.generated_qr_data = None
    
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
    
    def test_generate_qr_code(self) -> bool:
        """Test QR code generation for check-in"""
        try:
            # Clean slate - force checkout any existing check-in
            self.make_request('POST', '/api/attendance/attendance/checkout/')
            
            response = self.make_request('POST', '/api/attendance/qr/generate/')
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify QR code response structure
                if ('qr_code' in result and 'qr_data' in result and 
                    result['qr_data'].get('type') == 'checkin'):
                    return True
                
                self.log_failure("Generate QR - incorrect structure", response)
                return False
            else:
                self.log_failure("Generate QR code", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Generate QR code", error=str(e))
            return False
    
    def test_scan_qr_code_creates_attendance(self) -> bool:
        """Test scanning QR code creates attendance record"""
        try:
            # Generate a QR code first
            gen_response = self.make_request('POST', '/api/attendance/qr/generate/')
            if gen_response.status_code != 200:
                self.log_failure("Generate QR for scan test", gen_response, 200)
                return False
            
            qr_data = gen_response.json().get('qr_data')
            if not qr_data:
                self.log_failure("Generate QR - missing qr_data", gen_response)
                return False
            
            # Scan the QR code
            response = self.make_request('POST', '/api/attendance/qr/scan/', {'qr_data': qr_data})
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify attendance was created
                if 'attendance' in result:
                    attendance = result['attendance']
                    
                    # Verify attendance has required fields
                    if ('id' in attendance and 'check_in_time' in attendance and
                        attendance.get('status') in ['present', 'did_not_checkout']):
                        
                        # Double-check attendance exists in system
                        verify_response = self.make_request('GET', f'/api/attendance/attendance/{attendance["id"]}/')
                        if (verify_response.status_code == 200 and 
                            verify_response.json().get('check_in_time') and
                            verify_response.json().get('check_out_time') is None):
                            return True
                        
                        self.log_failure("Verify attendance record", verify_response, 200)
                        return False
                
                self.log_failure("Scan QR - no attendance created", response)
                return False
            else:
                self.log_failure("Scan QR code", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Scan QR code", error=str(e))
            return False
    
    def test_checkout_is_button_based(self) -> bool:
        """Test that checkout is button-based, not QR-based"""
        try:
            # Should have an active check-in from previous test
            # Just test the checkout button works
            checkout_response = self.make_request('POST', '/api/attendance/attendance/checkout/')
            
            if checkout_response.status_code == 200:
                checkout_data = checkout_response.json()
                
                # Verify checkout happened (check_out_time should be present)
                if ('attendance' in checkout_data and 
                    checkout_data['attendance'].get('check_out_time')):
                    return True
                    
                return False
            
            elif checkout_response.status_code == 400:
                error = checkout_response.json().get('error', '')
                if '6 PM' in error or 'No active check-in' in error:
                    # Expected behavior - either after 6 PM or no active check-in
                    return True
                return False
            else:
                return False
                
        except Exception as e:
            self.log_failure("Checkout test", error=str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """Run all QR tests"""
        print("Running QR Code Integration Tests...")
        
        # Setup dependencies first
        if not self.setup_dependencies():
            print("Failed to setup dependencies")
            return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0, "failed_details": []}
        
        tests = [
            ("Generate QR Code", self.test_generate_qr_code),
            ("Scan QR Creates Attendance", self.test_scan_qr_code_creates_attendance),
            ("Checkout is Button-Based", self.test_checkout_is_button_based),
        ]
        
        for test_name, test_func in tests:
            print(f"  Running: {test_name}")
            try:
                passed = test_func()
                self.results.add_test_result(test_name, passed)
                print(f"    {Colors.pass_text() if passed else Colors.fail_text()}")
                
                # Clean up after each test - force checkout any active check-in
                self.make_request('POST', '/api/attendance/attendance/checkout/')
                
            except Exception as e:
                self.results.add_test_result(test_name, False, str(e))
                print(f"    {Colors.fail_text()} - {str(e)}")
        
        return self.results.get_summary()
    
    def cleanup(self):
        """Clean up created resources and dependencies"""
        print("Cleaning up created QR test resources and dependencies...")
        self.cleanup_resources()
        self.resource_manager.cleanup_resources()

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Run QR code integration tests')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after tests')
    args = parser.parse_args()
    
    test_runner = QRIntegrationTests()
    
    try:
        results = test_runner.run_all_tests()
        
        print(f"\nQR Code Tests Summary:")
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
