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
        if self.game.card_popup.active:  # 황금열쇠 그림을 보는 동안은 AI도 굴리지 않음
            return
        choice = self.game.current_player.choose_roll()  # AI면 0/1/2, 사람이면 WAIT
        if choice is not WAIT:
            self.start_roll(GaugeRoll(choice))

    def start_roll(self, strategy):
        self.game.dice.roll(strategy)    # RandomRoll이든 GaugeRoll이든 똑같이 (다형성)
        self.game.change_state(MovingState(self.game))

    def draw(self, surface):
        self.game.dice.draw(surface, config.DICE_CENTER)
        self.game.gauge.draw(surface)


class MovingState(GameState):          # 주사위가 구르고 말이 한 칸씩 움직이는 중
    def __init__(self, game):
        super().__init__(game)
        self.steps_left = None         # None = 아직 주사위가 구르는 중
        self.timer = 0                 # 마지막으로 한 칸 옮긴 뒤 지난 시간

    def handle_event(self, event):
        pass                           # 움직이는 동안은 입력을 받지 않는다

    def update(self, dt):
        p = self.game.current_player
        board = self.game.board

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

        passed_start = p.move(1, board.size)   # 한 칸만, 정문을 지났으면 True
        self.steps_left -= 1
        if passed_start:
            p.receive(config.SALARY)
            self.game.log(f"{p.name}: 정문 통과, 월급 {config.SALARY:,}원")

        # 3단계: 다 왔으면 칸 도착 처리 (원래 코드와 같음)
        if self.steps_left == 0:
            board.get_tile(p.position).on_land(p, self.game)   # 칸 종류마다 다른 일 (다형성)
            if self.game.state is self:    # 칸이 다른 상태(BuyState 등)로 바꾸지 않았으면
                self.game.end_turn()

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


class BuyState(GameState):
    """빈 땅에 도착했을 때: 살지 말지 묻는 팝업 상태"""

    def __init__(self, game, tile):
        super().__init__(game)
        self.tile = tile
        self.player = game.current_player

        # 임시 팝업 자리. B의 팝업 그리기 도구가 오면 이 부분만 바꾼다.
        cx = config.SCREEN_W // 2
        cy = config.SCREEN_H // 2
        self.box = pygame.Rect(cx - 210, cy - 120, 420, 240)
        self.yes_rect = pygame.Rect(cx - 150, cy + 40, 130, 50)
        self.no_rect = pygame.Rect(cx + 20, cy + 40, 130, 50)

        # 폰트와 어두운 막은 한 번만 만든다
        self.font = pygame.font.SysFont(config.FONT_FALLBACK, 26)
        self.dark = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        self.dark.fill((0, 0, 0, 150))

    def update(self, dt):
        answer = self.player.decide_buy(self.tile)
        if answer is not WAIT:
            self.finish(answer)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.yes_rect.collidepoint(event.pos):
                self.finish(True)
            elif self.no_rect.collidepoint(event.pos):
                self.finish(False)

    def finish(self, answer):
        if answer:
            self.tile.buy(self.player)
            self.game.log(f"{self.player.name}: {self.tile.name} 구입 (-{self.tile.price:,}원)")
        else:
            self.game.log(f"{self.player.name}: {self.tile.name} 안 삼")
        self.game.end_turn()

    def draw(self, surface):
        surface.blit(self.dark, (0, 0))
        pygame.draw.rect(surface, config.WHITE, self.box)
        pygame.draw.rect(surface, config.INK, self.box, 3)
        self.draw_text(surface, f"{self.tile.name}을(를) 살까요?", self.box.centerx, self.box.top + 50)
        self.draw_text(surface, f"땅값 {self.tile.price:,}원", self.box.centerx, self.box.top + 95)
        for rect, label in ((self.yes_rect, "사기"), (self.no_rect, "안 사기")):
            pygame.draw.rect(surface, config.YELLOW, rect)
            pygame.draw.rect(surface, config.INK, rect, 2)
            self.draw_text(surface, label, rect.centerx, rect.centery)

    def draw_text(self, surface, msg, x, y):
        text = self.font.render(msg, True, config.NAVY)
        surface.blit(text, text.get_rect(center=(x, y)))