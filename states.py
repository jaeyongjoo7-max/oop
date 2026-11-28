# states.py : 게임의 단계(상태)들
from abc import ABC, abstractmethod
import pygame
import config
from player import WAIT
from roll_strategies import GaugeRoll
from tiles import ChanceTile
from ui import (Button, LightButton, draw_background, draw_divider, draw_panel, draw_shade,
                draw_text, fit_text, get_font, load_image)


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
# 팝업 단계: 화면을 어둡게 하고 가운데 아이보리 상자에서 "예/아니오"를 묻는다
# ---------------------------------------------------------------------------
class PopupState(GameState):
    """'예/아니오'를 묻는 팝업 단계의 공통 부모 (11/26).
    흐름(사람은 버튼, AI는 바로 답함, 끝나면 턴 넘기기)과 그리기는 여기 한 곳에만 있고,
    자식은 다른 세 가지(lines, decide, on_answer)만 채운다 (5강 재사용 + 확장).
    11/29: 아이보리 패널·네이비 글자·골드 강조로 모양만 바꿈 (선택지와 동작은 그대로)"""

    def __init__(self, game, tile, yes_text, no_text):
        super().__init__(game)
        self.tile = tile
        self.player = game.current_player
        cx, cy = config.SCREEN_W // 2, config.SCREEN_H // 2
        self.box = pygame.Rect((0, 0), config.POPUP_SIZE)
        self.box.center = (cx, cy)
        size = config.POPUP_BUTTON_SIZE
        button_y = self.box.bottom - 46
        self.yes_button = Button((cx - 85, button_y), size, yes_text, font_size=21, radius=config.PANEL_BUTTON_RADIUS)        # B의 Button 재사용 (9강)
        self.no_button = LightButton((cx + 85, button_y), size, no_text, font_size=21, radius=config.PANEL_BUTTON_RADIUS)

    # ----- 자식마다 다른 부분 (6강 추상 메서드) -----
    @abstractmethod
    def lines(self):
        """팝업에 쓸 글자 두 줄 (질문, 금액)"""

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
        draw_panel(surface, self.box)
        box = self.box
        # 누구의 선택인지 (친구 대결에서 헷갈리지 않게): 플레이어 색 점 + 이름
        small = get_font(config.FONT_BODY, 14)
        who = f"{self.player.name} · 가진 돈 {self.player.money:,}원"
        pygame.draw.circle(surface, self.player.color, (box.x + 28, box.y + 30), 7)
        draw_text(surface, who, small, config.SUB_TEXT, (box.x + 42, box.y + 30), align="left")
        draw_divider(surface, box.x + 20, box.right - 20, box.y + 52)
        question, amount = self.lines()
        draw_text(surface, question, get_font(config.FONT_BUTTON, 27), config.INK,
                  (box.centerx, box.y + 88))
        amount_font = get_font(config.FONT_BODY, 17)
        pill = pygame.Rect(0, 0, amount_font.size(amount)[0] + 36, 34)     # 금액은 골드로 강조
        pill.center = (box.centerx, box.y + 135)
        pygame.draw.rect(surface, config.GOLD, pill, border_radius=17)
        pygame.draw.rect(surface, config.INK, pill, width=2, border_radius=17)
        draw_text(surface, amount, amount_font, config.INK, pill.center)
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
        self.box = pygame.Rect((0, 0), (460, 270))
        self.box.center = (cx, cy)
        button_y = self.box.bottom - 48
        self.again_button = Button((cx - 100, button_y), (180, 52), "다시 하기", font_size=22, radius=config.PANEL_BUTTON_RADIUS)
        self.title_button = LightButton((cx + 100, button_y), (180, 52), "메인화면", font_size=22, radius=config.PANEL_BUTTON_RADIUS)

    def handle_event(self, event):
        if self.again_button.handle_event(event):
            self.game.restart()                              # 같은 상대·같은 이름으로 한 판 더
        elif self.title_button.handle_event(event):
            self.game.go_title()                             # 판을 치우고 메인으로

    def update(self, dt):
        pass

    def draw(self, surface):
        draw_shade(surface, surface.get_rect(), config.POPUP_SHADE)
        draw_panel(surface, self.box)
        box = self.box
        draw_text(surface, f"게임 끝 ({self.reason})", get_font(config.FONT_BODY, 15), config.SUB_TEXT,
                  (box.centerx, box.y + 34))
        draw_divider(surface, box.x + 20, box.right - 20, box.y + 56)
        draw_text(surface, self.result, get_font(config.FONT_BUTTON, 42), config.INK,
                  (box.centerx, box.y + 100))
        scores = " · ".join(f"{p.name} {p.total_assets():,}원" for p in self.game.players)
        font = get_font(config.FONT_BODY, 14)
        draw_text(surface, fit_text("총자산  " + scores, font, box.width - 40), font, config.SUB_TEXT,
                  (box.centerx, box.y + 148))
        self.again_button.draw(surface)
        self.title_button.draw(surface)


