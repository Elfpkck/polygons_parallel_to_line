# noinspection PyPep8Naming
def classFactory(iface):
    from .src.plugin import Plugin

    return Plugin()
