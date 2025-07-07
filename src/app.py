import sys
import math
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QRadialGradient, QPixmap, QPainter, QPainterPath
from core.physics import PhysicsEngine
from core.ball import Ball
from core.table import Table

class BilliardsGame(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        self.setFixedSize(1000, 550)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

        #сцена
        self.scene = QGraphicsScene()
        self.scene.setBackgroundBrush(self.create_table_brush())
        self.setScene(self.scene)

        #физический движок
        self.physics = PhysicsEngine()

        #создание стола с карманами
        self.table = Table(width=900, height=450)
        self.physics.add_table(self.table)
        
        #создаём шары
        self.balls = []
        self.init_balls()

        #таймер обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)
        
        self.drag_start = None
        self.cue_line = None
        self.cue_ball = self.balls[0]

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
        #пирамида
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
        self.scene.addRect(0, 0, 900, 450,
                           QPen(Qt.PenStyle.NoPen),
                           self.create_table_brush())
        #борты
        border_brush = QBrush(QColor(101, 67, 33)) 
        border_pen = QPen(QColor(70, 50, 20), 2)   
        
        self.scene.addRect(0, 0, 900, 20, border_pen, border_brush)  # Верх
        self.scene.addRect(0, 430, 900, 20, border_pen, border_brush)  # Низ
        self.scene.addRect(0, 0, 20, 450, border_pen, border_brush)  # Лево
        self.scene.addRect(880, 0, 20, 450, border_pen, border_brush)  # Право

        #лунки
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
            if self.cue_line:
                self.scene.removeItem(self.cue_line)
                self.cue_line = None

    def mouseMoveEvent(self, event):
        if self.drag_start:
            end_pos = self.mapToScene(event.pos())
            
            if self.cue_line:
                self.scene.removeItem(self.cue_line)
            
            self.cue_line = self.scene.addLine(
                self.drag_start.x(), self.drag_start.y(),
                end_pos.x(), end_pos.y(),
                QColor(Qt.GlobalColor.red)
            )

    def update_game(self):
        self.physics.update(1/60.0)
        for ball in self.balls:  
            ball.update_position()
        self.draw_game()

    def draw_game(self):
        self.scene.clear()
        self.draw_table()
        for ball in self.balls:  
            self.draw_ball(ball)
        if self.cue_line:
            self.scene.addItem(self.cue_line)

    def draw_ball(self, ball):
        if ball.position:
            brush = QBrush(QColor(*ball.color))
            pen = QPen(Qt.GlobalColor.black, 1)
            
            self.scene.addEllipse(
                ball.position[0] - ball.radius,
                ball.position[1] - ball.radius,
                ball.radius * 2,
                ball.radius * 2,
                pen,
                brush)
            
        is_striped = 9 <= ball.number <= 15
        if is_striped:
            stripe_height = ball.radius * 0.6 
            stripe_width = ball.radius * 1.8 
        
            self.scene.addRect(
                ball.position[0] - stripe_width/2,  
                ball.position[1] - stripe_height/2, 
                stripe_width,                  
                stripe_height,                     
                QPen(Qt.PenStyle.NoPen),           
                QBrush(QColor(255, 255, 255)))  
            
        if ball.number > 0:
                text = self.scene.addSimpleText(str(ball.number))
                if is_striped or ball.number == 1:
                    text.setBrush(QColor(0, 0, 0))
                else:
                    text.setBrush(QColor(255, 255, 255) if ball.number != 8 else QColor(255, 255, 0))
                text.setPos(
                    ball.position[0] - text.boundingRect().width()/2,
                    ball.position[1] - text.boundingRect().height()/2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = BilliardsGame()
    game.show()
    sys.exit(app.exec())