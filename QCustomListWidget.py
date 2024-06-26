from PyQt5.QtWidgets import QListWidget
from PyQt5.QtCore import pyqtSignal, Qt


class QCustomListWidget(QListWidget):
    itemMoved = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def dropEvent(self, event):
        super().dropEvent(event)
        self.itemMoved.emit()