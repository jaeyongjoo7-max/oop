"""판 위의 칸들.

칸 종류마다 on_land()를 다르게 구현한다 (다형성).
Game은 tile.on_land(player, game) 한 줄만 부르면, 칸 종류에 맞는 일이 일어난다.
새로운 칸이 필요하면 if문을 고치지 않고 Tile을 상속한 클래스를 하나 더 만든다 (OCP).
"""
import os
from abc import ABC, abstractmethod

import pygame

import config
from buildings import make_building

# ---------------------------------------------------------------------------
# 글자 그리기 도구: 폰트와 글자 그림은 한 번만 만들고 다시 쓴다 (매 프레임 만들면 느려짐)
# ---------------------------------------------------------------------------
_fonts = {}
_text_images = {}


def get_font(size, path=None):
    path = path or config.FONT_BODY
    key = (path, size)
    if key not in _fonts:
        if os.path.exists(path):
            _fonts[key] = pygame.font.Font(path, size)
        else:  # 폰트 파일이 아직 없으면 컴퓨터에 있는 한글 폰트로 대신
            _fonts[key] = pygame.font.SysFont(config.FONT_FALLBACK, size, bold=True)
    return _fonts[key]


def draw_text(surface, text, size, color, center, path=None):
    key = (text, size, color, path)
    if key not in _text_images:
        _text_images[key] = get_font(size, path).render(text, True, color)
    image = _text_images[key]
    surface.blit(image, image.get_rect(center=(int(center[0]), int(center[1]))))


# ---------------------------------------------------------------------------
# 칸 클래스들
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
        draw_text(surface, self.name, 17, config.NAVY, rect.center)
        pygame.draw.rect(surface, config.INK, rect, 2)

    def _draw_special(self, surface, rect, bg, fg, title, sub, title_size):
        """정문·학사경고처럼 테두리 상자가 있는 특수 칸 모양."""
        pygame.draw.rect(surface, bg, rect)
        pygame.draw.rect(surface, fg, rect.inflate(-10, -10), 3, border_radius=6)
        draw_text(surface, title, title_size, fg, (rect.centerx, rect.y + rect.h * 0.38))
        draw_text(surface, sub, 14, fg, (rect.centerx, rect.y + rect.h * 0.68))
        pygame.draw.rect(surface, config.INK, rect, 2)


class StartTile(Tile):
    """정문. 지나가거나 도착할 때 받는 월급은 말을 옮기는 쪽(MovingState, move_player_to)이 준다."""

    def on_land(self, player, game):
        game.log(f"{player.name}: 정문 도착")

    def draw(self, surface, rect):
        self._draw_special(surface, rect, config.START_BG, config.START_TEXT, self.name, "← 출발", 24)


