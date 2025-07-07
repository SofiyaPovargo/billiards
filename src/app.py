import sys
import math
from PyQt6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                            QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem)
from PyQt6.QtCore import Qt, QTimer, QPointF, QLineF
from PyQt6.QtGui import (QBrush, QColor, QPen, QRadialGradient,
                         QPainter, QFont)
from core.physics import PhysicsEngine
from core.ball import Ball
from core.table import Table

class BilliardsGame(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        self.setFixedSize(1000, 550)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Сцена
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(self.create_table_brush())
        self.setScene(self.scene)

        # Физический движок
        self.physics = PhysicsEngine()

        # Создание стола с карманами
        self.table = Table(width=900, height=450)
        self.physics.add_table(self.table)
        
        # Создаём шары
        self.balls = []
        self.init_balls()

        # Таймер обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)  # ~60 FPS
        
        # Управление
        self.drag_start = None
        self.cue_line = None
        self.cue_ball = self.balls[0]

        # Первоначальная отрисовка
        self.draw_game()

    def create_table_brush(self):
        gradient = QRadialGradient(450, 225, 500)
        gradient.setColorAt(0, QColor(0, 80, 0))
        gradient.setColorAt(1, QColor(0, 50, 0))
        return QBrush(gradient)

    def init_balls(self):
        ball_radius = 15
        self.balls.append(Ball(0, ball_radius, (300, 225)))
        pyramid_order = [
            [1],            # первый ряд
            [2, 9],         # второй ряд
            [3, 7, 8],      # третий ряд
            [10, 6, 4, 5],  # четвертый ряд
            [11, 15, 14, 12, 13]  # пятый ряд
        ]
        
        start_x, start_y = 600, 225
        spacing = ball_radius * 2.2

        for row in range(len(pyramid_order)):
            for col in range(len(pyramid_order[row])):
                ball_num = pyramid_order[row][col]
                x = start_x + row * spacing * math.cos(math.pi/6)
                y = start_y + (col - row/2) * spacing
                self.balls.append(Ball(ball_num, ball_radius, (x, y)))

        for ball in self.balls:
            self.physics.add_ball(ball)

    def draw_table(self):
        # Основное поле
        self.scene.addRect(0, 0, 900, 450,
                         QPen(Qt.PenStyle.NoPen),
                         self.create_table_brush())
        
        # Борта
        border_brush = QBrush(QColor(101, 67, 33)) 
        border_pen = QPen(QColor(70, 50, 20), 2)   
        
        self.scene.addRect(0, 0, 900, 20, border_pen, border_brush)  # Верх
        self.scene.addRect(0, 430, 900, 20, border_pen, border_brush)  # Низ
        self.scene.addRect(0, 0, 20, 450, border_pen, border_brush)  # Лево
        self.scene.addRect(880, 0, 20, 450, border_pen, border_brush)  # Право

        # Лунки
        pocket_brush = QBrush(QColor(0, 0, 0))
        for pos in self.table.pockets:
            self.scene.addEllipse(
                pos[0]-25, pos[1]-25, 50, 50,
                QPen(Qt.PenStyle.NoPen), pocket_brush
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start = self.mapToScene(event.pos())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drag_start:
            end_pos = self.mapToScene(event.pos())
            dx = self.drag_start.x() - end_pos.x()
            dy = self.drag_start.y() - end_pos.y()
            
            if self.cue_ball.body:
                self.cue_ball.body.velocity = (dx * 2, dy * 2)
            
            self.drag_start = None
            self.cue_line = None  # Сбрасываем линию

    def mouseMoveEvent(self, event):
        if self.drag_start:
            end_pos = self.mapToScene(event.pos())
            
            # Удаляем старую линию, если она есть
            if self.cue_line:
                self.scene.removeItem(self.cue_line)
            
            # Создаем новую линию
            self.cue_line = QGraphicsLineItem(
                QLineF(self.drag_start, end_pos)
            )
            self.cue_line.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            self.scene.addItem(self.cue_line)

    def update_game(self):
        self.physics.update(1/60.0)
        for ball in self.balls:
            ball.update_position()
        self.draw_game()

    def draw_game(self):
        self.scene.clear()
        self.draw_table()
        
        # Рисуем шары
        for ball in self.balls:
            self.draw_ball(ball)
        
        # Рисуем линию прицеливания заново, если нужно
        if self.drag_start and self.cue_line:
            end_pos = self.mapFromGlobal(self.mapToGlobal(QPointF(self.drag_start.x()+50, self.drag_start.y()+50)))
            self.cue_line = QGraphicsLineItem(
                QLineF(self.drag_start, end_pos)
            )
            self.cue_line.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            self.scene.addItem(self.cue_line)

    def draw_ball(self, ball):
        if not hasattr(ball, 'position') or not ball.position:
            return
            
        # Основной шар
        ball_item = QGraphicsEllipseItem(
            ball.position[0] - ball.radius,
            ball.position[1] - ball.radius,
            ball.radius * 2,
            ball.radius * 2
        )
        ball_item.setPen(QPen(Qt.GlobalColor.black, 1))
        ball_item.setBrush(QBrush(QColor(*ball.color)))
        self.scene.addItem(ball_item)
        
        # Полоса для полосатых шаров
        is_striped = 9 <= ball.number <= 15
        if is_striped:
            stripe = QGraphicsEllipseItem(
                ball.position[0] - ball.radius*0.8,
                ball.position[1] - ball.radius*0.3,
                ball.radius*1.6,
                ball.radius*0.6
            )
            stripe.setPen(QPen(Qt.PenStyle.NoPen))
            stripe.setBrush(QBrush(QColor(255, 255, 255)))
            self.scene.addItem(stripe)
        
        # Номер на шаре (кроме битка)
        if ball.number > 0:
            text = QGraphicsSimpleTextItem(str(ball.number))
            text.setFont(QFont("Arial", 10))
            text_color = (0, 0, 0) if is_striped or ball.number == 1 else (255, 255, 255) if ball.number != 8 else (255, 255, 0)
            text.setBrush(QColor(*text_color))
            text.setPos(
                ball.position[0] - text.boundingRect().width()/2,
                ball.position[1] - text.boundingRect().height()/2
            )
            self.scene.addItem(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = BilliardsGame()
    game.show()
    sys.exit(app.exec())