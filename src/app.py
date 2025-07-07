import sys
from PyQt6.QtWidgets import QApplication, QGraphicsView, QGraphicsScene
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor
from core.physics import PhysicsEngine
from core.ball import Ball
from core.table import Table

class BilliardsGame(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2D Бильярд")
        self.setFixedSize(950, 500)
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.physics = PhysicsEngine()
        self.table = Table(width=900, height=450)
        self.physics.add_table(self.table)
        
        self.cue_ball = Ball(0, position=(300, 225))
        self.target_ball = Ball(1, position=(600, 225))
        
        self.physics.add_ball(self.cue_ball)
        self.physics.add_ball(self.target_ball)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(16)
        
        self.drag_start = None
        self.cue_line = None

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