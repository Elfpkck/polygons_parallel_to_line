from qgis.PyQt.QtCore import QCoreApplication


def tr(string: str) -> str:
    return QCoreApplication.translate("Processing", string)
