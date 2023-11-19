# flake8: noqa
def classFactory(iface):
    from .src.plugin import Plugin

    return Plugin()
