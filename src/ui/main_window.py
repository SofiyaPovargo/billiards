# src/ui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self, game_canvas):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        
        self.game_canvas = game_canvas
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.game_canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def update_game(self):
        self.game_canvas.physics.update(1/60.0)
        for ball in self.game_canvas.balls:
            ball.update_position()
        self.game_canvas.update_display()