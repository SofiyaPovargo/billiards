# src/ui/game_canvas.py
from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLineItem, 
                            QGraphicsEllipseItem, QGraphicsSimpleTextItem, QWidget, QGraphicsPathItem)
from PyQt6.QtCore import Qt, QPointF, QLineF, pyqtSignal
from PyQt6.QtGui import (QBrush, QColor, QPen, QRadialGradient, QPainter, QPainterPath,
                         QFont, QLinearGradient)
import pymunk as pm
import math

class GameCanvas(QGraphicsView):
    game_over_signal = pyqtSignal(int)
    
    def __init__(self, physics, table, balls, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setFixedSize(1000, 550)
        
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, table.width, table.height)
        self.setScene(self.scene)
        
        self.physics = physics
        self.table = table
        self.initial_balls = balls.copy()
        self.balls = balls
        self.pockets = []
        
        self.drag_start = None
        self.cue_line = None
        self.cue_ball = balls[0] if balls else None
        
        # Игровые параметры
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = 1
        self.last_potted_player = None
        
        self.draw_table()
        self.update_balls()
        self.setup_collision_handler()

    def reset_game(self):
        # Сброс игры
        self.balls = self.initial_balls.copy()
        for ball in self.balls:
            if not hasattr(ball, 'body') or ball.body is None:
                ball.create_pymunk_body(self.physics.space)
            ball.in_pocket = False
            ball.body.position = ball.position
            ball.body.velocity = (0, 0)
        
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = 1
        self.last_potted_player = None
        self.update_balls()

    def setup_collision_handler(self):
        handler = self.physics.space.add_collision_handler(0, 1)
        handler.begin = self.handle_ball_pocket_collision

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
        
        self.border_top = self.scene.addRect(0, 0, self.table.width, 20, border_pen, border_brush)
        self.border_bottom = self.scene.addRect(0, self.table.height-20, self.table.width, 20, border_pen, border_brush)
        self.border_left = self.scene.addRect(0, 0, 20, self.table.height, border_pen, border_brush)
        self.border_right = self.scene.addRect(self.table.width-20, 0, 20, self.table.height, border_pen, border_brush)

        # Лунки
        pocket_brush = QBrush(QColor(0, 0, 0))
        for pos in self.table.pockets:
            pocket = self.scene.addEllipse(
                pos[0]-25, pos[1]-25, 50, 50,
                QPen(Qt.PenStyle.NoPen), pocket_brush
            )
            pocket.is_pocket = True 
            self.pockets.append(pocket)

        # Подписи элементов стола для последующего удаления
        self.table_rect.is_table_item = True
        self.border_top.is_table_item = True
        self.border_bottom.is_table_item = True
        self.border_left.is_table_item = True
        self.border_right.is_table_item = True
        
        for pocket in self.pockets:
            pocket.is_table_item = True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.cue_ball and not self.cue_ball.in_pocket:
            # Проверяем, что все шары остановились
            if all(not ball.is_moving() for ball in self.balls if not ball.in_pocket):
                self.drag_start = self.mapToScene(event.pos())
            
    def mouseMoveEvent(self, event):
        if self.drag_start and self.cue_ball and not self.cue_ball.in_pocket:
            end_pos = self.mapToScene(event.pos())
            
            if self.cue_line:
                self.scene.removeItem(self.cue_line)
            
            # Рассчитываем расстояние от битка до курсора
            dx = end_pos.x() - self.cue_ball.position[0]
            dy = end_pos.y() - self.cue_ball.position[1]
            drag_distance = math.hypot(dx, dy)
            angle = math.atan2(dy, dx)
            
            # Параметры кия (динамические)
            min_cue_length = 0  # Минимальная длина кия
            max_cue_length = 400  # Максимальная длина кия
            cue_length = min(max(drag_distance, min_cue_length), max_cue_length)
            
            # Ширина изменяется вместе с длиной
            tip_width = 6  # Ширина толстого конца (у битка)
            base_width = max(2, 6 - (cue_length / max_cue_length) * 4)  # Ширина тонкого конца
            
            # Начальная точка - от битка в направлении курсора
            start_x = self.cue_ball.position[0] + math.cos(angle) * (self.cue_ball.radius + 5)
            start_y = self.cue_ball.position[1] + math.sin(angle) * (self.cue_ball.radius + 5)
            
            # Конечная точка - от битка наружу
            end_x = start_x + math.cos(angle) * cue_length
            end_y = start_y + math.sin(angle) * cue_length
            
            # Градиент для кия
            gradient = QLinearGradient(start_x, start_y, end_x, end_y)
            gradient.setColorAt(0, QColor(139, 69, 19))  # Темный конец (бьющий)
            gradient.setColorAt(1, QColor(210, 180, 140))  # Светлый конец
            
            # Создаем кий как полигон
            path = QPainterPath()
            perpendicular = angle + math.pi/2
            
            # Рассчитываем точки для переменной ширины
            tip_offset_x = math.cos(perpendicular) * tip_width/2
            tip_offset_y = math.sin(perpendicular) * tip_width/2
            base_offset_x = math.cos(perpendicular) * base_width/2
            base_offset_y = math.sin(perpendicular) * base_width/2
            
            # Рисуем трапецию
            path.moveTo(end_x - tip_offset_x, end_y - tip_offset_y)
            path.lineTo(end_x + tip_offset_x, end_y + tip_offset_y)
            path.lineTo(start_x + base_offset_x, start_y + base_offset_y)
            path.lineTo(start_x - base_offset_x, start_y - base_offset_y)
            path.closeSubpath()
            
            self.cue_line = QGraphicsPathItem(path)
            self.cue_line.setBrush(QBrush(gradient))
            self.cue_line.setPen(QPen(Qt.GlobalColor.transparent))
            self.scene.addItem(self.cue_line)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.cue_line:
            if self.cue_ball and not self.cue_ball.in_pocket:
                end_pos = self.mapToScene(event.pos())
                
                # Рассчитываем расстояние для силы удара
                dx = self.cue_ball.position[0] - end_pos.x()
                dy = self.cue_ball.position[1] - end_pos.y()
                drag_distance = math.hypot(dx, dy)
                
                # Параметры силы удара
                min_force = 10
                max_force = 2000
                force_multiplier = 6
                force = min(max(drag_distance * force_multiplier, min_force), max_force)
                
                if force > min_force:
                    angle = math.atan2(dy, dx)
                    self.cue_ball.body.velocity = (force * math.cos(angle), 
                                                force * math.sin(angle))
                    
                    if self.last_potted_player != self.current_player:
                        self.current_player = 3 - self.current_player
            
            # Удаляем кий после удара
            self.scene.removeItem(self.cue_line)
            self.cue_line = None
            self.drag_start = None

    def handle_ball_pocket_collision(self, arbiter, space, data):
        ball_shape = arbiter.shapes[0]
        for ball in self.balls:
            if hasattr(ball, 'body') and ball.body and ball.body == ball_shape.body:
                ball.in_pocket = True
                
                # Обновляем счет
                if ball.number == 0:  # Биток
                    self.last_potted_player = None
                    # Штраф за биток - передача хода
                    self.current_player = 3 - self.current_player
                elif ball.number == 8:  # Черный шар
                    if all(b.in_pocket or b.number == 0 or b.number == 8 for b in self.balls):
                        # Конец игры
                        self.game_over_signal.emit(self.current_player)
                else:
                    if self.current_player == 1:
                        self.player1_score += 1
                    else:
                        self.player2_score += 1
                    self.last_potted_player = self.current_player
                
                return False 
        return True

    def draw_ball(self, ball):
        if ball.in_pocket or not hasattr(ball, 'position') or not ball.position:
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
            text = QGraphicsSimpleTextItem(str(ball.number), ball_item)
            text.setFont(QFont("Arial", 10))
            text_color = Qt.GlobalColor.white if ball.number == 8 else Qt.GlobalColor.black
            text.setBrush(QBrush(text_color))
            text.setPos(
                ball.position[0] - text.boundingRect().width()/2,
                ball.position[1] - text.boundingRect().height()/2
            )

    def update_balls(self):
        # Проверяем, все ли шары остановились
        all_stopped = True
        
        for ball in self.balls:
            if hasattr(ball, 'body') and ball.body:
                ball.update_position()
                if ball.is_moving() and not ball.in_pocket:
                    all_stopped = False
        
        # Удаляем забитые шары
        balls_to_remove = [b for b in self.balls if getattr(b, 'in_pocket', False)]
        for ball in balls_to_remove:
            if ball.body and ball.body.shapes:
                shape = next(iter(ball.body.shapes))
                self.physics.space.remove(ball.body, shape)
            if ball in self.balls:
                self.balls.remove(ball)
        
        # Очищаем сцену от старых шаров
        for item in self.scene.items():
            if isinstance(item, (QGraphicsEllipseItem, QGraphicsSimpleTextItem)):
                if not hasattr(item, 'is_table_item'):
                    self.scene.removeItem(item)
    
        # Рисуем все шары
        for ball in self.balls:
            self.draw_ball(ball)
        
        # Проверяем условия завершения игры
        if len([b for b in self.balls if b.number == 8]) == 0:  # Черный шар забит
            self.game_over_signal.emit(self.current_player)

    def update_display(self):
        self.update_balls()