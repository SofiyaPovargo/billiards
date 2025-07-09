# src/core/game_rules.py
from core.ball import Ball

class GameRules:
    def __init__(self):
        self.player1_score = 0
        self.player2_score = 0
        self.current_player = 1
        self.game_state = "playing"
        self.player1_type = None  # Шар с полоской или сплошной 
        self.player2_type = None  
        self.first_ball_pocketed = None

    def check_pocketed_balls(self, balls: list[Ball], table):
        for ball in balls:
            if getattr(ball, 'in_pocket', False):
                self.handle_pocketed_ball(ball)
                if ball.body:
                    ball.body = None

    def handle_pocketed_ball(self, ball: Ball):
        if ball.number == 0:
            self.handle_cue_ball_pocketed()
        if ball.number == 8:
            self.handle_8ball_pocketed()
        else:
            self.handle_regular_ball_pocketed(ball)

    def handle_cue_ball_pocketed(self):
        self.current_player = 2 if self.current_player == 1 else 1

    def handle_8ball_pocketed(self):
        if self.all_balls_pocketed_correctly():
            self.game_state = f"player{self.current_player}_won"
        else:
            self.game_state = f"player{2 if self.current_player == 1 else 1}_won"
        
    def handle_regular_ball_pocketed(self, ball: Ball):
        if self.first_ball_pocketed is None:
            self.first_ball_pocketed = ball.number
            self.assign_ball_type()

        if self.is_ball_valid_for_player(ball):
            if self.current_player == 1:
                self.player1_score += 1
            else:
                self.player2_score += 1
        else:
            # Если игрок забил шар соперника, ход переходит
            self.current_player = 2 if self.current_player == 1 else 1
            # Также засчитываем очко сопернику
            if self.current_player == 1:
                self.player1_score += 1
            else:
                self.player2_score += 1
        
    def assign_ball_type(self):
        if 1 <= self.first_ball_pocketed <= 7:
            self.player1_type = "solid"
            self.player2_type = "striped"
        if 9 <= self.first_ball_pocketed <= 15:
            self.player1_type = "striped"
            self.player2_type = "solid"

    def is_ball_valid_for_player(self, ball: Ball) -> bool:
        if self.player1_type is None:
            return True
            
        if self.current_player == 1:
            return (self.player1_type == "solid" and 1 <= ball.number <= 7) or \
                (self.player1_type == "striped" and 9 <= ball.number <= 15)
        else:
            return (self.player2_type == "solid" and 1 <= ball.number <= 7) or \
                (self.player2_type == "striped" and 9 <= ball.number <= 15)
        
    def all_balls_pocketed_correctly(self) -> bool:
        return True
    