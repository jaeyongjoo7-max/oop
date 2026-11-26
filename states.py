# states.py : 게임의 단계(상태)들
from abc import ABC, abstractmethod
import pygame
import config
from player import WAIT
from roll_strategies import GaugeRoll
from ui import Button, draw_shade, draw_text, get_font, draw_pawn


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
        self.again_button = Button((cx - 100, cy + 65), (180, 56), "다시 하기")
        self.title_button = Button((cx + 100, cy + 65), (180, 56), "메인화면")

    def handle_event(self, event):
        if self.again_button.handle_event(event):
            self.game.restart()                              # 같은 상대·같은 이름으로 한 판 더
        elif self.title_button.handle_event(event):
            self.game.change_state(TitleState(self.game))    # 처음 화면으로

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
        self.title_button.draw(surface)


# ================================================================
# 시작 화면 (11/26 2안): 타이틀 → 게임 설정 → 게임
# ================================================================

# ---------- 두 화면이 같이 쓰는 그리기 도구 (모듈 함수, 2강) ----------
def draw_box_cover(surface):
    """노란 배경 + 남색 테두리: 보드게임 상자 뚜껑 느낌"""
    surface.fill(config.YELLOW)
    frame = pygame.Rect(20, 20, config.SCREEN_W - 40, config.SCREEN_H - 40)
    pygame.draw.rect(surface, config.NAVY, frame, width=6, border_radius=30)


def draw_logo(surface, text, font, pos, align="center"):
    """그림자를 먼저 그리고 그 위에 글자 (시안의 두꺼운 그림자)"""
    x, y = pos
    draw_text(surface, text, font, config.LOGO_SHADOW, (x, y + 9), align)
    draw_text(surface, text, font, config.NAVY, (x, y), align)


def draw_mini_board(surface, topleft):
    """타이틀 오른쪽 작은 판: 5×5에서 바깥 16칸만 판 색으로 칠한다"""
    x0, y0 = topleft
    panel = pygame.Rect(x0, y0, 418, 418)
    pygame.draw.rect(surface, config.INK, panel.move(0, 12), border_radius=30)   # 그림자
    pygame.draw.rect(surface, config.NAVY, panel, border_radius=30)
    for r in range(5):
        for c in range(5):
            if 0 < r < 4 and 0 < c < 4:
                continue                                   # 가운데 9칸은 비움
            if r in (0, 4) and c in (0, 4):
                color = config.YELLOW                      # 모서리
            elif r == 0:
                color = config.BAND_200                    # 윗줄
            elif r == 4:
                color = config.BAND_100                    # 아랫줄
            elif c == 0:
                color = config.BAND_150                    # 왼쪽
            else:
                color = config.BAND_250                    # 오른쪽
            cell = pygame.Rect(x0 + 34 + c * 70, y0 + 34 + r * 70, 64, 64)
            pygame.draw.rect(surface, color, cell, border_radius=10)
    draw_pawn(surface, config.P1_RED, (x0 + 34 + 2 * 70 + 32, y0 + 34 + 4 * 70 + 58), 46)  # 아랫줄
    draw_pawn(surface, config.P2_BLUE, (x0 + 34 + 4 * 70 + 32, y0 + 34 + 1 * 70 + 58), 46)  # 오른쪽 줄


# ---------- 버튼: B의 Button을 물려받아 색만 바꾼다 (5강 상속 = 재사용 + 확장) ----------
class DarkButton(Button):
    """남색 바탕에 노란 글자 버튼 ([플레이], [시작!])"""
    def __init__(self, center, size, text):
        super().__init__(center, size, text, config.NAVY)   # 위치·크기·클릭 판정은 부모 것
        self.text_color = config.YELLOW
        self.hover_color = config.NAVY_HOVER
        self.shine_color = config.NAVY_SHINE


class ToggleButton(Button):
    """둘 중 하나를 고르는 버튼. 골라진 것만 노랗게 ([AI와 대결] / [친구와 대결])"""
    def __init__(self, center, size, text):
        super().__init__(center, size, text)
        self.selected = False                               # 새로 더한 것: 골라졌는가

    def draw(self, surface):
        if self.selected:
            self.color, self.text_color = config.YELLOW, config.NAVY
            self.hover_color, self.shine_color = config.BUTTON_HOVER, config.BUTTON_SHINE
        else:
            self.color, self.text_color = config.NAVY, config.WHITE
            self.hover_color, self.shine_color = config.NAVY_HOVER, config.NAVY_SHINE
        super().draw(surface)                               # 그리기는 부모 것 그대로


