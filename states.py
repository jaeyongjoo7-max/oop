# states.py : 게임의 단계(상태)들
from abc import ABC, abstractmethod
import pygame
import config
from player import WAIT
from roll_strategies import GaugeRoll
from ui import Button, draw_shade, draw_text, get_font


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
    def draw(self, surface):           # 그리기 (주사위·게이지는 Game이 늘 그리므로, 상태는 자기 것만)
        pass


class RollState(GameState):            # 주사위를 굴릴 차례
    def handle_event(self, event):
        strategy = self.game.gauge.handle_event(event)   # 굴리기가 정해지면 객체, 아니면 None
        if strategy:
            self.start_roll(strategy)

    def update(self, dt):
        self.game.gauge.update(dt)
        if self.game.card_popup.active:  # 황금열쇠 그림을 보는 동안은 AI도 굴리지 않음
            return
        choice = self.game.current_player.choose_roll()  # AI면 0/1/2, 사람이면 WAIT
        if choice is not WAIT:
            self.start_roll(GaugeRoll(choice))

    def start_roll(self, strategy):
        self.game.dice.roll(strategy)    # RandomRoll이든 GaugeRoll이든 똑같이 (다형성)
        self.game.change_state(MovingState(self.game))

    def draw(self, surface):
        pass                             # 주사위·게이지는 Game.draw가 그림


class MovingState(GameState):          # 주사위가 구르고 말이 한 칸씩 움직이는 중
    def __init__(self, game):
        super().__init__(game)
        self.steps_left = None         # None = 아직 주사위가 구르는 중
        self.timer = 0                 # 마지막으로 한 칸 옮긴 뒤 지난 시간

    def handle_event(self, event):
        pass                           # 움직이는 동안은 입력을 받지 않는다

    def update(self, dt):
        p = self.game.current_player

        # 1단계: 주사위가 멈출 때까지 기다린다
        if self.steps_left is None:
            dice = self.game.dice
            dice.update(dt)
            if dice.is_rolling:        # 아직 구르는 중이면 기다린다
                return
            double = " 더블!" if dice.is_double else ""
            self.game.log(f"{p.name}: {dice.total} 나옴{double}")
            self.steps_left = dice.total
            return

        # 2단계: STEP_TIME이 지날 때마다 한 칸씩
        self.timer += dt
        if self.timer < config.STEP_TIME:
            return
        self.timer = 0
        self.game.move_player(p, 1)    # 한 칸 + 정문을 지나면 월급 (카드 이동과 같은 메서드)
        self.steps_left -= 1

        # 3단계: 다 왔으면 칸 도착 처리
        if self.steps_left == 0:
            self.game.board.get_tile(p.position).on_land(p, self.game)   # 칸 종류마다 다른 일 (다형성)
            if self.game.state is self:    # 칸이 다른 상태(BuyState 등)로 바꾸지 않았으면
                self.game.end_turn()

    def draw(self, surface):
        pass                             # 주사위·게이지는 Game.draw가 그림


# ---------------------------------------------------------------------------
# 팝업 단계: 화면을 어둡게 하고 가운데 상자에서 "예/아니오"를 묻는다
# ---------------------------------------------------------------------------
class PopupState(GameState):
    """'예/아니오'를 묻는 팝업 단계의 공통 부모 (11/26).
    흐름(사람은 버튼, AI는 바로 답함, 끝나면 턴 넘기기)과 그리기는 여기 한 곳에만 있고,
    자식은 다른 세 가지(lines, decide, on_answer)만 채운다 (5강 재사용 + 확장)."""

    def __init__(self, game, tile, yes_text, no_text):
        super().__init__(game)
        self.tile = tile
        self.player = game.current_player
        cx, cy = config.SCREEN_W // 2, config.SCREEN_H // 2
        self.box = pygame.Rect((0, 0), config.POPUP_SIZE)
        self.box.center = (cx, cy)
        size = config.POPUP_BUTTON_SIZE
        self.yes_button = Button((cx - 85, cy + 65), size, yes_text)   # B의 Button 재사용 (9강)
        self.no_button = Button((cx + 85, cy + 65), size, no_text)

    # ----- 자식마다 다른 부분 (6강 추상 메서드) -----
    @abstractmethod
    def lines(self):
        """팝업에 쓸 글자 두 줄"""

    @abstractmethod
    def decide(self):
        """player.decide_buy(tile)처럼 플레이어에게 묻는다. True / False / WAIT"""

    @abstractmethod
    def on_answer(self, answer):
        """고른 뒤 할 일"""

    # ----- 모든 팝업이 그대로 물려받는 부분 -----
    def update(self, dt):
        answer = self.decide()           # AI는 바로 True/False, 사람은 WAIT (다형성)
        if answer is not WAIT:
            self.finish(answer)

    def handle_event(self, event):
        if self.yes_button.handle_event(event):
            self.finish(True)
        elif self.no_button.handle_event(event):
            self.finish(False)

    def finish(self, answer):
        self.on_answer(answer)
        self.game.end_turn()             # 턴 넘기기는 Game 한 곳에서만

    def draw(self, surface):
        draw_shade(surface, surface.get_rect(), config.POPUP_SHADE)
        pygame.draw.rect(surface, config.WHITE, self.box, border_radius=18)
        pygame.draw.rect(surface, config.INK, self.box, 4, border_radius=18)
        font = get_font(config.FONT_BODY, 24)
        for i, line in enumerate(self.lines()):
            draw_text(surface, line, font, config.NAVY,
                      (self.box.centerx, self.box.top + 50 + 45 * i))
        self.yes_button.draw(surface)
        self.no_button.draw(surface)


