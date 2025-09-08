"""
Console color utilities for test output
"""

class Colors:
    """ANSI color codes for console output"""
    
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    # Reset
    RESET = '\033[0m'
    
    @staticmethod
    def success(text):
        """Green text for success"""
        return f"{Colors.GREEN}{text}{Colors.RESET}"
    
    @staticmethod
    def error(text):
        """Red text for errors"""
        return f"{Colors.RED}{text}{Colors.RESET}"
    
    @staticmethod
    def warning(text):
        """Yellow text for warnings"""
        return f"{Colors.YELLOW}{text}{Colors.RESET}"
    
    @staticmethod
    def info(text):
        """Blue text for info"""
        return f"{Colors.BLUE}{text}{Colors.RESET}"
    
    @staticmethod
    def bold(text):
        """Bold text"""
        return f"{Colors.BOLD}{text}{Colors.RESET}"
    
    @staticmethod
    def header(text):
        """Bold cyan text for headers"""
        return f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}"
    
    @staticmethod
    def pass_text():
        """Green PASS text"""
        return f"{Colors.BOLD}{Colors.GREEN}PASS{Colors.RESET}"
    
    @staticmethod
    def fail_text():
        """Red FAIL text"""
        return f"{Colors.BOLD}{Colors.RED}FAIL{Colors.RESET}"
