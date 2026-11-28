"""
cards.py - 황금열쇠 카드 (A 담당)

구성
  ChanceCard (추상)  : 모든 카드의 공통 틀. title, description, image_file, execute(player, game)
  MoneyCard          : 돈을 내거나 받는 카드 (금액만 다르므로 클래스 1개 + 객체 8개)
  MoveCard           : 정해진 칸으로 이동하는 카드 (어느 칸·월급 여부만 다르므로 클래스 1개 + 객체 2개)
                       11/26: GoToStartCard·GoToIslandCard 두 클래스를 하나로 합침 (재사용)
  CardDeck           : 카드 더미. 섞고, 한 장씩 뽑고, 다 쓰면 다시 섞음
  CardPopup          : 뽑은 카드 그림을 판 가운데에 띄우는 화면 요소

다른 파일과의 약속 (메서드 이름 고정)
  player.pay(amount), player.receive(amount), player.name
  game.log(msg), game.board, game.deck, game.card_popup, game.move_player_to(p, i, salary)
  board.find_tile(tile_class), board.center_rect
  tile.on_land(player, game)

ChanceTile에서 쓰는 법
    card = game.deck.draw()
    game.card_popup.show(card)
    card.execute(player, game)
"""

import os
import random
from abc import ABC, abstractmethod

import pygame

import config
from tiles import IslandTile, StartTile
from ui import draw_shade, get_font


# ---------------------------------------------------------------------------
# 카드 클래스
# ---------------------------------------------------------------------------
class ChanceCard(ABC):
    """황금열쇠 카드의 공통 틀. execute()만 카드마다 다르게 만든다 (커맨드 패턴)."""

    def __init__(self, title, description, image_file):
        self.title = title
        self.description = description
        self.image_file = image_file

    @property
    def image_path(self):
        return os.path.join(config.CARD_IMAGE_DIR, self.image_file)

    @abstractmethod
    def execute(self, player, game):
        """카드 효과를 player에게 적용한다."""

    def log_effect(self, player, game):
        """모든 카드가 같은 모양으로 기록을 남긴다. 자식은 물려받아 부르기만 한다 (5강 재사용)."""
        game.log(f"[황금열쇠] {player.name}: {self.title} - {self.description}")

    def __repr__(self):
        return f"<{type(self).__name__} {self.title}>"


class MoneyCard(ChanceCard):
    """돈을 내거나(amount < 0) 받는(amount > 0) 카드.

    description에 {amount}를 넣어 두면 실제 금액으로 바뀐다.
    """

    def __init__(self, title, amount, description, image_file):
        super().__init__(title, description.format(amount=abs(amount)), image_file)
        self.amount = amount

    def execute(self, player, game):
        if self.amount < 0:
            player.pay(-self.amount)
        else:
            player.receive(self.amount)
        self.log_effect(player, game)


class MoveCard(ChanceCard):
    """정해진 칸으로 바로 이동하는 카드.
    셔틀버스(정문, 월급 받음)와 지각 3회(학사경고, 월급 없음)는 어느 칸인지·월급 여부만 다르다.
    → 데이터만 다르므로 클래스 하나 + 객체 둘 (지침서 "데이터만 다르면 객체")"""

    def __init__(self, title, description, image_file, target_class, salary):
        super().__init__(title, description, image_file)   # 제목·설명·그림은 부모 것 그대로
        self.target_class = target_class   # 갈 칸의 종류 (StartTile, IslandTile …)
        self.salary = salary               # True면 정문을 지날 때 월급

    def execute(self, player, game):
        target = game.board.find_tile(self.target_class)   # 칸 번호를 숫자로 적지 않음
        self.log_effect(player, game)
        game.move_player_to(player, target.index, self.salary)
        target.on_land(player, game)                       # 도착한 칸이 할 일은 칸이 안다 (다형성)


def create_golden_keys():
    """게임에 들어가는 황금열쇠 10장을 만든다."""
    amount = config.CARD_AMOUNTS
    return [
        MoneyCard("등록금 납부", -amount["tuition"],
                  "등록금 {amount}원을 지불하세요.", "01_tuition_payment.png"),
        MoneyCard("F학점", -amount["f_grade"],
                  "멘탈치료비 {amount}원을 지불하세요.", "02_f_grade_mental_care.png"),
        MoneyCard("코스피 급락", -amount["kospi"],
                  "{amount}원을 지불하세요.", "03_kospi_crash.png"),
        MoneyCard("과음의 대가", -amount["hangover"],
                  "{amount}원을 지불하세요.", "04_hangover_consequences.png"),
        MoneyCard("과제폭탄", -amount["assignment"],
                  "밤샘 비용 {amount}원을 지불하세요.", "05_assignment_bomb.png"),
        MoneyCard("과회비 징수", -amount["dept_fee"],
                  "{amount}원을 지불하세요.", "06_department_fee.png"),
        MoveCard("셔틀버스",
                 "정문으로 이동합니다.", "07_shuttle_to_main_gate.png", StartTile, True),
        MoneyCard("왕산체전 우승", amount["sports_win"],
                  "상금 {amount}원을 받습니다.", "08_wangsan_sports_champion.png"),
        MoneyCard("장학금", amount["scholarship"],
                  "장학금 {amount}원을 받습니다.", "09_scholarship.png"),
        MoveCard("지각 3회",
                 "학사경고 칸으로 이동합니다.", "10_late_three_times.png", IslandTile, False),
    ]


