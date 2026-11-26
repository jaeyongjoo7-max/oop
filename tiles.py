"""판 위의 칸들.

칸 종류마다 on_land()를 다르게 구현한다 (다형성).
Game은 tile.on_land(player, game) 한 줄만 부르면, 칸 종류에 맞는 일이 일어난다.
새로운 칸이 필요하면 if문을 고치지 않고 Tile을 상속한 클래스를 하나 더 만든다 (OCP).
"""
from abc import ABC, abstractmethod

import pygame

import config
from toll_levels import make_toll_level
from ui import draw_shade, draw_text, get_font


# ---------------------------------------------------------------------------
# 칸 클래스들
#   글자 도구는 ui.py의 것을 가져다 쓴다 (예전엔 여기에도 따로 있었음 → 11/26 합침)
# ---------------------------------------------------------------------------
class Tile(ABC):
    """모든 칸의 부모. 모든 칸은 번호, 이름, on_land(), draw()를 가진다."""

    def __init__(self, index, name):
        self.index = index
        self.name = name

    @abstractmethod
    def on_land(self, player, game):
        """말이 이 칸에 멈췄을 때 일어나는 일."""

    def draw(self, surface, rect):
        pygame.draw.rect(surface, config.TILE_BG, rect)
        draw_text(surface, self.name, get_font(config.FONT_BODY, 17), config.NAVY, rect.center)
        pygame.draw.rect(surface, config.INK, rect, 2)

    def _draw_special(self, surface, rect, bg, fg, title, sub, title_size):
        """정문·학사경고처럼 테두리 상자가 있는 특수 칸 모양 (자식들이 같이 쓴다)."""
        pygame.draw.rect(surface, bg, rect)
        pygame.draw.rect(surface, fg, rect.inflate(-10, -10), 3, border_radius=6)
        draw_text(surface, title, get_font(config.FONT_BODY, title_size), fg,
                  (rect.centerx, rect.y + rect.h * 0.38))
        draw_text(surface, sub, get_font(config.FONT_BODY, 14), fg,
                  (rect.centerx, rect.y + rect.h * 0.68))
        pygame.draw.rect(surface, config.INK, rect, 2)


class StartTile(Tile):
    """정문. 지나가거나 도착할 때 받는 월급은 말을 옮기는 쪽(Game.move_player)이 준다."""

    def on_land(self, player, game):
        game.log(f"{player.name}: 정문 도착")

    def draw(self, surface, rect):
        self._draw_special(surface, rect, config.START_BG, config.START_TEXT, self.name, "← 출발", 24)


class IslandTile(Tile):
    """학사경고. 정해진 턴 동안 쉰다. 쉬는 차례를 건너뛰는 건 TurnManager가 한다."""

    def on_land(self, player, game):
        player.start_rest(config.ISLAND_REST_TURNS)     # 쉬는 턴은 Player 안에 숨김 (캡슐화)
        game.log(f"{player.name}: 학사경고! {config.ISLAND_REST_TURNS}턴 쉬기")

    def draw(self, surface, rect):
        self._draw_special(surface, rect, config.ISLAND_BG, config.ISLAND_TEXT, self.name,
                           f"{config.ISLAND_REST_TURNS}턴 쉬기", 20)


