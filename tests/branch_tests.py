"""
Branch integration tests
Tests branch CRUD operations with REAL API calls and data
"""

import sys
import argparse
from base_test import BaseIntegrationTest, TestResults
from colors import Colors

class BranchIntegrationTests(BaseIntegrationTest):
    """Integration tests for branch management endpoints"""
    
    def __init__(self):
        super().__init__()
        self.results = TestResults()
        self.test_branches = []
    
    def test_create_branch(self) -> bool:
        """Test creating a new branch"""
        try:
            if not self.authenticate():
                return False
            
            branch_name = f"TestBranch_{self.generate_unique_id()}"
            data = {"name": branch_name}
            
            response = self.make_request('POST', '/api/auth/branches/', data)
            
            if response.status_code == 201:
                branch = response.json()
                required_fields = ['id', 'name', 'created_at']
                if all(field in branch for field in required_fields):
                    if branch['name'] == branch_name:
                        self.track_created_resource('branches', branch['id'])
                        self.test_branches.append(branch)
                        return True
                
                self.log_failure("Create branch - invalid response", response)
                return False
            else:
                self.log_failure("Create branch", response, 201)
                return False
                
        except Exception as e:
            self.log_failure("Create branch", error=str(e))
            return False
    
    def test_list_branches(self) -> bool:
        """Test listing all branches"""
        try:
            if not self.authenticate():
                return False
            
            response = self.make_request('GET', '/api/auth/branches/')
            
            if response.status_code == 200:
                result = response.json()
                
                # DRF usually returns paginated results or direct array
                branches = result.get('results', result) if isinstance(result, dict) else result
                
                if isinstance(branches, list):
                    # Verify our created branches are in the list
                    created_ids = [b['id'] for b in self.test_branches]
                    listed_ids = [b['id'] for b in branches if 'id' in b]
                    
                    if all(bid in listed_ids for bid in created_ids):
                        return True
                    else:
                        self.log_failure("List branches - missing created branches", response)
                        return False
                else:
                    self.log_failure("List branches - invalid response format", response)
                    return False
            else:
                self.log_failure("List branches", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("List branches", error=str(e))
            return False
    
    def test_get_branch_detail(self) -> bool:
        """Test getting branch details"""
        try:
            if not self.test_branches:
                return False
            
            branch_id = self.test_branches[0]['id']
            response = self.make_request('GET', f'/api/auth/branches/{branch_id}/')
            
            if response.status_code == 200:
                branch = response.json()
                required_fields = ['id', 'name', 'created_at']
                if all(field in branch for field in required_fields):
                    if branch['id'] == branch_id:
                        return True
                
                self.log_failure("Get branch detail - invalid response", response)
                return False
            else:
                self.log_failure("Get branch detail", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Get branch detail", error=str(e))
            return False
    
    def test_update_branch(self) -> bool:
        """Test updating branch name"""
        try:
            if not self.test_branches:
                return False
            
            branch_id = self.test_branches[0]['id']
            new_name = f"UpdatedBranch_{self.generate_unique_id()}"
            data = {"name": new_name}
            
            response = self.make_request('PATCH', f'/api/auth/branches/{branch_id}/', data)
            
            if response.status_code == 200:
                branch = response.json()
                if branch.get('name') == new_name and branch.get('id') == branch_id:
                    # Update our local copy
                    self.test_branches[0]['name'] = new_name
                    return True
                
                self.log_failure("Update branch - name not updated", response)
                return False
            else:
                self.log_failure("Update branch", response, 200)
                return False
                
        except Exception as e:
            self.log_failure("Update branch", error=str(e))
            return False
    
    def test_create_duplicate_branch(self) -> bool:
        """Test creating branch with duplicate name"""
        try:
            if not self.test_branches:
                return False
            
            # Try to create branch with same name as existing one
            existing_name = self.test_branches[0]['name']
            data = {"name": existing_name}
            
            response = self.make_request('POST', '/api/auth/branches/', data)
            
            if response.status_code == 400:
                result = response.json()
                # Should return validation error
                if 'name' in result or 'error' in result or 'non_field_errors' in result:
                    return True
                
            self.log_failure("Create duplicate branch", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Create duplicate branch", error=str(e))
            return False
    
    def test_create_branch_invalid_data(self) -> bool:
        """Test creating branch with invalid data"""
        try:
            # Try to create branch without name
            data = {}
            
            response = self.make_request('POST', '/api/auth/branches/', data)
            
            if response.status_code == 400:
                result = response.json()
                if 'name' in result or 'error' in result:
                    return True
                
            self.log_failure("Create branch invalid data", response, 400)
            return False
            
        except Exception as e:
            self.log_failure("Create branch invalid data", error=str(e))
            return False
    
    def run_all_tests(self) -> dict:
        """Run all branch tests"""
        print("Running Branch Integration Tests...")
        
        tests = [
            ("Create Branch", self.test_create_branch),
            ("Create Another Branch", self.test_create_branch),  # Create second for list test
            ("List Branches", self.test_list_branches),
            ("Get Branch Detail", self.test_get_branch_detail),
            ("Update Branch", self.test_update_branch),
            ("Create Duplicate Branch", self.test_create_duplicate_branch),
            ("Create Branch Invalid Data", self.test_create_branch_invalid_data),
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
        """Clean up created branches"""
        print("Cleaning up created branches...")
        self.cleanup_resources()

def main():
    """Main entry point for standalone execution"""
    parser = argparse.ArgumentParser(description='Run branch integration tests')
    parser.add_argument('--cleanup', action='store_true', help='Run cleanup after tests')
    args = parser.parse_args()
    
    test_runner = BranchIntegrationTests()
    
    try:
        results = test_runner.run_all_tests()
        
        print(f"\nBranch Tests Summary:")
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
