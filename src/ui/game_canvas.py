# src/ui/game_canvas.py
from PyQt6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsLineItem, 
                            QGraphicsEllipseItem, QGraphicsSimpleTextItem, QWidget, QGraphicsPathItem, QApplication)
from PyQt6.QtCore import Qt, QPointF, QLineF, pyqtSignal
from PyQt6.QtGui import (QBrush, QColor, QPen, QRadialGradient, QPainter, QPainterPath, QAction,
                         QFont, QLinearGradient)
import pymunk as pm
import math
from core.physics import PhysicsEngine
from core.ball import Ball
from core.game_rules import GameRules
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap, QImage

class GameCanvas(QGraphicsView):
    game_over_signal = pyqtSignal(int)
    
    def __init__(self, physics, table, balls, parent=None):
        super().__init__(parent)
        self.setRenderHints(QPainter.RenderHint.Antialiasing | 
                          QPainter.RenderHint.TextAntialiasing | 
                          QPainter.RenderHint.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)
        self.setMinimumSize(800, 450)

        
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, table.width, table.height)
        self.setScene(self.scene)
        
        self.game_rules = GameRules() 

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
        
        self.original_table_width = table.width
        self.original_table_height = table.height

        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, table.width, table.height)
        self.setScene(self.scene)

        self.draw_table()
        self.update_balls()
        self.setup_collision_handler()

        self.allow_cue_ball_reposition = False
        
        self.cue_ball_start_pos = (300, table.height/2)  
        self.cue_ball_out_pos = (50, table.height/2)
        self.dragging_cue_ball = False

        self.potted_balls_order = []

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
    
        restart_action = QAction("Начать заново", self)
        restart_action.triggered.connect(self.reset_game)
        self.addAction(restart_action)
        
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(lambda: QApplication.instance().quit())
        self.addAction(exit_action)

    
    def reset_game(self):
        # Полная очистка физического пространства
        for body in self.physics.space.bodies:
            self.physics.space.remove(body)
        for shape in self.physics.space.shapes:
            self.physics.space.remove(shape)
        
        # Пересоздаем физический движок
        self.physics = PhysicsEngine()
        
        # Восстанавливаем стол
        self.physics.add_table(self.table)
        
        # Полностью пересоздаем шары из начальных параметров
        self.balls = []
        for initial_ball in self.initial_balls:
            new_ball = Ball(
                number=initial_ball.number,
                radius=initial_ball.radius,
                position=initial_ball.position,
                color=initial_ball.color
            )
            self.physics.add_ball(new_ball)
            self.balls.append(new_ball)
            # Гарантируем нулевую скорость
            if new_ball.body:
                new_ball.body.velocity = (0, 0)
        
        # Полный сброс игрового состояния
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = 1
        self.last_potted_player = None
        self.potted_balls_order = []
        self.cue_ball = self.balls[0] if self.balls else None
        self.game_rules = GameRules()  # Полностью новые правила
        self.allow_cue_ball_reposition = False
        self.dragging_cue_ball = False
        
        # Очистка сцены от графических элементов
        for item in self.scene.items():
            if not hasattr(item, 'is_table_item'):
                self.scene.removeItem(item)
        
        # Перерисовка стола и шаров
        self.draw_table()
        self.update_balls()
        self.setup_collision_handler()

    def setup_collision_handler(self):
            # Обработчик столкновений шаров с лузами
        handler = self.physics.space.add_collision_handler(1, 2)  # Шары (1) и лузы (2)
        handler.begin = self.handle_ball_pocket_collision
    
        # Обработчик столкновений шаров между собой
        ball_handler = self.physics.space.add_collision_handler(1, 1)
        ball_handler.begin = self.handle_ball_collision
        ball_handler.pre_solve = self.handle_ball_collision

    def create_table_brush(self):
        gradient = QRadialGradient(self.table.width/2, self.table.height/2, 
                                 max(self.table.width, self.table.height)/1.5)
        gradient.setColorAt(0, QColor(0, 100, 0))
        gradient.setColorAt(0.5, QColor(0, 80, 0))
        gradient.setColorAt(1, QColor(0, 60, 0))
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
                pos[0]-20, pos[1]-20, 40, 40,
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
                    
                    # Проверяем, был ли забит шар в предыдущем ходе
                    if not any(ball.in_pocket for ball in self.balls if ball.number != 0):
                        # Если не было забито шаров, меняем игрока
                        self.current_player = 3 - self.current_player
                        self.game_rules.current_player = self.current_player
            
            # Удаляем кий после удара
            self.scene.removeItem(self.cue_line)
            self.cue_line = None
            self.drag_start = None

    def handle_ball_pocket_collision(self, arbiter, space, data):
        ball_shape = arbiter.shapes[0]
        for ball in self.balls:
            if hasattr(ball, 'body') and ball.body and ball.body == ball_shape.body:
                ball.in_pocket = True
                
                if ball.number == 0:  # Биток
                    # Переносим биток в специальную позицию
                    ball.body.position = self.cue_ball_out_pos
                    ball.body.velocity = (0, 0)
                    ball.in_pocket = False
                    self.dragging_cue_ball = True
                    # Штраф за биток - передача хода
                    self.current_player = 3 - self.current_player
                    return False
                
                elif ball.number == 8:  # Черный шар
                    if ball.body and ball.body.shapes:
                        shape = next(iter(ball.body.shapes))
                        space.remove(ball.body, shape)
                    # Проверяем условия победы
                    player_balls = []
                    opponent_balls = []
                    
                    if self.game_rules.player1_type == "solid":
                        player_balls = [b for b in self.initial_balls if 1 <= b.number <= 7]
                        opponent_balls = [b for b in self.initial_balls if 9 <= b.number <= 15]
                    else:
                        player_balls = [b for b in self.initial_balls if 9 <= b.number <= 15]
                        opponent_balls = [b for b in self.initial_balls if 1 <= b.number <= 7]
                    
                    # Все шары игрока должны быть забиты до черного
                    player_balls_potted = all(b.in_pocket for b in player_balls)
                    opponent_balls_potted = any(b.in_pocket for b in opponent_balls)
                    
                    if (self.current_player == 1 and self.game_rules.player1_type == "solid" and player_balls_potted) or \
                    (self.current_player == 2 and self.game_rules.player2_type == "solid" and player_balls_potted):
                        self.game_over_signal.emit(self.current_player)  # Победа
                    else:
                        self.game_over_signal.emit(3 - self.current_player)  # Поражение
                    return False
                
                else:
                    self.potted_balls_order.append(ball.number)
                    # Используем game_rules для обработки забитых шаров
                    self.game_rules.check_pocketed_balls([ball], self.table)
                    
                    # Обновляем текущего игрока из game_rules
                    self.current_player = self.game_rules.current_player
                    
                    # Обновляем счет
                    self.player1_score = self.game_rules.player1_score
                    self.player2_score = self.game_rules.player2_score
        return True

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Проверяем, что все шары остановились
            all_stopped = all(not ball.is_moving() for ball in self.balls if not ball.in_pocket)
            
            if not all_stopped:
                return
                
            if self.cue_ball and not self.cue_ball.in_pocket:
                self.drag_start = self.mapToScene(event.pos())

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

    def handle_ball_collision(self, arbiter, space, data):
        return True
    
    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        self.adjust_table_size()
        
    def adjust_table_size(self):
        """Адаптирует размер стола к текущему размеру виджета"""
        # Рассчитываем новые размеры с сохранением пропорций
        view_rect = self.viewport().rect()
        width_ratio = view_rect.width() / self.original_table_width
        height_ratio = view_rect.height() / self.original_table_height
        scale_factor = min(width_ratio, height_ratio) * 0.95  # Небольшой отступ
        
        # Применяем масштабирование
        self.resetTransform()
        self.scale(scale_factor, scale_factor)
        
        # Центрируем сцену
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)