class ChanceTile(Tile):
    """황금열쇠. 카드를 한 장 뽑아 실행한다 (카드가 할 일은 카드가 안다)."""

    def on_land(self, player, game):
        card = game.deck.draw()
        game.card_popup.show(card)                     # 카드 그림을 판 가운데에 띄움
        card.execute(player, game)                     # 카드가 할 일은 카드가 안다 (다형성)

    def draw(self, surface, rect):
        pygame.draw.rect(surface, config.CHANCE_BG, rect)
        self._draw_key(surface, rect.centerx + 4, rect.y + rect.h * 0.4)
        draw_text(surface, self.name, get_font(config.FONT_BODY, 16), config.CHANCE_TEXT,
                  (rect.centerx, rect.y + rect.h * 0.77))
        pygame.draw.rect(surface, config.INK, rect, 2)

    @staticmethod
    def _draw_key(surface, cx, cy):
        gold, ink = config.KEY_GOLD, config.INK
        cx, cy = int(cx), int(cy)
        parts = [pygame.Rect(cx - 6, cy - 5, 32, 10),        # 열쇠 몸통
                 pygame.Rect(cx + 18, cy + 3, 6, 10),        # 큰 이
                 pygame.Rect(cx + 9, cy + 3, 6, 7)]          # 작은 이
        for part in parts:
            pygame.draw.rect(surface, gold, part, border_radius=2)
            pygame.draw.rect(surface, ink, part, 3, border_radius=2)
        pygame.draw.circle(surface, gold, (cx - 16, cy), 14)  # 손잡이 고리
        pygame.draw.circle(surface, ink, (cx - 16, cy), 14, 3)
        pygame.draw.circle(surface, config.CHANCE_BG, (cx - 16, cy), 5)
        pygame.draw.circle(surface, ink, (cx - 16, cy), 5, 2)


