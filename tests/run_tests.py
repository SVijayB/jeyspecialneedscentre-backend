#!/usr/bin/env python3
"""
CLI interface for running Django REST API integration tests
Provides simple command-line interface for test execution
"""

import sys
import os
import argparse

# Add the tests directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration_runner import IntegrationTestRunner

def print_usage():
    """Print usage examples"""
    print("\nUsage Examples:")
    print("  python run_tests.py                           # Run all tests")
    print("  python run_tests.py --tests auth,branch       # Run specific modules")
    print("  python run_tests.py --tests user --cleanup    # Run user tests with cleanup")
    print("  python run_tests.py --no-cleanup              # Run all tests without cleanup")
    print("  python run_tests.py --list                    # List available test modules")
    print("\nAvailable test modules:")
    print("  auth       - Authentication (login, logout, tokens)")
    print("  branch     - Branch management (CRUD operations)")
    print("  user       - User management (CRUD operations)")
    print("  attendance - Attendance logging (CRUD operations)")
    print("  leave      - Leave applications (CRUD operations)")
    print("  qr         - QR code generation and scanning")

def list_modules():
    """List available test modules"""
    modules = {
        'auth': 'Authentication tests (login, logout, token validation)',
        'branch': 'Branch management tests (create, read, update, delete)',
        'user': 'User management tests (create, read, update, delete)',
        'attendance': 'Attendance logging tests (create, read, update, delete)',
        'leave': 'Leave application tests (create, read, update, delete)',
        'qr': 'QR code tests (generate, scan, validation)'
    }
    
    print("\nAvailable Test Modules:")
    print("=" * 60)
    for module, description in modules.items():
        print(f"{module:12} - {description}")
    print("=" * 60)

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Django REST API Integration Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run all tests
  %(prog)s --tests auth,user         # Run auth and user tests only
  %(prog)s --tests branch --cleanup  # Run branch tests with forced cleanup
  %(prog)s --list                    # Show available test modules
  
Test Execution Order:
  Tests run in dependency order: auth → branch → user → attendance → leave → qr
  
Server Requirements:
  - Django server must be running on http://localhost:8000
  - Admin credentials: username='admin', password='admin123'
  
Integration Test Features:
  - Creates REAL data in the database
  - Tests LIVE API endpoints  
  - Automatically cleans up created data
  - Logs only failures with full debugging info
        """
    )
    
    parser.add_argument(
        '--tests', 
        type=str, 
        metavar='MODULE1,MODULE2',
        help='Comma-separated list of test modules to run (e.g., auth,user,branch)'
    )
    
    parser.add_argument(
        '--cleanup', 
        action='store_true',
        help='Force cleanup after tests (default: auto-cleanup enabled)'
    )
    
    parser.add_argument(
        '--no-cleanup', 
        action='store_true',
        help='Skip final cleanup (useful for debugging)'
    )
    
    parser.add_argument(
        '--list', 
        action='store_true',
        help='List available test modules and exit'
    )
    
    parser.add_argument(
        '--help-usage', 
        action='store_true',
        help='Show detailed usage examples and exit'
    )
    
    args = parser.parse_args()
    
    # Handle special flags
    if args.list:
        list_modules()
        return 0
    
    if args.help_usage:
        print_usage()
        return 0
    
    # Validate arguments
    if args.cleanup and args.no_cleanup:
        print("ERROR: Cannot specify both --cleanup and --no-cleanup")
        return 1
    
    # Parse selected modules
    selected_modules = None
    if args.tests:
        selected_modules = [m.strip() for m in args.tests.split(',')]
        
        # Validate module names
        valid_modules = ['auth', 'branch', 'user', 'attendance', 'leave', 'qr']
        invalid_modules = [m for m in selected_modules if m not in valid_modules]
        
        if invalid_modules:
            print(f"ERROR: Invalid test modules: {invalid_modules}")
            print(f"Valid modules: {', '.join(valid_modules)}")
            print("Use --list to see all available modules")
            return 1
    
    # Show execution plan
    modules_to_run = selected_modules if selected_modules else ['auth', 'branch', 'user', 'attendance', 'leave', 'qr']
    cleanup_enabled = not args.no_cleanup
    
    print("Integration Test Execution Plan:")
    print(f"  Modules: {', '.join(modules_to_run)}")
    print(f"  Cleanup: {'Enabled' if cleanup_enabled else 'Disabled'}")
    print(f"  Server:  http://localhost:8000")
    print("")
    
    # Create and run tests
    runner = IntegrationTestRunner()
    
    try:
        # Run the tests
        results = runner.run_all_tests(selected_modules)
        
        # Perform cleanup unless disabled
        if cleanup_enabled:
            runner.final_cleanup()
        
        # Determine exit code
        success = results['failed'] == 0
        
        if success:
            print(f"\n🎉 All tests PASSED! ({results['passed']}/{results['total']})")
        else:
            print(f"\n❌ {results['failed']} test(s) FAILED out of {results['total']}")
            print(f"   Pass rate: {results['pass_rate']}%")
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
        if cleanup_enabled:
            print("Performing cleanup...")
            runner.final_cleanup()
        return 1
        
    except Exception as e:
        print(f"\n💥 Critical error during test execution:")
        print(f"   {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        sys.exit(1)