class IslandTile(Tile):
    """학사경고. 정해진 턴 동안 쉰다."""

    def on_land(self, player, game):
        player.rest_turns = config.ISLAND_REST_TURNS
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
        draw_text(surface, self.name, 16, config.CHANCE_TEXT, (rect.centerx, rect.y + rect.h * 0.77))
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
    """땅. 빈 땅이면 사고, 내 땅이면 짓고, 상대 땅이면 통행료를 낸다."""

    BAND_HEIGHT = 24

    def __init__(self, index, name, price, band_color):
        super().__init__(index, name)
        self.price = price
        self.band_color = band_color
        self.owner = None          # 주인 Player 객체
        self.building = None       # 땅 하나에 건물 하나
        self._flash_text = None    # 사거나 짓거나 인수했을 때 잠깐 띄울 글자
        self._flash_start = 0

    # ----- 돈 계산 (계산은 여기 한 곳에서만) -----
    @property
    def toll(self):
        rate = self.building.toll_rate if self.building else 1
        return int(self.price * config.TOLL_RATE * rate)

    @property
    def acquire_price(self):
        building_cost = self.building.cost if self.building else 0
        return int((self.price + building_cost) * config.ACQUIRE_RATE)

    # ----- 칸에 도착했을 때 -----
    def on_land(self, player, game):
        if self.owner is None:
            if self.can_buy(player):
                game.ask_buy(self)                     # 빈 땅 → BuyState
            else:
                game.log(f"{player.name}: 돈이 부족해서 {self.name}을(를) 살 수 없어요")
        elif self.owner is player:
            building = self.next_building()
            if building is None:
                game.log(f"{self.name}: 이미 랜드마크예요")
            elif self.can_build(building):
                game.ask_build(self)                   # 내 땅 → BuildState
            else:
                game.log(f"{player.name}: 돈이 부족해서 {building.name}을(를) 못 지어요")
        else:
            toll = self.toll
            player.pay(toll)
            self.owner.receive(toll)
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

    # ----- 짓기 -----
    def next_building(self):
        """다음 단계 건물 객체 (빈 땅이면 별장). 이미 랜드마크면 None.
        BuildState는 tile.upgrade(tile.next_building()), AI는 tile.next_building().cost로 판단."""
        level = self.building.level + 1 if self.building else 1
        if level > len(config.BUILDING_STEPS):
            return None
        return make_building(level, self.price)

    def can_build(self, building):
        current = self.building.level if self.building else 0
        return (self.owner is not None and building.level > current
                and self.owner.money >= building.cost)

    def upgrade(self, building):
        if not self.can_build(building):
            return False
        self.owner.pay(building.cost)
        self.building = building
        self._start_flash(f"{building.name}!")
        return True

    # ----- 인수 -----
    def can_be_acquired(self):
        """랜드마크가 있으면 인수 불가. 판단은 건물 객체에게 맡긴다 (다형성)."""
        return self.owner is not None and (self.building is None or self.building.can_be_acquired())

    def can_acquire(self, player):
        return (self.can_be_acquired() and self.owner is not player
                and player.money >= self.acquire_price)

    def acquire(self, player):
        if not self.can_acquire(player):
            return False
        price = self.acquire_price
        player.pay(price)
        self.owner.receive(price)
        self.owner.remove_tile(self)           # 원래 주인 목록에서 먼저 빼고
        self.owner = player
        player.add_tile(self)                  # 새 주인 목록에 넣는다 (건물도 같이 넘어감)
        self._start_flash("인수!")
        return True

    # ----- 그리기 -----
    def draw(self, surface, rect):
        pygame.draw.rect(surface, config.TILE_BG, rect)
        if self.owner:                                  # 주인 색으로 옅게 칠하기
            tint = pygame.Surface(rect.size, pygame.SRCALPHA)
            tint.fill((*self.owner.color, config.OWNER_TINT_ALPHA))
            surface.blit(tint, rect.topleft)

        band = pygame.Rect(rect.x, rect.y, rect.w, self.BAND_HEIGHT)
        pygame.draw.rect(surface, self.band_color, band)
        draw_text(surface, f"{self.price:,}원", 13, config.WHITE, band.center)

        name_size = 17 if len(self.name) <= 4 else 16
        name_y = rect.y + self.BAND_HEIGHT + (rect.h - self.BAND_HEIGHT) // 2
        draw_text(surface, self.name, name_size, config.NAVY, (rect.centerx, name_y))
        pygame.draw.rect(surface, config.INK, rect, 2)
        if self.owner:
            pygame.draw.rect(surface, self.owner.color, rect.inflate(-4, -4), 4)   # 주인 색 테두리
            self._draw_flag(surface, rect)
        if self.building:
            self.building.draw(surface, rect)          # 건물마다 자기 모양대로 (랜드마크는 금색 테두리)
            draw_text(surface, self.building.name, 12, config.NAVY, (rect.x + 52, rect.bottom - 13))
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
        """사거나 짓거나 인수한 직후 잠깐: 칸이 반짝이고 글자가 떠오르며 사라진다."""
        if self._flash_text is None:
            return
        elapsed = pygame.time.get_ticks() - self._flash_start
        if elapsed >= config.FLASH_MS:
            self._flash_text = None
            return
        t = elapsed / config.FLASH_MS                     # 0 → 1
        color = self.owner.color if self.owner else config.YELLOW

        glow = pygame.Surface(rect.size, pygame.SRCALPHA)
        glow.fill((*color, int(140 * (1 - t))))
        surface.blit(glow, rect.topleft)

        pill = pygame.Rect(0, 0, rect.w - 20, 30)
        pill.center = (rect.centerx, rect.centery - int(18 * t))
        pygame.draw.rect(surface, color, pill, border_radius=15)
        pygame.draw.rect(surface, config.WHITE, pill, 2, border_radius=15)
        draw_text(surface, self._flash_text, 18, config.WHITE, pill.center)
