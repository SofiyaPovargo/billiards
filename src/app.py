# src/app.py
import sys
import math
import os
from PyQt6.QtWidgets import QApplication
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.physics import PhysicsEngine
from core.ball import Ball
from core.table import Table
from ui.game_canvas import GameCanvas
from ui.main_window import MainWindow

def init_balls(table_width, table_height):
    balls = []
    ball_radius = 15
    balls.append(Ball(0, ball_radius, (300, table_height/2)))
    
    pyramid_order = [
        [1],            # первый ряд
        [2, 9],         # второй ряд
        [3, 7, 8],      # третий ряд
        [10, 6, 4, 5],  # четвертый ряд
        [11, 15, 14, 12, 13]  # пятый ряд
    ]
    
    start_x, start_y = 600, table_height/2
    spacing = ball_radius * 2.2

    for row in range(len(pyramid_order)):
        for col in range(len(pyramid_order[row])):
            ball_num = pyramid_order[row][col]
            x = start_x + row * spacing * math.cos(math.pi/6)
            y = start_y + (col - row/2) * spacing
            balls.append(Ball(ball_num, ball_radius, (x, y)))
    
    return balls

def main():
    app = QApplication(sys.argv)
    
    # Инициализация игровых компонентов
    physics = PhysicsEngine()
    table = Table(width=900, height=450)
    physics.add_table(table)
    
    balls = init_balls(table.width, table.height)
    for ball in balls:
        physics.add_ball(ball)
    
    # Создание UI
    game_canvas = GameCanvas(
        physics=physics,
        table=table,
        balls=balls
    )

    window = MainWindow(game_canvas)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()