import sys
import math
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QTimer, QPointF
from PyQt6.QtGui import QBrush, QColor, QPen, QRadialGradient, QPixmap, QPainter
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

    def create_table_brush(self):
        gradient = QRadialGradient(450, 225, 500)
        gradient.setColorAt(0, QColor(0, 80, 0))
        gradient.setColorAt(1, QColor(0, 50, 0))
        return QBrush(gradient)

    def init_balls(self):
        ball_radius = 15
        self.balls.append(Ball(0, ball_radius, (300, 225)))

        #пирамида
        start_x, start_y = 600, 225
        spacing = ball_radius * 2.2

        for row in range(5):
            for col in range(row + 1):
                ball_num = row * (row + 1) // 2 + col + 1
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
        
        borders = [
            [(0, 0), (900, 0), (900, 20), (0, 20)],           # Верх
            [(0, 430), (900, 430), (900, 450), (0, 450)],      # Низ
            [(0, 0), (20, 0), (20, 450), (0, 450)],            # Лево
            [(880, 0), (900, 0), (900, 450), (880, 450)]       # Право
        ]
        
        for border in borders:
            self.scene.addPolygon([QPointF(*p) for p in border], 
                                 border_pen, border_brush)
        
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
        self.cue_ball.update_position()
        self.target_ball.update_position()
        self.draw_game()

    def draw_game(self):
        self.scene.clear()
        self.scene.addRect(0, 0, 900, 450, brush=QBrush(Qt.GlobalColor.green))
        self.draw_ball(self.cue_ball)
        self.draw_ball(self.target_ball)
        
        if self.cue_line:
            self.scene.addItem(self.cue_line)

    def draw_ball(self, ball):
        if ball.position:
            self.scene.addEllipse(
                ball.position[0] - ball.radius,
                ball.position[1] - ball.radius,
                ball.radius * 2,
                ball.radius * 2,
                brush=QBrush(QColor(*ball.color))
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    game = BilliardsGame()
    game.show()
    sys.exit(app.exec())