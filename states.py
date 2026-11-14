# states.py : 게임의 단계(상태)들
from abc import ABC, abstractmethod
import pygame
import config


class GameState(ABC):                  # 추상 클래스: 모든 상태의 공통 틀
    def __init__(self, game):
        self.game = game               # 상태가 Game에게 부탁할 때 쓴다

    @abstractmethod
    def handle_event(self, event):     # 입력
        pass

    @abstractmethod
    def update(self, dt):              # 시간 (dt는 밀리초)
        pass

    @abstractmethod
    def draw(self, surface):           # 그리기
        pass


class RollState(GameState):            # 주사위를 굴릴 차례
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.game.log("굴리기 클릭")
            self.game.change_state(MovingState(self.game))

    def update(self, dt):
        pass

    def draw(self, surface):
        # 임시 표시: 나중에 B의 굴리기 버튼으로 바꾼다
        center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        pygame.draw.circle(surface, config.YELLOW, center, 40)

class MovingState(GameState):          # 말이 움직이는 중
    def __init__(self, game):
        super().__init__(game)         # 부모의 __init__으로 self.game 저장
        self.elapsed = 0               # 이 상태에서 지난 시간(ms)

    def handle_event(self, event):
        pass                           # 움직이는 동안은 입력을 받지 않는다

    def update(self, dt):
        self.elapsed += dt             # 매 프레임 지난 시간을 더한다
        if self.elapsed >= config.MOVE_TIME:
            self.game.log("이동 끝")
            self.game.end_turn()                 # 다음 상태는 Game이 정함

    def draw(self, surface):
        # 임시 표시: 나중에 말 이동 애니메이션으로 바꾼다
        center = (config.SCREEN_WIDTH // 2, config.SCREEN_HEIGHT // 2)
        pygame.draw.circle(surface, config.P1_RED, center, 40)