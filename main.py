import sys
from PyQt6.QtWidgets import QApplication, QMainWindow

app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Minimal Qt App")
window.setGeometry(100, 100, 400, 300)

window.show()

sys.exit(app.exec())