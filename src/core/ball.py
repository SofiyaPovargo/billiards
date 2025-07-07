
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
        #шарики 1-7 сплошные, а 9-15 с полоской, 8 шарик чёрный для битья
        base_colors = {
            0: (255, 255, 255),   # Белый (биток)
            1: (255, 255, 0),     # Желтый
            2: (0, 0, 255),       # Синий
            3: (255, 0, 0),       # Красный
            4: (128, 0, 128),     # Фиолетовый
            5: (255, 165, 0),     # Оранжевый
            6: (0, 128, 0),       # Зеленый
            7: (128, 0, 0),       # Коричневый
            8: (0, 0, 0),         # Черный
            9: (255, 255, 0),     # Желтый (полосатый)
            10: (0, 0, 255),      # Синий (полосатый)
            11: (255, 0, 0),      # Красный (полосатый)
            12: (128, 0, 128),    # Фиолетовый (полосатый)
            13: (255, 165, 0),    # Оранжевый (полосатый)
            14: (0, 128, 0),      # Зеленый (полосатый)
            15: (128, 0, 0)      # Коричневый (полосатый)
        }
        return base_colors.get(number, (255, 0, 0)) 
    
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