# ================================================================
# 메인 화면 (11/29 최종 시안): 메인 → 게임 준비 → 보드
#   게임 방법과 종료 확인은 메인 위에 뜨는 창 (OverlayState)
# ================================================================

def draw_menu_scene(surface, shade=None):
    """메인·게임 준비가 같이 쓰는 뒤 그림: 캠퍼스 배경 + 로고 + 좌하단 말 + 우하단 주사위 (모듈 함수, 2강)"""
    draw_background(surface)
    for path, pos in ((config.LOGO_IMAGE, config.LOGO_POS),
                      (config.DECO_PAWNS_IMAGE, config.DECO_PAWNS_POS),
                      (config.DECO_DICE_IMAGE, config.DECO_DICE_POS)):
        image = load_image(path)
        if image:                         # 그림 파일이 없으면 그냥 건너뜀
            surface.blit(image, pos)      # 8강: screen.blit(그림, (x, y))
    if shade:
        draw_shade(surface, surface.get_rect(), shade)


# ---------- ① 메인 ----------
class TitleState(GameState):
    """① 메인: 로고 + [게임 시작] [게임 방법] [게임 종료]"""
    def __init__(self, game):
        super().__init__(game)
        cx = config.SCREEN_W // 2
        size, font = config.MENU_BUTTON_SIZE, config.MENU_FONT_SIZE
        y_start, y_help, y_exit = config.MENU_BUTTON_YS
        self.start_button = Button((cx, y_start), size, "게임 시작", font_size=font)       # 골드
        self.help_button = LightButton((cx, y_help), size, "게임 방법", font, config.MENU_LIGHT_BUTTON)  # 아이보리
        self.exit_button = LightButton((cx, y_exit), size, "게임 종료", font, config.MENU_LIGHT_BUTTON)
        self.buttons = [self.start_button, self.help_button, self.exit_button]

    def handle_event(self, event):
        if self.start_button.handle_event(event):
            self.game.change_state(SetupState(self.game))
        elif self.help_button.handle_event(event):
            self.open(HelpState(self.game, self))
        elif self.exit_button.handle_event(event):
            self.open(ExitConfirmState(self.game, self))

    def open(self, overlay):
        """메인 위에 창을 띄운다. 메인 버튼은 처음 모양으로 (창을 닫고 돌아왔을 때 눌린 채로 남지 않게)"""
        for button in self.buttons:
            button.reset()
        self.game.change_state(overlay)

    def update(self, dt):
        pass

    def draw(self, surface):
        draw_menu_scene(surface)
        for button in self.buttons:
            button.draw(surface)


# ---------- 메인 위에 뜨는 창 ----------
class OverlayState(GameState):
    """메인 위에 뜨는 창의 공통 부모 (지침서에 없는 새 이름).
    아래 화면(below)을 그대로 그리고 어둡게 덮은 뒤 아이보리 패널을 그린다.
    입력은 이 창만 받는다: 아래 화면의 handle_event는 부르지 않으므로 메인 버튼이 눌리지 않는다."""

    def __init__(self, game, below, panel_rect):
        super().__init__(game)
        self.below = below                     # 닫으면 돌아갈 화면 (메인)
        self.panel = pygame.Rect(panel_rect)

    def close(self):
        self.game.change_state(self.below)

    def update(self, dt):
        pass

    def draw(self, surface):
        self.below.draw(surface)               # 아래 화면은 그리기만
        draw_shade(surface, surface.get_rect(), config.MENU_SHADE)
        draw_panel(surface, self.panel)
        self.draw_content(surface)

    @abstractmethod
    def draw_content(self, surface):
        """패널 안쪽 (자식마다 다름)"""


