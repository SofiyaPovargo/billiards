import pymunk as pm
from .ball import Ball
from .table import Table

class PhysicsEngine:
    def __init__(self):
        self.space = pm.Space()
        self.space.gravity = (0, 0)
        self.space.damping = 0.1
        self.pocket_radius = 25
    
    def add_ball(self, ball: Ball):
        ball.create_pymunk_body(self.space)
        for shape in ball.body.shapes:
            shape.collision_type = 0

    def add_table(self, table: Table):
        table.create_pymunk_borders(self.space)
        for pocket_pos in table.pockets:
            pocket_shape = pm.Circle(self.space.static_body, self.pocket_radius, pocket_pos)
            pocket_shape.sensor = True 
            pocket_shape.collision_type = 1
            self.space.add(pocket_shape)

    def update(self, dt: float):
        self.space.step(dt)

    def is_ball_moving(self, ball_body: pm.Body) -> bool:
        return ball_body.velocity.length > 0.1