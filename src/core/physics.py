import pymunk as pm
from .ball import Ball
from .table import Table

class PhysicsEngine:
    def __init__(self):
        self.space = pm.Space()
        self.space.gravity = (0, 0)
        self.space.damping = 0.1
    
    def add_ball(self, ball: Ball):
        ball.create_pymunk_body(self.space)

    def add_table(self, table: Table):
        table.create_pymunk_borders(self.space)

    def update(self, dt: float):
        self.space.step(dt)

    def is_ball_moving(self, ball_body: pm.Body) -> bool:
        return ball_body.velocity.length > 0.1