class HelpState(OverlayState):
    """게임 방법: 주사위 · 땅과 통행료 · 황금열쇠 · 승리 조건"""
    ROWS = [
        ("dice", "주사위", "짧게 클릭하면 일반 굴리기, 길게 누르면 게이지 굴리기."),
        ("land", "땅과 통행료", "빈 땅은 살 수 있고, 상대 땅에 도착하면 통행료를 내요."),
        ("key", "황금열쇠", "황금열쇠 칸에 도착하면 카드를 한 장 뽑아요."),
        ("trophy", "승리 조건",
         f"상대가 파산하거나 {config.MAX_TURNS}턴(두 사람 합계) 뒤 총자산이 더 많으면 이겨요."),
    ]

    def __init__(self, game, below):
        super().__init__(game, below, config.HELP_PANEL_RECT)
        self.close_button = Button((self.panel.centerx, self.panel.bottom - 48), (222, 46), "닫기", font_size=23, radius=config.PANEL_BUTTON_RADIUS)

    def handle_event(self, event):
        if self.close_button.handle_event(event):
            self.close()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()

    def draw_content(self, surface):
        p = self.panel
        draw_text(surface, "게임 방법", get_font(config.FONT_BUTTON, 46), config.INK, (p.centerx, p.y + 48))
        draw_divider(surface, p.x + 34, p.right - 34, p.y + 81)
        title_font = get_font(config.FONT_BODY, 19)
        desc_font = get_font(config.FONT_BODY, 16)
        for i, (icon, title, desc) in enumerate(self.ROWS):
            top = p.y + 85 + i * 82
            icon_rect = pygame.Rect(p.x + 43, top + 14, 49, 49)
            pygame.draw.rect(surface, config.ICON_BG, icon_rect, border_radius=10)
            self.draw_icon(surface, icon, icon_rect)
            draw_text(surface, title, title_font, config.INK, (p.x + 112, top + 26), align="left")
            draw_text(surface, desc, desc_font, config.SUB_TEXT, (p.x + 112, top + 55), align="left")
            if i < len(self.ROWS) - 1:
                draw_divider(surface, p.x + 37, p.right - 37, top + 80)
        self.close_button.draw(surface)

    @staticmethod
    def draw_icon(surface, kind, rect):
        """도움말 아이콘을 도형으로 그린다 (그림 파일 없이)"""
        cx, cy = rect.center
        ink = config.INK
        if kind == "dice":
            die = pygame.Rect(0, 0, 26, 26)
            die.center = (cx, cy)
            pygame.draw.rect(surface, config.WHITE, die, border_radius=6)
            pygame.draw.rect(surface, ink, die, width=2, border_radius=6)
            for dx, dy in ((-6, -6), (0, 0), (6, 6)):
                pygame.draw.circle(surface, ink, (cx + dx, cy + dy), 2)
        elif kind == "land":
            card = pygame.Rect(0, 0, 28, 26)
            card.center = (cx, cy)
            pygame.draw.rect(surface, config.WHITE, card, border_radius=4)
            pygame.draw.rect(surface, config.BAND_150, (card.x, card.y, card.w, 7),
                             border_top_left_radius=4, border_top_right_radius=4)
            pygame.draw.rect(surface, ink, card, width=2, border_radius=4)
            for k in range(2):
                pygame.draw.line(surface, ink, (card.x + 6, card.y + 13 + k * 5), (card.right - 8 - k * 5, card.y + 13 + k * 5), 2)
        elif kind == "key":
            ChanceTile.draw_key(surface, cx + 2, cy, config.ICON_BG, 0.8)   # 판의 열쇠 그림을 재사용
        else:                                                               # 트로피
            cup = pygame.Rect(cx - 10, cy - 13, 20, 16)
            pygame.draw.rect(surface, config.GOLD, cup, border_bottom_left_radius=10, border_bottom_right_radius=10)
            pygame.draw.rect(surface, ink, cup, width=2, border_bottom_left_radius=10, border_bottom_right_radius=10)
            pygame.draw.circle(surface, ink, (cx - 12, cy - 7), 5, 2)
            pygame.draw.circle(surface, ink, (cx + 12, cy - 7), 5, 2)
            pygame.draw.line(surface, ink, (cx, cy + 3), (cx, cy + 8), 3)
            pygame.draw.rect(surface, ink, (cx - 8, cy + 8, 16, 4), border_radius=2)