class PropertyTile(Tile):
    """땅. 빈 땅이면 사고, 내 땅이면 통행료가 오르고, 상대 땅이면 통행료를 낸다."""

    BAND_HEIGHT = 24

    def __init__(self, index, name, price, band_color):
        super().__init__(index, name)        # 번호·이름은 부모 것을 그대로 (5강 재사용)
        self.price = price
        self.band_color = band_color
        self.owner = None          # 주인 Player 객체
        self.toll_level = make_toll_level(0)    # 통행료 단계 (0단계 = 기본)
        self._flash_text = None    # 사거나 인수하거나 단계가 오를 때 잠깐 띄울 글자
        self._flash_start = 0

    # ----- 돈 계산 (계산은 여기 한 곳에서만) -----
    @property
    def toll(self):
        return int(self.price * config.TOLL_RATE * self.toll_level.toll_rate)

    @property
    def acquire_price(self):
        return int(self.price * config.ACQUIRE_RATE)    # 11/26 추천안: 땅값 × 2

    # ----- 칸에 도착했을 때 -----
    def on_land(self, player, game):
        if self.owner is None:
            if self.can_buy(player):
                game.ask_buy(self)                     # 빈 땅 → BuyState
            else:
                game.log(f"{player.name}: 돈이 부족해서 {self.name}을(를) 살 수 없어요")
        elif self.owner is player:
            self.raise_toll(game)                      # 내 땅 → 통행료 한 단계 상승
        else:
            toll = self.toll
            player.pay_to(self.owner, toll)            # 돈은 Player의 문으로만 오간다 (캡슐화)
            game.log(f"{player.name} → {self.owner.name}: 통행료 {toll:,}원")
            if not player.is_bankrupt() and self.can_acquire(player):
                game.ask_acquire(self)                 # 인수할지 → AcquireState

    # ----- 사기 -----
    def can_buy(self, player):
        return self.owner is None and player.money >= self.price

    def buy(self, player):
        if not self.can_buy(player):
            return False
        player.pay(self.price)
        self.owner = player
        player.add_tile(self)                  # 패널의 땅 수·총자산에 들어감
        self._start_flash("구매!")
        return True

    # ----- 통행료 상승 (11/22: 자기 땅에 다시 오면 공짜로 한 단계) -----
    def next_toll_level(self):
        """다음 단계 객체. 이미 최대면 None."""
        level = self.toll_level.level + 1
        if level >= len(config.TOLL_STEPS):
            return None
        return make_toll_level(level)

    def raise_toll(self, game):
        """통행료를 한 단계 올린다. 단계 데이터(TollLevel)는 그대로 재사용한다."""
        next_level = self.next_toll_level()
        if next_level is None:
            game.log(f"{self.name}: 통행료 최대 ({self.toll:,}원)")
            return
        self.toll_level = next_level
        self._start_flash(f"{self.toll:,}원!")
        if self.toll_level.can_be_acquired():
            game.log(f"{self.name}: 통행료 {self.toll:,}원으로!")
        else:
            game.log(f"{self.name}: 통행료 최대 {self.toll:,}원! 이제 인수할 수 없어요")

    # ----- 인수 -----
    def can_be_acquired(self):
        """최대 단계면 인수 불가. 판단은 단계 객체에게 맡긴다 (다형성)."""
        return self.owner is not None and self.toll_level.can_be_acquired()

    def can_acquire(self, player):
        return (self.can_be_acquired() and self.owner is not player
                and player.money >= self.acquire_price)

    def acquire(self, player):
        if not self.can_acquire(player):
            return False
        player.pay_to(self.owner, self.acquire_price)
        self.owner.remove_tile(self)           # 원래 주인 목록에서 먼저 빼고
        self.owner = player
        player.add_tile(self)                  # 새 주인 목록에 넣는다 (통행료 단계도 같이 넘어감)
        self._start_flash("인수!")
        return True

    # ----- 그리기 -----
    def draw(self, surface, rect):
        pygame.draw.rect(surface, config.TILE_BG, rect)
        if self.owner:                                  # 주인 색으로 옅게 칠하기
            draw_shade(surface, rect, (*self.owner.color, config.OWNER_TINT_ALPHA))

        band = pygame.Rect(rect.x, rect.y, rect.w, self.BAND_HEIGHT)
        pygame.draw.rect(surface, self.band_color, band)
        draw_text(surface, f"{self.price:,}원", get_font(config.FONT_BODY, 13), config.WHITE, band.center)

        name_size = 17 if len(self.name) <= 4 else 16
        name_y = rect.y + self.BAND_HEIGHT + (rect.h - self.BAND_HEIGHT) // 2
        draw_text(surface, self.name, get_font(config.FONT_BODY, name_size), config.NAVY,
                  (rect.centerx, name_y))
        pygame.draw.rect(surface, config.INK, rect, 2)
        if self.owner:
            pygame.draw.rect(surface, self.owner.color, rect.inflate(-4, -4), 4)   # 주인 색 테두리
            self._draw_flag(surface, rect)
            self.toll_level.draw(surface, rect, self.toll)   # 단계마다 자기 모양대로 (최대는 금색 테두리)
        self._draw_flash(surface, rect)

    def _draw_flag(self, surface, rect):
        """오른쪽 아래 작은 깃발: 누구 땅인지 표시."""
        pole_x, top, bottom = rect.right - 14, rect.bottom - 34, rect.bottom - 9
        pygame.draw.line(surface, config.INK, (pole_x, top), (pole_x, bottom), 3)
        flag = [(pole_x, top), (pole_x - 20, top + 6), (pole_x, top + 12)]
        pygame.draw.polygon(surface, self.owner.color, flag)
        pygame.draw.polygon(surface, config.INK, flag, 2)

    def _start_flash(self, text):
        self._flash_text = text
        self._flash_start = pygame.time.get_ticks()

    def _draw_flash(self, surface, rect):
        """사거나 인수하거나 단계가 오른 직후 잠깐: 칸이 반짝이고 글자가 떠오르며 사라진다."""
        if self._flash_text is None:
            return
        elapsed = pygame.time.get_ticks() - self._flash_start
        if elapsed >= config.FLASH_MS:
            self._flash_text = None
            return
        t = elapsed / config.FLASH_MS                     # 0 → 1
        color = self.owner.color if self.owner else config.YELLOW
        draw_shade(surface, rect, (*color, int(140 * (1 - t))))

        pill = pygame.Rect(0, 0, rect.w - 20, 30)
        pill.center = (rect.centerx, rect.centery - int(18 * t))
        pygame.draw.rect(surface, color, pill, border_radius=15)
        pygame.draw.rect(surface, config.WHITE, pill, 2, border_radius=15)
        draw_text(surface, self._flash_text, get_font(config.FONT_BODY, 18), config.WHITE, pill.center)