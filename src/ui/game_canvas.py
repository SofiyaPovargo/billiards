# src/ui/game_canvas.py
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsLineItem, QGraphicsEllipseItem, QGraphicsSimpleTextItem, QWidget
from PyQt6.QtCore import Qt, QPointF, QLineF
from PyQt6.QtGui import QBrush, QColor, QPen, QRadialGradient, QPainter, QFont
from core.physics import PhysicsEngine
from core.table import Table
from core.ball import Ball
import pymunk as pm

class GameCanvas(QGraphicsView):
    def __init__(self, physics: PhysicsEngine, table: Table, balls: list[Ball], parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFixedSize(1000, 550)
        
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, table.width, table.height)
        self.setScene(self.scene)
        
        self.physics = physics
        self.table = table
        self.balls = balls
        self.pockets = []
        
        self.drag_start = None
        self.cue_line = None
        self.cue_ball = balls[0] if balls else None

        self.draw_table()
        self.update_balls()
        handler = self.physics.space.add_collision_handler(0, 1)
        handler.begin = self.handle_ball_pocket_collection

    def create_table_brush(self):
        gradient = QRadialGradient(450, 225, 500)
        gradient.setColorAt(0, QColor(0, 80, 0))
        gradient.setColorAt(1, QColor(0, 50, 0))
        return QBrush(gradient)

    def draw_table(self):
        # Основное поле
        self.table_rect = self.scene.addRect(0, 0, self.table.width, self.table.height,
                         QPen(Qt.PenStyle.NoPen),
                         self.create_table_brush())
        
        # Борта
        border_brush = QBrush(QColor(101, 67, 33)) 
        border_pen = QPen(QColor(70, 50, 20), 2)   
        
        self.border_top = self.scene.addRect(0, 0, self.table.width, 20, border_pen, border_brush)  # Верх
        self.border_bottom = self.scene.addRect(0, self.table.height-20, self.table.width, 20, border_pen, border_brush)  # Низ
        self.border_left = self.scene.addRect(0, 0, 20, self.table.height, border_pen, border_brush)  # Лево
        self.border_right = self.scene.addRect(self.table.width-20, 0, 20, self.table.height, border_pen, border_brush)  # Право

        # Лунки
        pocket_brush = QBrush(QColor(0, 0, 0))
        for pos in self.table.pockets:
            pocket = self.scene.addEllipse(
                pos[0]-25, pos[1]-25, 50, 50,
                QPen(Qt.PenStyle.NoPen), pocket_brush
            )
            pocket.is_pocket = True 
            self.pockets.append(pocket)

        self.table_rect.is_table_item = True
        self.border_top.is_table_item = True
        self.border_bottom.is_table_item = True
        self.border_left.is_table_item = True
        self.border_right.is_table_item = True
        
        for pocket in self.pockets:
            pocket.is_table_item = True

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
            
            self.cue_line = QGraphicsLineItem(QLineF(self.drag_start, end_pos))
            self.cue_line.setPen(QPen(QColor(Qt.GlobalColor.red), 2))
            self.scene.addItem(self.cue_line)

    def handle_ball_pocket_collection(self, arbiter, space, data):
        ball_shape = arbiter.shapes[0]
        for ball in self.balls:
            if hasattr(ball, 'body') and ball.body and ball.body == ball_shape.body:
                ball.in_pocket = True
                return False 
        return True 

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
        
        if 9 <= ball.number <= 15:
            stripe = QGraphicsEllipseItem(ball_item)  
            stripe.setRect(
                ball.position[0] - ball.radius*0.8,
                ball.position[1] - ball.radius*0.3,
                ball.radius*1.6,
                ball.radius*0.6
            )
            stripe.setPen(QPen(Qt.PenStyle.NoPen))
            stripe.setBrush(QBrush(Qt.GlobalColor.white))
        
        if ball.number > 0:
            text = QGraphicsSimpleTextItem(str(ball.number), ball_item)  # Делаем дочерним
            text.setFont(QFont("Arial", 10))
            text_color = Qt.GlobalColor.white if ball.number == 8 else Qt.GlobalColor.black
            text.setBrush(QBrush(text_color))
            text.setPos(
                ball.position[0] - text.boundingRect().width()/2,
                ball.position[1] - text.boundingRect().height()/2
            )
        
        self.table_rect.is_table_item = True
        self.border_top.is_table_item = True
        self.border_bottom.is_table_item = True
        self.border_left.is_table_item = True
        self.border_right.is_table_item = True
        
        for pocket in self.pockets:
            pocket.is_table_item = True

    def update_balls(self):
        for ball in self.balls:
            if hasattr(ball, 'body') and ball.body:
                ball.update_position()
                ball.position = (ball.body.position.x, ball.body.position.y)
    
        balls_to_remove = [ball for ball in self.balls if getattr(ball, 'in_pocket', False)]
        for ball in balls_to_remove:
            if ball.body:
                self.physics.space.remove(ball.body, ball.body.shapes[0])
            self.balls.remove(ball)
        
        for item in self.scene.items():
            if isinstance(item, (QGraphicsEllipseItem, QGraphicsSimpleTextItem)):
                if not hasattr(item, 'is_table_item'):
                    self.scene.removeItem(item)
        
        for ball in self.balls:
            self.draw_ball(ball)

    def update_display(self):
        self.update_balls()