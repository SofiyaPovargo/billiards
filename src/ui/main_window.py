# src/ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                            QPushButton, QMessageBox, QHBoxLayout)
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self, game_canvas):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        self.setFixedSize(1000, 600)  # Увеличил высоту для отображения счета
        
        self.game_canvas = game_canvas
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS
        
        # Создаем виджеты для счета
        self.score_widget = QWidget()
        self.score_layout = QHBoxLayout()
        
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = 1
        
        self.player1_label = QLabel(f"Игрок 1: {self.player1_score}")
        self.player2_label = QLabel(f"Игрок 2: {self.player2_score}")
        self.current_player_label = QLabel(f"Текущий ход: Игрок {self.current_player}")
        
        for label in [self.player1_label, self.player2_label, self.current_player_label]:
            label.setFont(QFont("Arial", 14))
            self.score_layout.addWidget(label)
        
        self.score_widget.setLayout(self.score_layout)
        
        # Основной layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.score_widget)
        layout.addWidget(self.game_canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Связываем сигнал завершения игры с обработчиком
        self.game_canvas.game_over_signal.connect(self.handle_game_over)

    def update_game(self):
        self.game_canvas.physics.update(1/60.0)
        self.game_canvas.update_display()
        
        # Обновляем счет
        self.player1_label.setText(f"Игрок 1: {self.game_canvas.player1_score}")
        self.player2_label.setText(f"Игрок 2: {self.game_canvas.player2_score}")
        self.current_player_label.setText(f"Текущий ход: Игрок {self.game_canvas.current_player}")

    def handle_game_over(self, winner):
        msg = QMessageBox()
        msg.setWindowTitle("Игра окончена")
        msg.setText(f"Игрок {winner} победил!")
        msg.setInformativeText("Хотите сыграть еще?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        ret = msg.exec()
        if ret == QMessageBox.StandardButton.Yes:
            self.game_canvas.reset_game()
        else:
            self.close()