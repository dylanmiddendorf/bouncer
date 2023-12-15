def static_property(func):
    return staticmethod(property(func))