
import time
import functools
from modules.logger import Logger
def timer(func):
    """
    A decorator that prints the execution time of the function it decorates.
    """
    @functools.wraps(func)  # Preserves the original function's metadata (name, docstring)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # Start the clock
        
        result = func(*args, **kwargs)    # Execute the actual function
        
        end_time = time.perf_counter()    # Stop the clock
        execution_time = end_time - start_time
        
        Logger.info(f"\n--> Function '{func.__name__}' took {execution_time:.4f} seconds to finish.")
        return result
        
    return wrapper