class ExitConfirmState(OverlayState):
    """종료 확인: [취소]는 메인으로, [종료]는 게임 루프를 끝낸다"""

    def __init__(self, game, below):
        super().__init__(game, below, config.EXIT_PANEL_RECT)
        y = self.panel.y + 149
        self.cancel_button = LightButton((self.panel.centerx - 110, y), (194, 46), "취소", font_size=23, radius=config.PANEL_BUTTON_RADIUS)
        self.quit_button = Button((self.panel.centerx + 109, y), (194, 46), "종료", font_size=23, radius=config.PANEL_BUTTON_RADIUS)

    def handle_event(self, event):
        if self.cancel_button.handle_event(event):
            self.close()
        elif self.quit_button.handle_event(event):
            self.game.running = False          # 기존 게임 루프 종료 (창 닫기 버튼과 같은 길)
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.close()

    def draw_content(self, surface):
        p = self.panel
        draw_text(surface, "게임을 종료할까요?", get_font(config.FONT_BUTTON, 44), config.INK,
                  (p.centerx, p.y + 59))
        draw_divider(surface, p.x + 32, p.right - 32, p.y + 95)
        self.cancel_button.draw(surface)
        self.quit_button.draw(surface)


# ---------- 게임 준비에서 쓰는 위젯 ----------
class ToggleButton(Button):
    """둘 중 하나를 고르는 버튼. 골라진 것만 골드 ([AI와 대결] / [친구와 대결])"""
    def __init__(self, center, size, text):
        super().__init__(center, size, text, font_size=23, radius=config.PANEL_BUTTON_RADIUS)
        self.selected = False                               # 새로 더한 것: 골라졌는가

    def draw(self, surface):
        if self.selected:
            self.color, self.hover_color, self.shine_color = config.GOLD, config.BUTTON_HOVER, config.BUTTON_SHINE
        else:
            self.color, self.hover_color, self.shine_color = config.NAME_BOX_BG, config.LIGHT_HOVER, config.NAME_BOX_BG
        super().draw(surface)                               # 그리기는 부모 것 그대로


