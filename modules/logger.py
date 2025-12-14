import sys
from datetime import datetime

class Logger:
    """
    A static logging utility.
    - Prints to console in color.
    - Optionally writes to a file with timestamps.
    - Default method .log() prints in GREEN.
    """
    
    # ANSI Colors
    RESET = "\033[0m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    
    # Static configuration
    _file_path = None

    @staticmethod
    def setup_file(path):
        """Enable file logging by setting a file path."""
        Logger._file_path = path

    @staticmethod
    def _output(color, args, kwargs):
        """Internal handler for formatting and writing."""
        # 1. Handle 'sep' and 'end' arguments
        sep = kwargs.get('sep', ' ')
        end = kwargs.get('end', '\n')  # Default to newline if not provided
        
        message = sep.join(map(str, args))
        
        # 2. Print to Console (Colored)
        # Use the 'end' variable instead of hardcoding \n
        sys.stdout.write(f"{color}{message}{Logger.RESET}{end}")
        sys.stdout.flush()  # Crucial for streaming text (characters appear immediately)
        
        # 3. Write to File (Clean text + Timestamp)
        if Logger._file_path:
            # For file logs, we generally prefer full lines, but if you want
            # the file to match the stream, you can adapt this. 
            # This keeps file logs readable by checking if we are just printing a newline.
            if message.strip() == "" and end == "":
                return

            timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
            try:
                with open(Logger._file_path, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} {message}\n")
            except IOError:
                sys.stderr.write(f"{Logger.RED}Error: Could not write to log file.{Logger.RESET}\n")

    @staticmethod
    def log(*args, **kwargs):
        """Default print. Output is GREEN."""
        Logger._output(Logger.GREEN, args, kwargs)

    @staticmethod
    def error(*args, **kwargs):
        """Output is RED."""
        Logger._output(Logger.RED, args, kwargs)

    @staticmethod
    def warn(*args, **kwargs):
        """Output is YELLOW."""
        Logger._output(Logger.YELLOW, args, kwargs)

    @staticmethod
    def info(*args, **kwargs):
        """Output is BLUE."""
        Logger._output(Logger.BLUE, args, kwargs)
        
    @staticmethod
    def print(*args, **kwargs):
        """Output is normal print"""
        print(*args, **kwargs)