import pymunk as pm

class Table:
    def __init__(self, width: float = 800, height: float = 400):
        self.width = width
        self.height = height
        self.pockets = self._init_pockets()

    def _init_pockets(self) -> list[tuple[float, float]]:
        return [
            (25, 25),  
            (self.width // 2, 25),
            (self.width - 25, 25), 
            (25, self.height - 25), 
            (self.width // 2, self.height - 25),
            (self.width - 25, self.height - 25)
        ]
    
    def create_pymunk_borders(self, space: pm.Space, thickness: float = 20.0):
        borders = [
            [(0, 0), (self.width, 0)],
            [(0, self.height), (self.width, self.height)],
            [(0, 0), (0, self.height)],
            [(self.width, 0), (self.width, self.height)]
        ]
        for start, end in borders:
            border = pm.Segment(space.static_body, start, end, thickness)
            border.elasticity = 0.8
            space.add(border)