class NameBox:
    """이름 칸 하나. 1P·2P가 같은 클래스로 만든 객체 둘 (4강)"""
    PLACEHOLDER = "이름 입력"          # 비어 있을 때 보이는 글자 (시안)

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

    def activate(self):
        """칸을 눌렀을 때: 입력 시작, 한글 입력기 후보 창을 이 칸 근처에"""
        self.active = True
        pygame.key.start_text_input()
        pygame.key.set_text_input_rect(self.rect)

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
                self.activate()                               # 칸을 누르면 입력 시작
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
        pygame.draw.rect(surface, config.NAME_BOX_BG, self.rect, border_radius=10)
        border = config.INK if self.active else config.NAME_LINE
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=10)
        font = get_font(config.FONT_BODY, 17)
        x, y = self.rect.x + 18, self.rect.centery
        if self.text or self.composing:
            draw_text(surface, self.text, font, config.INK, (x, y), align="left")
            if self.composing:                              # 조합 중인 글자는 밑줄
                cx = x + font.size(self.text)[0]
                draw_text(surface, self.composing, font, config.INK, (cx, y), align="left")
                w = font.size(self.composing)[0]
                pygame.draw.line(surface, config.INK, (cx, y + 12), (cx + w, y + 12), 2)
        else:
            draw_text(surface, self.PLACEHOLDER, font, config.HINT_TEXT, (x, y), align="left")
        if self.active and (pygame.time.get_ticks() // 500) % 2 == 0:   # 깜빡이는 커서 막대
            cx = x + font.size(self.text + self.composing)[0] + 2
            pygame.draw.line(surface, config.INK, (cx, y - 12), (cx, y + 12), 2)


class LockedNameBox(NameBox):
    """AI와 할 때 2P 칸: 이름 칸을 물려받고, 입력만 막고 모양만 바꾼다"""
    def __init__(self, center):
        super().__init__(center, "AI")       # name은 부모의 property 그대로 → "AI"

    def handle_event(self, event):
        pass                                 # 오버라이딩: 아무 입력도 받지 않음

    def draw(self, surface):
        pygame.draw.rect(surface, config.LOCKED_BG, self.rect, border_radius=10)
        pygame.draw.rect(surface, config.LOCKED_LINE, self.rect, width=1, border_radius=10)
        draw_text(surface, "AI", get_font(config.FONT_BODY, 17), config.LOCKED_TEXT,
                  (self.rect.x + 18, self.rect.centery), align="left")
        x, y = self.rect.right - 26, self.rect.centery
        body = pygame.Rect(x - 7, y - 3, 14, 11)                                   # 자물쇠 몸통
        loop = pygame.Rect(x - 5, y - 11, 10, 12)                                  # 자물쇠 고리
        pygame.draw.rect(surface, config.LOCKED_TEXT, loop, width=2,
                         border_top_left_radius=5, border_top_right_radius=5)
        pygame.draw.rect(surface, config.LOCKED_TEXT, body, border_radius=3)


# ---------- ② 게임 준비 ----------
class SetupState(GameState):
    """② 게임 준비: 상대 고르기 + 이름 + [메인으로] [시작!]"""
    def __init__(self, game):
        super().__init__(game)
        self.panel = pygame.Rect(config.SETUP_PANEL_RECT)
        p = self.panel
        left_x, right_x = p.x + 167, p.right - 167             # 버튼 두 개의 가운데
        self.ai_button = ToggleButton((left_x, p.y + 129), config.TOGGLE_SIZE, "AI와 대결")
        self.friend_button = ToggleButton((right_x, p.y + 129), config.TOGGLE_SIZE, "친구와 대결")
        box_x = p.x + 116 + config.NAME_BOX_SIZE[0] // 2
        self.p1_box = NameBox((box_x, p.y + 206), "플레이어 1")
        self.p2_box = NameBox((box_x, p.y + 271), "플레이어 2")
        self.ai_box = LockedNameBox((box_x, p.y + 271))
        self.back_button = LightButton((left_x - 1, p.y + 364), (250, 46), "메인으로", font_size=23, radius=config.PANEL_BUTTON_RADIUS)
        self.start_button = Button((right_x + 1, p.y + 364), (250, 46), "시작!", font_size=23, radius=config.PANEL_BUTTON_RADIUS)
        self.set_mode(game.mode)                             # 지난번에 고른 상대를 기억
        self.p1_box.activate()                               # 처음엔 1P 칸에 바로 입력

    def set_mode(self, mode):
        self.mode = mode
        self.ai_button.selected = (mode == "ai")
        self.friend_button.selected = (mode == "person")
        if mode == "ai" and self.p2_box.active:             # 2P 칸이 잠기면 입력도 끝
            self.p2_box.deactivate()

    @property
    def p2(self):
        """지금 쓰는 2P 칸: AI면 잠긴 칸, 친구면 보통 칸 (다형성: 둘 다 handle_event·draw·name이 있다)"""
        return self.ai_box if self.mode == "ai" else self.p2_box

    def focus_name_box(self):
        """상대를 고른 뒤 바로 이름을 칠 수 있게: 1P가 비었으면 1P, 아니면 (친구 대결일 때) 2P"""
        if self.p1_box.active or self.p2.active:
            return
        if not self.p1_box.text:
            self.p1_box.activate()
        elif self.mode == "person" and not self.p2_box.text:
            self.p2_box.activate()

    def handle_event(self, event):
        if self.ai_button.handle_event(event):
            self.set_mode("ai")
            self.focus_name_box()
        elif self.friend_button.handle_event(event):
            self.set_mode("person")
            self.focus_name_box()
        elif self.start_button.handle_event(event):
            self.start_game()
            return
        elif self.back_button.handle_event(event):
            self.p1_box.deactivate()
            self.p2.deactivate()
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
        draw_menu_scene(surface, config.MENU_SHADE)
        draw_panel(surface, self.panel)
        p = self.panel
        draw_text(surface, "게임 준비", get_font(config.FONT_BUTTON, 46), config.INK, (p.centerx, p.y + 46))
        draw_divider(surface, p.x + 36, p.right - 36, p.y + 83)
        self.ai_button.draw(surface)
        self.friend_button.draw(surface)
        chip_font = get_font(config.FONT_BODY, 15)
        for box, color, tag in ((self.p1_box, config.P1_RED, "1P"), (self.p2, config.P2_BLUE, "2P")):
            chip = pygame.Rect(p.x + 40, 0, 61, 40)
            chip.centery = box.rect.centery
            pygame.draw.rect(surface, color, chip, border_radius=8)
            draw_text(surface, tag, chip_font, config.WHITE, chip.center)
            box.draw(surface)
        draw_divider(surface, p.x + 36, p.right - 36, p.y + 317)
        self.back_button.draw(surface)
        self.start_button.draw(surface)