# ---------- 이름 칸 ----------
class NameBox:
    """이름 칸 하나. 1P·2P가 같은 클래스로 만든 객체 둘 (4강)"""
    def __init__(self, center, hint):
        self.rect = pygame.Rect((0, 0), config.NAME_BOX_SIZE)
        self.rect.center = center
        self.hint = hint              # 비워 두면 쓰는 이름 ("플레이어 1")
        self.text = ""                # 다 쓴 글자
        self.composing = ""           # 한글 조합 중인 글자 ("ㄱ" → "가" 가 되기 전)
        self.active = False           # 지금 입력 중인 칸인가

    @property
    def name(self):
        """실제로 쓸 이름: 조합 중인 글자까지 포함, 비었으면 hint"""
        return (self.text + self.composing).strip()[:config.NAME_MAX_LEN] or self.hint

    def deactivate(self):
        """칸을 떠날 때: 조합 중이던 마지막 글자("곽호랭"의 "랭")까지 확정한다"""
        if self.composing:
            self.text = (self.text + self.composing)[:config.NAME_MAX_LEN]
            self.composing = ""
            pygame.key.stop_text_input()     # 입력기에 남은 조합 글자를 비운다
            pygame.key.start_text_input()    # (안 비우면 다음 칸에 그 글자가 늦게 들어갈 수 있음)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True                            # 칸을 누르면 입력 시작
            elif self.active:
                self.deactivate()                             # 다른 곳을 누르면 확정
            return
        if not self.active:
            return
        # 강의 범위 밖: TEXTINPUT / TEXTEDITING
        #   한글은 ㄱ+ㅏ → 가 처럼 조합되어서 KEYDOWN으로는 받을 수 없다.
        #   TEXTINPUT은 완성된 글자를, TEXTEDITING은 조합 중인 글자를 알려 준다.
        if event.type == pygame.TEXTINPUT:
            self.text = (self.text + event.text)[:config.NAME_MAX_LEN]
            self.composing = ""
        elif event.type == pygame.TEXTEDITING:
            self.composing = event.text
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_BACKSPACE and not self.composing:
            self.text = self.text[:-1]

    def draw(self, surface):
        border = config.YELLOW if self.active else config.NAVY
        pygame.draw.rect(surface, config.WHITE, self.rect, border_radius=12)
        pygame.draw.rect(surface, border, self.rect, width=4 if self.active else 3, border_radius=12)
        font = get_font(config.FONT_BUTTON, 26)
        x, y = self.rect.x + 16, self.rect.centery
        shown = self.text + self.composing
        if shown:
            draw_text(surface, shown, font, config.NAVY, (x, y), align="left")
        else:
            draw_text(surface, self.hint, font, config.HINT_TEXT, (x, y), align="left")
        if self.active:                                     # 글자 뒤 커서 막대
            cx = x + font.size(shown)[0] + 2
            pygame.draw.line(surface, config.NAVY, (cx, y - 14), (cx, y + 14), 2)


class LockedNameBox(NameBox):
    """AI와 할 때 2P 칸: 이름 칸을 물려받고, 입력만 막고 모양만 바꾼다"""
    def __init__(self, center):
        super().__init__(center, "AI")       # name은 부모의 property 그대로 → "AI"

    def handle_event(self, event):
        pass                                 # 오버라이딩: 아무 입력도 받지 않음

    def draw(self, surface):
        pygame.draw.rect(surface, config.LOCKED_BG, self.rect, border_radius=12)
        pygame.draw.rect(surface, config.LOCKED_LINE, self.rect, width=3, border_radius=12)
        draw_text(surface, "AI", get_font(config.FONT_BUTTON, 26), config.NAVY,
                  (self.rect.x + 16, self.rect.centery), align="left")
        body = pygame.Rect(self.rect.right - 38, self.rect.centery - 3, 18, 13)    # 자물쇠 몸통
        loop = pygame.Rect(self.rect.right - 35, self.rect.centery - 13, 12, 14)   # 자물쇠 고리
        pygame.draw.rect(surface, config.LOCKED_LINE, loop, width=3,
                         border_top_left_radius=6, border_top_right_radius=6)
        pygame.draw.rect(surface, config.LOCKED_LINE, body, border_radius=3)


