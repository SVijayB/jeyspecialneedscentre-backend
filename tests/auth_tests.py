"""
Authentication integration tests
Tests login, logout, token validation with REAL API calls
"""

import sys
import argparse
from base_test import BaseIntegrationTest, TestResults
from colors import Colors

class AuthIntegrationTests(BaseIntegrationTest):
    """Integration tests for authentication endpoints"""
    
    def __init__(self):
        super().__init__()
        self.results = TestResults()
    
    def test_admin_login_success(self) -> bool:
        """Test successful admin login"""
        try:
            url = f"{self.base_url}/api/auth/login/"
            data = {"username": "admin", "password": "admin123"}
            
            response = self.make_request('POST', '/api/auth/login/', data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                required_fields = ['token', 'user']
                if all(field in result for field in required_fields):
                    user_fields = ['id', 'username', 'role', 'employee_id']
                    if all(field in result['user'] for field in user_fields):
                        # Store token for subsequent tests
                        self.token = result['token']
                        self.admin_user = result['user']
                        self.session.headers.update({'Authorization': f'Token {self.token}'})
                        return True
                
                self.log_failure("Admin login - invalid response structure", response)
                return False
            else:
                self.log_failure("Admin login", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Admin login", error=str(e))
            return False
    
    def test_invalid_credentials(self) -> bool:
        """Test login with invalid credentials"""
        try:
            data = {"username": "invalid", "password": "wrong123"}
            response = self.make_request('POST', '/api/auth/login/', data)
            
            if response.status_code == 401:
                result = response.json()
                if 'error' in result:
                    return True
                
            self.log_failure("Invalid credentials test", response, 401)
            return False
            
        except Exception as e:
            self.log_failure("Invalid credentials test", error=str(e))
            return False
    
    def test_missing_credentials(self) -> bool:
        """Test login with missing username/password"""
        try:
            data = {"username": "admin"}  # Missing password
            response = self.make_request('POST', '/api/auth/login/', data)
            
            if response.status_code == 400:
                result = response.json()
                if 'error' in result:
                    return True
                
            self.log_failure("Missing credentials test", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Missing credentials test", error=str(e))
            return False
    
    def test_token_authentication(self) -> bool:
        """Test using token for authenticated endpoint"""
        try:
            # Ensure we have a token
            if not self.token:
                if not self.authenticate():
                    return False
            
            # Test accessing authenticated endpoint
            response = self.make_request('GET', '/api/auth/users/me/')
            
            if response.status_code == 200:
                result = response.json()
                if 'id' in result and 'username' in result:
                    return True
                
            self.log_failure("Token authentication test", response, 200)
            return False
            
        except Exception as e:
            self.log_failure("Token authentication test", error=str(e))
            return False
    
    def test_logout(self) -> bool:
        """Test logout functionality"""
        try:
            # Ensure we're logged in
            if not self.token:
                if not self.authenticate():
                    return False
            
            response = self.make_request('POST', '/api/auth/logout/')
            
            if response.status_code == 200:
                result = response.json()
                if 'message' in result:
                    # Clear token after logout
                    self.token = None
                    if 'Authorization' in self.session.headers:
                        del self.session.headers['Authorization']
                    return True
                
            self.log_failure("Logout test", response, 200)
            return False
            
        except Exception as e:
            self.log_failure("Logout test", error=str(e))
            return False
    
    def test_invalid_token_access(self) -> bool:
        """Test access with invalid token"""
        try:
            # Set invalid token
            self.session.headers.update({'Authorization': 'Token invalid_token_123'})
            
            response = self.make_request('GET', '/api/auth/users/me/')
            
            if response.status_code == 401:
                return True
                
            self.log_failure("Invalid token test", response, 401)
            return False
            
        except Exception as e:
            self.log_failure("Invalid token test", error=str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """Run all authentication tests"""
        print("Running Authentication Integration Tests...")
        
        tests = [
            ("Admin Login Success", self.test_admin_login_success),
            ("Invalid Credentials", self.test_invalid_credentials),
            ("Missing Credentials", self.test_missing_credentials),
            ("Token Authentication", self.test_token_authentication),
            ("Logout", self.test_logout),
            ("Invalid Token Access", self.test_invalid_token_access),
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
        """Cleanup any created resources"""
        # Auth tests don't create persistent resources
        # Just clear session
        self.token = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Run authentication integration tests')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after tests')
    args = parser.parse_args()
    
    test_runner = AuthIntegrationTests()
    
    try:
        results = test_runner.run_all_tests()
        
        print(f"\nAuthentication Tests Summary:")
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
