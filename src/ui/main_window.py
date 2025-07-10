# src/ui/main_window.py
from PyQt6.QtCore import (QTimer, QPropertyAnimation, QEasingCurve, QRect,
                         Qt, QPointF)
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel,
                            QPushButton, QMessageBox, QHBoxLayout, QSizePolicy, QApplication, 
                            QStackedWidget)
from PyQt6.QtGui import QFont, QColor, QPainter

class MainWindow(QMainWindow):
    def __init__(self, game_canvas):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        self.setMinimumSize(900, 600)
        
        self.game_canvas = game_canvas
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS
        
        # Словари для хранения виджетов шаров
        self.player1_balls = {}
        self.player2_balls = {}
        
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
        
        # Контейнер игрока 1 (сплошные шары)
        self.player1_container = QWidget()
        self.player1_layout = QHBoxLayout()
        self.player1_layout.setSpacing(10)
        self.player1_layout.setContentsMargins(0, 0, 0, 0)
        
        # Контейнер для забитых шаров игрока 1
        self.player1_potted_container = QWidget()
        self.player1_potted_layout = QHBoxLayout()
        self.player1_potted_layout.setSpacing(5)
        self.player1_potted_layout.setContentsMargins(0, 0, 0, 0)
        self.player1_potted_container.setLayout(self.player1_potted_layout)
        
        # Оставшиеся шары игрока 1
        for i in range(1, 8):
            self.add_ball_to_layout(self.player1_layout, i, "player1")
        
        self.player1_label = self.create_score_label()
        
        # Собираем контейнер игрока 1
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
        
        # Контейнер игрока 2 (полосатые шары)
        self.player2_container = QWidget()
        self.player2_layout = QHBoxLayout()
        self.player2_layout.setSpacing(10)
        self.player2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Контейнер для забитых шаров игрока 2
        self.player2_potted_container = QWidget()
        self.player2_potted_layout = QHBoxLayout()
        self.player2_potted_layout.setSpacing(5)
        self.player2_potted_layout.setContentsMargins(0, 0, 0, 0)
        self.player2_potted_container.setLayout(self.player2_potted_layout)
        
        self.player2_label = self.create_score_label()
        self.player2_layout.addWidget(self.player2_label)
        
        # Оставшиеся шары игрока 2
        for i in range(9, 16):
            self.add_ball_to_layout(self.player2_layout, i, "player2")
        
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

    def add_ball_to_layout(self, layout, ball_number, player):
        container = QWidget()
        container.setFixedSize(36, 36)
        container.setStyleSheet("background: transparent;")
        
        # Основной круг шара
        ball = QLabel(container)
        ball.setGeometry(0, 0, 36, 36)
        color = self.get_ball_color(ball_number)
        ball.setStyleSheet(f"""
            background: {color};
            border-radius: 18px;
            border: 1px solid black;
        """)
        
        # Добавляем полосу для шаров 9-15
        if 9 <= ball_number <= 15:
            stripe = QLabel(container)
            stripe.setGeometry(1, 15, 34, 8)  # Позиция и размер полосы
            stripe.setStyleSheet("""
                background: white;
                border-radius: 3px;
                border: none;
            """)
        
        container.setProperty("ball_number", ball_number)
        layout.addWidget(container)
        
        # Сохраняем ссылку на виджет шара
        if player == "player1":
            self.player1_balls[ball_number] = container
        else:
            self.player2_balls[ball_number] = container

    def init_score_balls(self):
        # Инициализация уже выполнена в create_score_widget()
        pass

    def update_game(self):
        self.game_canvas.physics.update(1/60.0)
        self.game_canvas.update_display()
        
        # Обновляем счет (теперь player2 слева, player1 справа)
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
        # Очищаем контейнеры забитых шаров
        for i in reversed(range(self.player1_potted_layout.count())):
            self.player1_potted_layout.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.player2_potted_layout.count())):
            self.player2_potted_layout.itemAt(i).widget().setParent(None)
        
        # Добавляем забитые шары в порядке их попадания
        for ball_number in self.game_canvas.potted_balls_order:
            if 1 <= ball_number <= 7:  # Шары игрока 1
                ball = self.player1_balls.get(ball_number)
                if ball:
                    ball_copy = self.create_ball_copy(ball)
                    self.player1_potted_layout.addWidget(ball_copy)
            elif 9 <= ball_number <= 15:  # Шары игрока 2
                ball = self.player2_balls.get(ball_number)
                if ball:
                    ball_copy = self.create_ball_copy(ball)
                    self.player2_potted_layout.addWidget(ball_copy)
        
        # Обновляем стили оставшихся шаров
        self.update_remaining_balls()

    def create_ball_copy(self, original_ball):
        ball_number = original_ball.property("ball_number")
        container = QWidget()
        container.setFixedSize(36, 36)
        container.setStyleSheet("background: transparent;")
        
        # Основной круг шара
        ball = QLabel(container)
        ball.setGeometry(0, 0, 36, 36)
        color = self.get_ball_color(ball_number)
        ball.setStyleSheet(f"""
            background: {color};
            border-radius: 18px;
            border: 1px solid black;
        """)
        
        # Добавляем полосу для шаров 9-15
        if 9 <= ball_number <= 15:
            stripe = QLabel(container)
            stripe.setGeometry(1, 15, 34, 8)
            stripe.setStyleSheet("""
                background: white;
                border-radius: 3px;
                border: none;
            """)
        
        return container

    def update_remaining_balls(self):
        # Для игрока 1
        potted_solids = [num for num in self.game_canvas.potted_balls_order if 1 <= num <= 7]
        for num in range(1, 8):
            ball = self.player1_balls.get(num)
            if ball:
                if num in potted_solids:
                    ball.hide()
                else:
                    ball.show()
        
        # Для игрока 2
        potted_stripes = [num for num in self.game_canvas.potted_balls_order if 9 <= num <= 15]
        for num in range(9, 16):
            ball = self.player2_balls.get(num)
            if ball:
                if num in potted_stripes:
                    ball.hide()
                else:
                    ball.show()

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
            ball = self.player1_balls.get(ball_number)
        else:
            ball = self.player2_balls.get(ball_number)
        
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
            self.reset_game()  # Вызываем сброс игры
        else:
            QApplication.instance().quit()  # Закрываем приложение

    def reset_game(self):
        # Полный сброс интерфейса
        self.game_canvas.reset_game()
        
        # Очистка контейнеров забитых шаров
        for i in reversed(range(self.player1_potted_layout.count())):
            self.player1_potted_layout.itemAt(i).widget().setParent(None)
        for i in reversed(range(self.player2_potted_layout.count())):
            self.player2_potted_layout.itemAt(i).widget().setParent(None)
        
        # Сброс счетов
        self.player1_label.setText("0")
        self.player2_label.setText("0")
        
        # Восстановление всех шаров в панели
        for ball in self.player1_balls.values():
            ball.show()
        for ball in self.player2_balls.values():
            ball.show()
        
        # Сброс индикатора игрока
        self.current_player_indicator.setText("▶ ИГРОК 1 ◀")
        self.current_player_indicator.setStyleSheet("""
            font: bold 18px;
            color: #4CAF50;
            qproperty-alignment: AlignCenter;
        """)