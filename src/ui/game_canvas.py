# src/ui/game_canvas.py
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QBrush, QColor, QPen, QRadialGradient, QPainter, QFont

class GameCanvas(QGraphicsView):
    def __init__(self, physics_engine, table, balls):
        super().__init__()
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFixedSize(1000, 550)
        
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        self.physics = physics_engine
        self.table = table
        self.balls = balls
        
        self.drag_start = None
        self.cue_line = None
        self.cue_ball = balls[0] if balls else None

    def create_table_brush(self):
        gradient = QRadialGradient(450, 225, 500)
        gradient.setColorAt(0, QColor(0, 80, 0))
        gradient.setColorAt(1, QColor(0, 50, 0))
        return QBrush(gradient)

    def draw_table(self):
        # Основное поле
        self.scene.addRect(0, 0, self.table.width, self.table.height,
                         QPen(Qt.PenStyle.NoPen),
                         self.create_table_brush())
        
        # Борта
        border_brush = QBrush(QColor(101, 67, 33)) 
        border_pen = QPen(QColor(70, 50, 20), 2)   
        
        self.scene.addRect(0, 0, self.table.width, 20, border_pen, border_brush)  # Верх
        self.scene.addRect(0, self.table.height-20, self.table.width, 20, border_pen, border_brush)  # Низ
        self.scene.addRect(0, 0, 20, self.table.height, border_pen, border_brush)  # Лево
        self.scene.addRect(self.table.width-20, 0, 20, self.table.height, border_pen, border_brush)  # Право

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
            self.cue_line = None

    def mouseMoveEvent(self, event):
        if self.drag_start:
            end_pos = self.mapToScene(event.pos())
            
            if self.cue_line:
                self.scene.removeItem(self.cue_line)
            
            self.cue_line = QGraphicsLineItem(QLineF(self.drag_start, end_pos))
            self.cue_line.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            self.scene.addItem(self.cue_line)

    def draw_ball(self, ball):
        if not hasattr(ball, 'position') or not ball.position:
            return
            
        ball_item = QGraphicsEllipseItem(
            ball.position[0] - ball.radius,
            ball.position[1] - ball.radius,
            ball.radius * 2,
            ball.radius * 2
        )
        ball_item.setPen(QPen(Qt.GlobalColor.black, 1))
        ball_item.setBrush(QBrush(QColor(*ball.color)))
        self.scene.addItem(ball_item)
        
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

    def update_display(self):
        self.scene.clear()
        self.draw_table()
        
        for ball in self.balls:
            self.draw_ball(ball)
        
        if self.drag_start and self.cue_line:
            end_pos = self.mapFromGlobal(self.mapToGlobal(QPointF(self.drag_start.x()+50, self.drag_start.y()+50)))
            self.cue_line = QGraphicsLineItem(QLineF(self.drag_start, end_pos))
            self.cue_line.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            self.scene.addItem(self.cue_line)