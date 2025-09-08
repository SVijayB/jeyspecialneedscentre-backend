"""
Base test utilities for integration testing
Provides shared functionality, logging, and HTTP client for all test modules
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class BaseIntegrationTest:
    """Base class for all integration tests with shared utilities"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.admin_user = None
        self.created_resources = {
            'branches': [],
            'users': [],
            'attendance': [],
            'leaves': [],
            'checkout_requests': []
        }
        
        # Setup logging for failures only - write to file
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        if not self.logger.handlers:
            # Create logs directory if it doesn't exist
            import os
            os.makedirs("test_logs", exist_ok=True)
            
            # File handler for detailed failure logs
            file_handler = logging.FileHandler(f"test_logs/integration_test_failures.log")
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.ERROR)
    
    def authenticate(self, username: str = "admin", password: str = "admin123") -> bool:
        """Authenticate and store token for subsequent requests"""
        url = f"{self.base_url}/api/auth/login/"
        data = {"username": username, "password": password}
        
        try:
            response = self.session.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                self.token = result['token']
                self.admin_user = result['user']
                self.session.headers.update({'Authorization': f'Token {self.token}'})
                return True
            else:
                self.log_failure("Authentication failed", response)
                return False
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, 
                    params: Dict = None) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            elif method.upper() == 'PATCH':
                response = self.session.patch(url, json=data)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
        except Exception as e:
            self.logger.error(f"Request error for {method} {url}: {str(e)}")
            raise
    
    def log_failure(self, test_name: str, response: requests.Response = None, 
                   expected_status: int = None, error: str = None):
        """Log test failure with full debugging information"""
        import os
        from datetime import datetime
        
        # Ensure logs directory exists
        os.makedirs("test_logs", exist_ok=True)
        
        # Create detailed log entry
        log_entry = f"\n{'='*80}\n"
        log_entry += f"FAILED TEST: {test_name}\n"
        log_entry += f"TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_entry += f"{'='*80}\n"
        
        if response:
            log_entry += f"Status Code: {response.status_code}\n"
            if expected_status:
                log_entry += f"Expected Status: {expected_status}\n"
            log_entry += f"URL: {response.url}\n"
            log_entry += f"Response Body: {response.text}\n"
            
            # Log request details
            if hasattr(response, 'request'):
                req = response.request
                log_entry += f"Request Method: {req.method}\n"
                if req.body:
                    log_entry += f"Request Body: {req.body}\n"
                if hasattr(req, 'headers'):
                    log_entry += f"Request Headers: {dict(req.headers)}\n"
        
        if error:
            log_entry += f"Error: {error}\n"
        
        log_entry += f"{'='*80}\n"
        
        # Write to file
        with open("test_logs/integration_test_failures.log", "a", encoding="utf-8") as f:
            f.write(log_entry)
            f.flush()
        
        # Also use the logger
        self.logger.error(f"FAILED: {test_name}")
        if response:
            self.logger.error(f"Status: {response.status_code}, Response: {response.text}")
        if error:
            self.logger.error(f"Error: {error}")
        
        # Force flush the log
        for handler in self.logger.handlers:
            handler.flush()
    
    def generate_unique_id(self, prefix: str = "") -> str:
        """Generate unique identifier using timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"{prefix}{timestamp}" if prefix else timestamp
    
    def track_created_resource(self, resource_type: str, resource_id: int):
        """Track created resource for cleanup"""
        if resource_type in self.created_resources:
            self.created_resources[resource_type].append(resource_id)
    
    def cleanup_resources(self):
        """Clean up all created resources in reverse order"""
        cleanup_order = ['checkout_requests', 'leaves', 'attendance', 'users', 'branches']
        
        for resource_type in cleanup_order:
            resource_ids = self.created_resources[resource_type]
            if not resource_ids:
                continue
                
            endpoint_map = {
                'branches': '/api/auth/branches',
                'users': '/api/auth/users', 
                'attendance': '/api/attendance/attendance',
                'leaves': '/api/attendance/leaves',
                'checkout_requests': '/api/attendance/checkout-requests'
            }
            
            endpoint = endpoint_map.get(resource_type)
            if not endpoint:
                continue
                
            for resource_id in reversed(resource_ids):
                try:
                    response = self.make_request('DELETE', f"{endpoint}/{resource_id}/")
                    if response.status_code not in [204, 404]:
                        self.logger.warning(
                            f"Failed to delete {resource_type} {resource_id}: {response.status_code}"
                        )
                except Exception as e:
                    self.logger.warning(f"Error deleting {resource_type} {resource_id}: {str(e)}")
            
            self.created_resources[resource_type].clear()

# Test result tracking
class TestResults:
    """Track test results across all modules"""
    
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.failed_test_details = []
    
    def add_test_result(self, test_name: str, passed: bool, error: str = None):
        """Add a test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
            self.failed_test_details.append({
                'test': test_name,
                'error': error
            })
    
    def get_summary(self) -> Dict:
        """Get test results summary"""
        return {
            'total': self.total_tests,
            'passed': self.passed_tests,
            'failed': self.failed_tests,
            'pass_rate': round((self.passed_tests / self.total_tests * 100), 2) if self.total_tests > 0 else 0,
            'failed_details': self.failed_test_details
        }
