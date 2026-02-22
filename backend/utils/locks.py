import threading

# Global lock for akshare operations to prevent concurrent initialization/usage issues
# particularly with py_mini_racer (V8) which is not thread-safe during initialization.
akshare_lock = threading.Lock()
