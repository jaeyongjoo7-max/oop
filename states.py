# states.py : 게임의 단계(상태)들
from abc import ABC, abstractmethod
import pygame
import config
from player import WAIT
from roll_strategies import GaugeRoll


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
        strategy = self.game.gauge.handle_event(event)   # 굴리기가 정해지면 객체, 아니면 None
        if strategy:
            self.start_roll(strategy)

    def update(self, dt):
        self.game.gauge.update(dt)
        choice = self.game.current_player.choose_roll()  # AI면 0/1/2, 사람이면 WAIT
        if choice is not WAIT:
            self.start_roll(GaugeRoll(choice))

    def start_roll(self, strategy):
        self.game.dice.roll(strategy)    # RandomRoll이든 GaugeRoll이든 똑같이 (다형성)
        self.game.change_state(MovingState(self.game))

    def draw(self, surface):
        self.game.dice.draw(surface, config.DICE_CENTER)
        self.game.gauge.draw(surface)


class MovingState(GameState):          # 주사위가 구르고 말이 움직이는 중
    def handle_event(self, event):
        pass                           # 움직이는 동안은 입력을 받지 않는다

    def update(self, dt):
        dice = self.game.dice
        dice.update(dt)
        if dice.is_rolling:            # 아직 구르는 중이면 기다린다
            return

        p = self.game.current_player
        board = self.game.board
        double = " 더블!" if dice.is_double else ""
        self.game.log(f"{p.name}: {dice.total} 나옴{double}")

        passed_start = p.move(dice.total, board.size)   # 정문을 지났으면 True
        if passed_start:
            p.receive(config.SALARY)
            self.game.log(f"{p.name}: 정문 통과, 월급 {config.SALARY:,}원")

        board.get_tile(p.position).on_land(p, self.game)   # 칸 종류마다 다른 일 (다형성)

        if self.game.state is self:    # 칸이 다른 상태(BuyState 등)로 바꾸지 않았으면
            self.game.end_turn()       # 턴 끝 (다음 상태는 Game이 정함)

    def draw(self, surface):
        self.game.dice.draw(surface, config.DICE_CENTER)
        self.game.gauge.draw(surface)


class GameOverState(GameState):        # 게임 끝
    def __init__(self, game, winner, reason):
        super().__init__(game)
        self.winner = winner           # 이긴 사람 (아직 없으면 None)
        self.reason = reason           # 끝난 이유
        self.game.log(f"게임 끝: {reason}")

    def handle_event(self, event):
        pass                           # 나중에: 다시 하기 버튼

    def update(self, dt):
        pass

    def draw(self, surface):
        # 임시 표시: 나중에 결과 화면으로 바꾼다
        center = (config.SCREEN_W // 2, config.SCREEN_H // 2)
        pygame.draw.circle(surface, config.WHITE, center, 40)
