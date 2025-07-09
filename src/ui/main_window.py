# src/ui/main_window.py
from PyQt6.QtCore import (QTimer, QPropertyAnimation, QEasingCurve, QRect,
                         Qt, QPointF)
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                            QPushButton, QMessageBox, QHBoxLayout, QSizePolicy)
from PyQt6.QtGui import QFont, QColor, QPainter

class MainWindow(QMainWindow):
    def __init__(self, game_canvas):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        self.setFixedSize(1000, 650) 
        
        self.game_canvas = game_canvas
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS
        
        self.create_score_widget()
        self.init_score_balls()
        
        # Основной layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(self.score_widget)
        layout.addWidget(self.game_canvas)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # Связываем сигнал завершения игры с обработчиком
        self.game_canvas.game_over_signal.connect(self.handle_game_over)

    def create_score_widget(self):
        self.score_widget = QWidget()
        self.score_widget.setStyleSheet("""
            background: #2a2a2a;
            border-radius: 10px;
            padding: 10px;
        """)
        
        self.score_layout = QHBoxLayout()
        self.score_layout.setContentsMargins(20, 10, 20, 10)
        self.score_layout.setSpacing(30)
        
        # Контейнер игрока 1
        self.player1_container = QWidget()
        self.player1_layout = QHBoxLayout()
        self.player1_layout.setSpacing(10)
        self.player1_layout.setContentsMargins(0, 0, 0, 0)

        # Шары игрока 1 (1-7)
        for i in range(1, 8):
            self.add_ball_to_layout(self.player1_layout, i)
                
        self.player1_label = self.create_score_label()
        self.player1_layout.addWidget(self.player1_label)
        self.player1_container.setLayout(self.player1_layout)
        
        # Индикатор текущего игрока
        self.current_player_indicator = QLabel("▶ ИГРОК 1 ◀")
        self.current_player_indicator.setStyleSheet("""
            font: bold 18px;
            color: #4CAF50;
            qproperty-alignment: AlignCenter;
            min-width: 150px;
        """)
        
        # Контейнер игрока 2
        self.player2_container = QWidget()
        self.player2_layout = QHBoxLayout()
        self.player2_layout.setSpacing(10)
        self.player2_layout.setContentsMargins(0, 0, 0, 0)

        # Шары игрока 2 (9-15)
        for i in range(9, 16):
            self.add_ball_to_layout(self.player2_layout, i)

        self.player2_label = self.create_score_label()
        self.player2_layout.addWidget(self.player2_label)
        self.player2_container.setLayout(self.player2_layout)
        
        # Собираем все вместе
        self.score_layout.addWidget(self.player1_container)
        self.score_layout.addWidget(self.current_player_indicator)
        self.score_layout.addWidget(self.player2_container)
        self.score_widget.setLayout(self.score_layout)

    def create_score_label(self):
        label = QLabel("0")
        label.setStyleSheet("""
            font: bold 24px;
            color: white;
            min-width: 40px;
            max-width: 40px;
            qproperty-alignment: AlignCenter;
            background: #333;
            border-radius: 5px;
            padding: 5px;
        """)
        return label

    def add_ball_to_layout(self, layout, ball_number):
        ball = QLabel()
        ball.setFixedSize(24, 24)
        color = self.get_ball_color(ball_number)
        ball.setStyleSheet(f"""
            background: {color};
            border-radius: 12px;
            border: 1px solid black;
        """)
        layout.addWidget(ball)

    def init_score_balls(self):
        # Инициализация уже выполнена в create_score_widget()
        pass

    def update_game(self):
        self.game_canvas.physics.update(1/60.0)
        self.game_canvas.update_display()
        
        # Обновляем счет
        self.player1_label.setText(str(self.game_canvas.player1_score))
        self.player2_label.setText(str(self.game_canvas.player2_score))
        
        # Обновляем отображение шаров
        self.update_score_balls()
        
        # Обновляем индикатор текущего игрока
        if self.game_canvas.current_player == 1:
            self.current_player_indicator.setText("▶ ИГРОК 1 ◀")
            self.current_player_indicator.setStyleSheet("""
                font: bold 18px;
                color: #4CAF50;
                qproperty-alignment: AlignCenter;
            """)
        else:
            self.current_player_indicator.setText("▶ ИГРОК 2 ◀")
            self.current_player_indicator.setStyleSheet("""
                font: bold 18px;
                color: #2196F3;
                qproperty-alignment: AlignCenter;
            """)

    def update_score_balls(self):
        # Игрок 1 (шары 1-7)
        for i in range(1, 8):
            ball = self.player1_layout.itemAt(i-1).widget()
            state = "active" if i <= self.game_canvas.player1_score else "inactive"
            self.update_ball_style(ball, i, state)
        
        # Игрок 2 (шары 9-15)
        for i in range(9, 16):
            ball = self.player2_layout.itemAt(i-9).widget()
            state = "active" if (i-8) <= self.game_canvas.player2_score else "inactive"
            self.update_ball_style(ball, i, state)

    def update_ball_style(self, ball, number, state):
        color = self.get_ball_color(number)
        if state == "active":
            ball.setStyleSheet(f"""
                background: {color};
                border-radius: 12px;
                border: 2px solid white;
            """)
        else:
            ball.setStyleSheet(f"""
                background: #555;
                border-radius: 12px;
                border: 1px solid #333;
            """)

    def get_ball_color(self, number):
        colors = {
            1: "#FFFF00", 2: "#0000FF", 3: "#FF0000", 4: "#800080",
            5: "#FFA500", 6: "#008000", 7: "#800000", 8: "#000000",
            9: "#FFFF00", 10: "#0000FF", 11: "#FF0000", 12: "#800080",
            13: "#FFA500", 14: "#008000", 15: "#800000"
        }
        return colors.get(number, "#AAAAAA")

    def animate_ball(self, player, ball_number):
        if player == 1:
            ball = self.player1_layout.itemAt(ball_number-1).widget()
        else:
            ball = self.player2_layout.itemAt(ball_number-9).widget()
        
        if not ball:
            return
            
        animation = QPropertyAnimation(ball, b"pos")
        animation.setDuration(300)
        animation.setStartValue(ball.pos())
        animation.setEndValue(QPointF(ball.x(), ball.y()-10))
        animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        
        animation.finished.connect(lambda: self.reset_ball_position(ball))
        animation.start()

    def reset_ball_position(self, ball):
        if not ball:
            return
            
        anim = QPropertyAnimation(ball, b"pos")
        anim.setDuration(200)
        anim.setStartValue(ball.pos())
        anim.setEndValue(QPointF(ball.x(), ball.y()+10))
        anim.start()

    def handle_game_over(self, winner):
        msg = QMessageBox()
        msg.setWindowTitle("Игра окончена")
        msg.setText(f"Игрок {winner} победил!")
        msg.setInformativeText("Хотите сыграть еще?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        ret = msg.exec()
        if ret == QMessageBox.StandardButton.Yes:
            self.game_canvas.reset_game()
            self.player1_label.setText("0")
            self.player2_label.setText("0")
            self.update_score_balls()  # Сбрасываем отображение шаров
        else:
            self.close()