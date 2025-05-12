"""
This module configures caching for the application.
"""

def disable_caches():
    """Disable all caching mechanisms in the app."""
    import sys
    
    # Force reload all modules
    for module in list(sys.modules.keys()):
        if module not in sys.builtin_module_names and not module.startswith('_'):
            try:
                if sys.modules[module]:
                    try:
                        if hasattr(sys.modules[module], '__cached__'):
                            del sys.modules[module].__cached__
                    except (AttributeError, TypeError):
                        pass
            except KeyError:
                pass
    
    # Disable Python's import cache
    sys.dont_write_bytecode = True
    
    return {
        'SEND_FILE_MAX_AGE_DEFAULT': 0,
        'TEMPLATES_AUTO_RELOAD': True,
        'DEBUG': True,
        'ENV': 'development',
        'EXPLAIN_TEMPLATE_LOADING': True,
        'TESTING': True,  # This disables some internal caching
    } 