class BuyState(PopupState):
    """빈 땅에 도착했을 때: 살지 묻기"""

    def __init__(self, game, tile):
        super().__init__(game, tile, "사기", "안 사기")

    def lines(self):
        return [f"{self.tile.name}을(를) 살까요?", f"땅값 {self.tile.price:,}원"]

    def decide(self):
        return self.player.decide_buy(self.tile)

    def on_answer(self, answer):
        if answer:
            self.tile.buy(self.player)
            self.game.log(f"{self.player.name}: {self.tile.name} 구입 (-{self.tile.price:,}원)")
        else:
            self.game.log(f"{self.player.name}: {self.tile.name} 안 삼")


class AcquireState(PopupState):
    """상대 땅에서 통행료를 낸 뒤: 인수할지 묻기"""

    def __init__(self, game, tile):
        super().__init__(game, tile, "인수", "안 함")

    def lines(self):
        return [f"{self.tile.name}을(를) 인수할까요?", f"인수 가격 {self.tile.acquire_price:,}원"]

    def decide(self):
        return self.player.decide_acquire(self.tile)

    def on_answer(self, answer):
        if answer:
            price, old_owner = self.tile.acquire_price, self.tile.owner
            self.tile.acquire(self.player)
            self.game.log(f"{self.player.name}: {self.tile.name} 인수 ({old_owner.name}에게 {price:,}원)")
        else:
            self.game.log(f"{self.player.name}: {self.tile.name} 인수 안 함")


class GameOverState(GameState):        # 게임 끝
    def __init__(self, game, winner, reason):
        super().__init__(game)
        self.winner = winner           # 이긴 사람 (무승부면 None)
        self.reason = reason           # 끝난 이유
        self.result = f"{winner.name} 승리!" if winner else "무승부"
        self.game.log(f"게임 끝({reason}): {self.result}")

        cx, cy = config.SCREEN_W // 2, config.SCREEN_H // 2
        self.box = pygame.Rect((0, 0), config.POPUP_SIZE)
        self.box.center = (cx, cy)
        # 나중에 TitleState가 생기면 [메인화면] 버튼으로 바꾼다
        self.again_button = Button((cx, cy + 65), (200, 56), "다시 하기")

    def handle_event(self, event):
        if self.again_button.handle_event(event):
            self.game.restart()

    def update(self, dt):
        pass

    def draw(self, surface):
        draw_shade(surface, surface.get_rect(), config.POPUP_SHADE)
        pygame.draw.rect(surface, config.WHITE, self.box, border_radius=18)
        pygame.draw.rect(surface, config.INK, self.box, 4, border_radius=18)
        draw_text(surface, f"게임 끝 ({self.reason})", get_font(config.FONT_BODY, 20), config.SUB_TEXT,
                  (self.box.centerx, self.box.top + 42))
        draw_text(surface, self.result, get_font(config.FONT_LOGO, 40), config.NAVY,
                  (self.box.centerx, self.box.top + 95))
        self.again_button.draw(surface)