# ---------------------------------------------------------------------------
# 카드 더미
# ---------------------------------------------------------------------------
class CardDeck:
    """카드를 섞어 두고 위에서 한 장씩 뽑는다. 다 뽑으면 버린 카드를 다시 섞는다."""

    def __init__(self, cards=None, rng=None):
        self._rng = rng or random.Random()
        self._draw_pile = list(cards) if cards is not None else create_golden_keys()
        self._discard = []
        self.shuffle()

    def shuffle(self):
        self._draw_pile.extend(self._discard)
        self._discard.clear()
        self._rng.shuffle(self._draw_pile)

    def draw(self):
        if not self._draw_pile:
            self.shuffle()
        card = self._draw_pile.pop()
        self._discard.append(card)
        return card

    def __len__(self):
        return len(self._draw_pile)


# ---------------------------------------------------------------------------
# 맵 중앙 팝업
# ---------------------------------------------------------------------------
class CardPopup:
    """뽑은 황금열쇠 그림을 판 가운데(칸으로 둘러싸인 빈 공간)에 띄운다.

    메인 루프에서:
        for event in pygame.event.get():
            if popup.handle_event(event):
                continue            # 팝업이 클릭을 썼으면 다른 곳에 넘기지 않음
        board.draw(screen)
        popup.draw(screen)          # 판을 그린 다음에 그려야 위에 보임

    popup.active가 True인 동안은 다음 턴으로 넘어가지 않게 하면 된다.
    """

    _image_cache = {}

    def __init__(self, board):
        self.board = board
        self.card = None
        self._start_ms = 0
        self._font = None
        self._small_font = None

    # ----- 바깥에서 부르는 메서드 -----
    @property
    def active(self):
        return self.card is not None

    def show(self, card):
        self.card = card
        self._start_ms = pygame.time.get_ticks()

    def close(self):
        self.card = None

    def handle_event(self, event):
        """클릭하거나 키를 누르면 닫는다. 팝업이 이벤트를 썼으면 True."""
        if not self.active:
            return False
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
            # 뜨자마자 실수로 닫히지 않도록 애니메이션이 끝난 뒤부터 받음
            if self._elapsed() >= config.CARD_POPUP_ANIM_MS:
                self.close()
            return True
        return False

    def draw(self, surface):
        if not self.active:
            return
        elapsed = self._elapsed()
        if elapsed >= config.CARD_POPUP_MS:
            self.close()
            return

        area = self.board.center_rect

        # 1) 판 가운데를 어둡게 (ui의 공통 도구 재사용)
        draw_shade(surface, area, config.CARD_SHADE, radius=16)

        # 2) 카드 그림 (작게 시작해서 커지며 나타남)
        t = min(1.0, elapsed / config.CARD_POPUP_ANIM_MS)
        ease = 1 - (1 - t) ** 3
        image = self._fitted_image(area)
        if ease < 1.0:
            w, h = image.get_size()
            scale = 0.6 + 0.4 * ease
            image = pygame.transform.smoothscale(
                image, (max(1, int(w * scale)), max(1, int(h * scale))))
            image.set_alpha(int(255 * ease))
        img_rect = image.get_rect(center=(area.centerx, area.centery - area.height * 0.08))
        surface.blit(image, img_rect)

        if ease < 1.0:
            return

        # 3) 그림 아래에 설명 (금액은 그림에 없어서 글자로 보여 줌)
        self._ensure_fonts(area)
        text = self._font.render(self.card.description, True, config.CARD_TEXT_COLOR)
        box = text.get_rect(midtop=(area.centerx, img_rect.bottom + 12)).inflate(28, 14)
        pygame.draw.rect(surface, config.CARD_TEXT_BG, box, border_radius=10)
        pygame.draw.rect(surface, config.CARD_TEXT_BORDER, box, width=3, border_radius=10)
        surface.blit(text, text.get_rect(center=box.center))

        hint = self._small_font.render("클릭하면 닫힙니다", True, config.CARD_HINT_TEXT)
        surface.blit(hint, hint.get_rect(midtop=(area.centerx, box.bottom + 6)))

    # ----- 내부 도우미 -----
    def _elapsed(self):
        return pygame.time.get_ticks() - self._start_ms

    def _fitted_image(self, area):
        """판 안쪽에 맞게 비율을 유지하며 줄인 그림 (크기별로 한 번만 만든다)."""
        key = (self.card.image_path, area.size)
        if key not in self._image_cache:
            original = self._load_original(self.card)
            max_w, max_h = area.width * 0.85, area.height * 0.62
            w, h = original.get_size()
            scale = min(max_w / w, max_h / h, 1.0)
            size = (max(1, int(w * scale)), max(1, int(h * scale)))
            self._image_cache[key] = pygame.transform.smoothscale(original, size)
        return self._image_cache[key]

    def _load_original(self, card):
        key = (card.image_path, None)
        if key not in self._image_cache:
            try:
                self._image_cache[key] = pygame.image.load(card.image_path).convert_alpha()
            except (pygame.error, FileNotFoundError):
                self._image_cache[key] = self._placeholder(card)
        return self._image_cache[key]

    def _placeholder(self, card):
        """그림 파일이 없을 때 대신 보여 줄 카드."""
        surf = pygame.Surface((512, 342), pygame.SRCALPHA)
        pygame.draw.rect(surf, config.CARD_PLACEHOLDER_BG, surf.get_rect(), border_radius=24)
        pygame.draw.rect(surf, config.CARD_PLACEHOLDER_BORDER, surf.get_rect(), width=8, border_radius=24)
        font = get_font(config.FONT_BODY, 48)
        text = font.render(card.title, True, config.CARD_PLACEHOLDER_TEXT)
        surf.blit(text, text.get_rect(center=surf.get_rect().center))
        return surf

    def _ensure_fonts(self, area):
        if self._font is None:
            size = max(16, int(area.height * 0.055))
            self._font = get_font(config.FONT_BODY, size)
            self._small_font = get_font(config.FONT_BODY, max(12, int(size * 0.6)))