# ---------- ① 타이틀 ----------
class TitleState(GameState):
    """① 타이틀: 외대 마블 로고 + [플레이] + 작은 판"""
    def __init__(self, game):
        super().__init__(game)
        self.play_button = DarkButton(config.PLAY_BTN_POS, config.PLAY_BTN_SIZE, "플레이")
        self.logo_font = get_font(config.FONT_LOGO, 150)     # 폰트는 한 번만 만든다

    def handle_event(self, event):
        if self.play_button.handle_event(event):
            self.game.change_state(SetupState(self.game))

    def update(self, dt):
        pass

    def draw(self, surface):
        draw_box_cover(surface)
        draw_logo(surface, "외대", self.logo_font, (130, 250), align="left")
        draw_logo(surface, "마블", self.logo_font, (130, 405), align="left")
        self.play_button.draw(surface)
        x, y = config.MINI_BOARD_TOPLEFT
        draw_mini_board(surface, (x, y))
        self.game.dice.draw(surface, (x + 209, y + 209))     # 판 가운데에 B의 주사위 재사용


# ---------- ② 게임 설정 ----------
class SetupState(GameState):
    """② 게임 설정: 상대 고르기 + 이름 + [시작!]"""
    def __init__(self, game):
        super().__init__(game)
        cx = config.SCREEN_W // 2
        self.ai_button = ToggleButton((cx - 160, 250), config.TOGGLE_SIZE, "AI와 대결")
        self.friend_button = ToggleButton((cx + 160, 250), config.TOGGLE_SIZE, "친구와 대결")
        self.p1_box = NameBox((cx + 60, 400), "플레이어 1")
        self.p2_box = NameBox((cx + 60, 490), "플레이어 2")
        self.ai_box = LockedNameBox((cx + 60, 490))
        self.start_button = DarkButton((cx, 620), (260, 72), "시작!")
        self.back_button = DarkButton((140, 80), (180, 50), "처음으로")
        self.title_font = get_font(config.FONT_LOGO, 64)
        self.label_font = get_font(config.FONT_BUTTON, 24)
        self.chip_font = get_font(config.FONT_BUTTON, 20)
        self.set_mode(game.mode)                             # 지난번에 고른 상대를 기억
        self.p1_box.active = True                            # 처음엔 1P 칸에 바로 입력

    def set_mode(self, mode):
        self.mode = mode
        self.ai_button.selected = (mode == "ai")
        self.friend_button.selected = (mode == "person")

    @property
    def p2(self):
        """지금 쓰는 2P 칸: AI면 잠긴 칸, 친구면 보통 칸 (다형성: 둘 다 handle_event·draw·name이 있다)"""
        return self.ai_box if self.mode == "ai" else self.p2_box

    def handle_event(self, event):
        if self.ai_button.handle_event(event):
            self.set_mode("ai")
        elif self.friend_button.handle_event(event):
            self.set_mode("person")
        elif self.start_button.handle_event(event):
            self.start_game()
            return
        elif self.back_button.handle_event(event):
            self.game.change_state(TitleState(self.game))
            return
        self.p1_box.handle_event(event)
        self.p2.handle_event(event)

    def start_game(self):
        self.p1_box.deactivate()                             # 조합 중이던 글자까지 확정
        self.p2.deactivate()
        self.game.mode = self.mode
        self.game.names = [self.p1_box.name, self.p2.name]
        self.game.restart()                                  # 플레이어 만들기는 Game.make_players 한 곳

    def update(self, dt):
        pass

    def draw(self, surface):
        cx = config.SCREEN_W // 2
        draw_box_cover(surface)
        self.back_button.draw(surface)
        draw_logo(surface, "게임 설정", self.title_font, (cx, 130))
        draw_text(surface, "누구와 할까요?", self.label_font, config.NAVY, (cx, 200))
        self.ai_button.draw(surface)
        self.friend_button.draw(surface)
        draw_text(surface, "이름", self.label_font, config.NAVY, (cx, 335))
        rows = [(self.p1_box, config.P1_RED, "1P"), (self.p2, config.P2_BLUE, "2P")]
        for box, color, tag in rows:
            row = pygame.Rect(cx - 310, box.rect.centery - 38, 620, 76)
            pygame.draw.rect(surface, config.NAVY, row.move(0, 6), border_radius=20)   # 그림자
            pygame.draw.rect(surface, config.WHITE, row, border_radius=20)
            pygame.draw.rect(surface, config.NAVY, row, width=4, border_radius=20)
            draw_pawn(surface, color, (row.x + 38, row.bottom - 12), 46)
            chip = pygame.Rect(row.x + 70, row.centery - 17, 52, 34)
            pygame.draw.rect(surface, color, chip, border_radius=17)
            draw_text(surface, tag, self.chip_font, config.WHITE, chip.center)
            box.draw(surface)
        self.start_button.draw(surface)