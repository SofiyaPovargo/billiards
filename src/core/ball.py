
import pymunk as pm

class Ball:
    def __init__(self, 
                number: int, 
                radius: float = 15.0, 
                position: tuple[float, float] = (0, 0), 
                color: tuple[int, int, int] = None, 
                velocity: tuple[float, float] = (0, 0)):
        self.number = number
        self.radius = radius
        self.position = position
        self.color = color if color is not None else self._get_ball_color(number)
        self.velocity = velocity
        self.body = None

    def  _get_ball_color(self, number: int) -> tuple[int, int, int]:
        return (255, 255, 255)
    
    def create_pymunk_body(self, space: pm.Space) -> pm.Body:
        mass = 1.0
        inertia = pm.moment_for_circle(mass, 0, self.radius)
        body = pm.Body(mass, inertia)
        body.position = self.position
        shape = pm.Circle(body, self.radius)
        shape.elasticity = 0.95
        shape.friction = 0.4
        space.add(body, shape)
        self.body = body
        return body
    
    def update_position(self):
        if self.body is not None:
            self.position = (self.body.position.x, self.body.position.y)
            self.velocity = (self.body.velocity.x, self.body.velocity.y)

    def is_moving(self) -> bool:
        if self.body is None:
            return False
        return self.body.velocity.length > 0.1