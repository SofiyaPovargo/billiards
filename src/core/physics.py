import pymunk as pm
from .ball import Ball
from .table import Table

class PhysicsEngine:
    def __init__(self):
        self.space = pm.Space()
        self.space.gravity = (0, 0)
        self.space.damping = 0.3
        self.pocket_radius = 18
        
    def add_ball(self, ball: Ball):
        # Создаем физическое тело шара
        mass = 1.0
        inertia = pm.moment_for_circle(mass, 0, ball.radius)
        body = pm.Body(mass, inertia)
        body.position = ball.position
        shape = pm.Circle(body, ball.radius)
        shape.elasticity = 0.95
        shape.friction = 0.7
        shape.collision_type = 1 
        
        # Добавляем в пространство
        self.space.add(body, shape)
        ball.body = body

    def add_table(self, table: Table):
        # Добавление стола можно делать напрямую, так как оно происходит при инициализации
        table.create_pymunk_borders(self.space)
        for pocket_pos in table.pockets:
            pocket_shape = pm.Circle(self.space.static_body, self.pocket_radius, pocket_pos)
            pocket_shape.sensor = True
            pocket_shape.collision_type = 2
            self.space.add(pocket_shape)

    def update(self, dt: float):
        self.space.step(dt)

    def is_ball_moving(self, ball_body: pm.Body) -> bool:
        return ball_body.velocity.length > 1