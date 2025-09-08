"""
Integration test runner
Coordinates execution of all test modules in proper dependency order
"""

import sys
import importlib
from datetime import datetime
from base_test import BaseIntegrationTest, TestResults
from colors import Colors

class IntegrationTestRunner:
    """Main runner for all integration tests"""
    
    def __init__(self):
        self.base_test = BaseIntegrationTest()
        self.overall_results = TestResults()
        self.test_modules = {
            'auth': 'auth_tests',
            'branch': 'branch_tests', 
            'user': 'user_tests',
            'attendance': 'attendance_tests',
            'leave': 'leave_tests',
            'qr': 'qr_tests'
        }
        
        # Define execution order (dependencies)
        self.execution_order = ['auth', 'branch', 'user', 'attendance', 'leave', 'qr']
    
    def run_test_module(self, module_name: str) -> dict:
        """Run a specific test module"""
        try:
            print(f"\n{'='*60}")
            print(Colors.header(f"RUNNING {module_name.upper()} TESTS"))
            print(f"{'='*60}")
            
            # Import and run the test module
            module = importlib.import_module(self.test_modules[module_name])
            
            # Special case for QR tests (class name is QRIntegrationTests not QrIntegrationTests)
            if module_name == 'qr':
                test_class_name = "QRIntegrationTests"
            else:
                test_class_name = f"{module_name.capitalize()}IntegrationTests"
            
            # Get the test class
            test_class = getattr(module, test_class_name)
            test_runner = test_class()
            
            # Run all tests in the module
            results = test_runner.run_all_tests()
            
            # Update overall results
            self.overall_results.total_tests += results['total']
            self.overall_results.passed_tests += results['passed']
            self.overall_results.failed_tests += results['failed']
            
            # Add failed test details with module prefix
            for failure in results['failed_details']:
                self.overall_results.failed_test_details.append({
                    'test': f"{module_name}.{failure['test']}",
                    'error': failure['error']
                })
            
            return results
            
        except Exception as e:
            print(f"ERROR: Failed to run {module_name} tests: {str(e)}")
            # Track as one failed test
            self.overall_results.total_tests += 1
            self.overall_results.failed_tests += 1
            self.overall_results.failed_test_details.append({
                'test': f"{module_name}.module_execution",
                'error': str(e)
            })
            return {
                'total': 1, 
                'passed': 0, 
                'failed': 1, 
                'pass_rate': 0, 
                'failed_details': [{'test': 'module_execution', 'error': str(e)}]
            }
    
    def run_all_tests(self, selected_modules: list = None) -> dict:
        """Run all test modules in dependency order"""
        start_time = datetime.now()
        
        print("="*80)
        print(Colors.bold("DJANGO REST API INTEGRATION TEST SUITE"))
        print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Check server connectivity first
        try:
            response = self.base_test.make_request('GET', '/health/')
            if response.status_code != 200:
                print(f"WARNING: Health check failed with status {response.status_code}")
                print("Continuing with tests anyway...")
        except Exception as e:
            print(f"WARNING: Could not reach server: {str(e)}")
            print("Continuing with tests anyway...")
        
        # Determine which modules to run
        modules_to_run = selected_modules if selected_modules else self.execution_order
        
        # Validate module names
        invalid_modules = [m for m in modules_to_run if m not in self.test_modules]
        if invalid_modules:
            print(f"ERROR: Invalid module names: {invalid_modules}")
            print(f"Available modules: {list(self.test_modules.keys())}")
            return self.overall_results.get_summary()
        
        print(f"Running modules: {modules_to_run}")
        
        # Run each module
        module_results = {}
        for module_name in modules_to_run:
            try:
                results = self.run_test_module(module_name)
                module_results[module_name] = results
                
                print(f"\n{module_name.upper()} Results:")
                if results['failed'] == 0:
                    print(Colors.success(f"  Passed: {results['passed']}/{results['total']} ({results['pass_rate']}%)"))
                else:
                    print(Colors.warning(f"  Passed: {results['passed']}/{results['total']} ({results['pass_rate']}%)"))
                    print(Colors.error(f"  Failed: {results['failed']} tests"))
                
            except KeyboardInterrupt:
                print(f"\nTest execution interrupted by user")
                break
            except Exception as e:
                print(f"CRITICAL ERROR in {module_name}: {str(e)}")
                continue
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Print final summary
        print("\n" + "="*80)
        print(Colors.header("FINAL TEST SUMMARY"))
        print("="*80)
        print(f"Execution time: {duration}")
        print(f"Total tests: {self.overall_results.total_tests}")
        print(Colors.success(f"Passed: {self.overall_results.passed_tests}"))
        print(Colors.error(f"Failed: {self.overall_results.failed_tests}"))
        
        if self.overall_results.total_tests > 0:
            pass_rate = round((self.overall_results.passed_tests / self.overall_results.total_tests * 100), 2)
            if pass_rate == 100:
                print(Colors.success(f"Pass rate: {pass_rate}%"))
            elif pass_rate >= 80:
                print(Colors.warning(f"Pass rate: {pass_rate}%"))
            else:
                print(Colors.error(f"Pass rate: {pass_rate}%"))
        
        # Show module breakdown
        print(f"\nModule Breakdown:")
        for module_name, results in module_results.items():
            status = Colors.success("PASS") if results['failed'] == 0 else Colors.error("FAIL")
            print(f"  {module_name:12}: {results['passed']:3}/{results['total']:3} ({results['pass_rate']:6.1f}%) [{status}]")
        
        # Show failed tests
        if self.overall_results.failed_test_details:
            print(f"\nFailed Tests ({len(self.overall_results.failed_test_details)}):")
            for i, failure in enumerate(self.overall_results.failed_test_details, 1):
                print(f"  {i:2}. {failure['test']}")
                if failure['error']:
                    print(f"      Error: {failure['error']}")
        
        return self.overall_results.get_summary()
    
    def final_cleanup(self):
        """Perform final cleanup of all created resources"""
        print("\n" + "="*60)
        print("PERFORMING FINAL CLEANUP")
        print("="*60)
        
        try:
            # Authenticate as admin for cleanup
            if self.base_test.authenticate():
                print("Authenticated for cleanup...")
                
                # Cleanup in reverse dependency order
                cleanup_order = ['qr', 'leave', 'attendance', 'user', 'branch']
                
                for module_name in cleanup_order:
                    try:
                        print(f"Cleaning up {module_name} resources...")
                        module = importlib.import_module(self.test_modules[module_name])
                        test_class_name = f"{module_name.capitalize()}IntegrationTests"
                        test_class = getattr(module, test_class_name)
                        test_runner = test_class()
                        
                        # Initialize with admin session
                        test_runner.session = self.base_test.session
                        test_runner.token = self.base_test.token
                        
                        test_runner.cleanup()
                        
                    except Exception as e:
                        print(f"Warning: Failed to cleanup {module_name}: {str(e)}")
                
                print("Final cleanup completed.")
            else:
                print("Failed to authenticate for cleanup")
                
        except Exception as e:
            print(f"Error during final cleanup: {str(e)}")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Django REST API Integration Tests')
    parser.add_argument('--tests', type=str, help='Comma-separated list of test modules to run')
    parser.add_argument('--cleanup', action='store_true', help='Perform final cleanup after tests')
    parser.add_argument('--no-cleanup', action='store_true', help='Skip final cleanup')
    
    args = parser.parse_args()
    
    # Parse selected modules
    selected_modules = None
    if args.tests:
        selected_modules = [m.strip() for m in args.tests.split(',')]
    
    runner = IntegrationTestRunner()
    
    try:
        # Run tests
        results = runner.run_all_tests(selected_modules)
        
        # Perform cleanup unless explicitly disabled
        if not args.no_cleanup:
            runner.final_cleanup()
        
        # Exit with appropriate code
        success = results['failed'] == 0
        print(f"\nIntegration tests {'PASSED' if success else 'FAILED'}")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        if not args.no_cleanup:
            runner.final_cleanup()
        return 1
    except Exception as e:
        print(f"Critical error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
