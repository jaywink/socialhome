def safe_clear_cached_property(instance, name):
    """Safely clear a cached property, by wrapping `del` in a try/except."""
    try:
        delattr(instance, name)
    except AttributeError:
        pass
