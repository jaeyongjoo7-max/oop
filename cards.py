"""
cards.py - 황금열쇠 카드 (A 담당)

구성
  ChanceCard (추상)  : 모든 카드의 공통 틀. title, description, image_file, execute(player, game)
  MoneyCard          : 돈을 내거나 받는 카드 (금액만 다르므로 클래스 1개 + 객체 여러 개)
  GoToStartCard      : 정문(출발점)으로 이동하는 카드 (행동이 다르므로 상속)
  CardDeck           : 카드 더미. 섞고, 한 장씩 뽑고, 다 쓰면 다시 섞음
  CardPopup          : 뽑은 카드 그림을 맵 중앙에 띄우는 화면 요소

다른 파일과의 약속 (메서드 이름 고정)
  player.pay(amount), player.receive(amount), player.position, player.name
  game.log(text), game.board
  board.size, board.get_tile(i), board.tile_rect(i)
  tile.on_land(player, game)

ChanceTile에서 쓰는 법
    card = game.card_deck.draw()
    game.card_popup.show(card)
    card.execute(player, game)
"""

import os
import random
from abc import ABC, abstractmethod

import pygame

try:
    import config
except ImportError:  # config.py 없이 이 파일만 따로 시험할 때
    config = None


# ---------------------------------------------------------------------------
# 설정값: config.py에 같은 이름이 있으면 그 값을 쓰고, 없으면 아래 기본값을 씀
# ---------------------------------------------------------------------------
_DEFAULTS = {
    "GOLDEN_KEY_IMAGE_DIR": os.path.join("assets", "images", "cards"),
    "GOLDEN_KEY_AMOUNTS": {
        "tuition": 200,       # 등록금 납부
        "f_grade": 100,       # F학점 멘탈치료비
        "kospi": 150,         # 코스피 급락
        "hangover": 50,       # 과음의 대가
        "assignment": 50,     # 과제폭탄
        "dept_fee": 30,       # 과회비 징수
        "sports_win": 150,    # 왕산체전 우승 상금
        "scholarship": 100,   # 장학금
    },
    "START_INDEX": 0,               # 정문 칸 번호
    "CARD_POPUP_MS": 2500,          # 팝업이 자동으로 닫히기까지 시간 (ms)
    "CARD_POPUP_ANIM_MS": 250,      # 튀어나오는 애니메이션 시간 (ms)
    "FONT_PATH": None,              # 한글 폰트 파일 경로 (없으면 시스템 폰트)
}


def _cfg(name):
    return getattr(config, name, _DEFAULTS[name])


def _amount(key):
    amounts = _cfg("GOLDEN_KEY_AMOUNTS")
    return amounts.get(key, _DEFAULTS["GOLDEN_KEY_AMOUNTS"][key])


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
        return os.path.join(_cfg("GOLDEN_KEY_IMAGE_DIR"), self.image_file)

    @abstractmethod
    def execute(self, player, game):
        """카드 효과를 player에게 적용한다."""

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
        game.log(f"[황금열쇠] {player.name}: {self.title} - {self.description}")


class GoToStartCard(ChanceCard):
    """정문(출발점)으로 바로 이동하는 카드. 도착한 칸의 on_land()도 실행한다."""

    def execute(self, player, game):
        start = _cfg("START_INDEX")
        player.position = start
        game.log(f"[황금열쇠] {player.name}: {self.title} - {self.description}")
        game.board.get_tile(start).on_land(player, game)


def create_golden_keys():
    """게임에 들어가는 황금열쇠 9장을 만든다."""
    return [
        MoneyCard("등록금 납부", -_amount("tuition"),
                  "등록금 {amount}원을 지불하세요.", "01_tuition_payment.png"),
        MoneyCard("F학점", -_amount("f_grade"),
                  "멘탈치료비 {amount}원을 지불하세요.", "02_f_grade_mental_care.png"),
        MoneyCard("코스피 급락", -_amount("kospi"),
                  "{amount}원을 지불하세요.", "03_kospi_crash.png"),
        MoneyCard("과음의 대가", -_amount("hangover"),
                  "{amount}원을 지불하세요.", "04_hangover_consequences.png"),
        MoneyCard("과제폭탄", -_amount("assignment"),
                  "밤샘 비용 {amount}원을 지불하세요.", "05_assignment_bomb.png"),
        MoneyCard("과회비 징수", -_amount("dept_fee"),
                  "{amount}원을 지불하세요.", "06_department_fee.png"),
        GoToStartCard("셔틀버스",
                      "정문으로 이동합니다.", "07_shuttle_to_main_gate.png"),
        MoneyCard("왕산체전 우승", _amount("sports_win"),
                  "상금 {amount}원을 받습니다.", "08_wangsan_sports_champion.png"),
        MoneyCard("장학금", _amount("scholarship"),
                  "장학금 {amount}원을 받습니다.", "09_scholarship.png"),
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
            if self._elapsed() >= _cfg("CARD_POPUP_ANIM_MS"):
                self.close()
            return True
        return False

    def draw(self, surface):
        if not self.active:
            return
        elapsed = self._elapsed()
        if elapsed >= _cfg("CARD_POPUP_MS"):
            self.close()
            return

        area = self._center_area()

        # 1) 판 가운데를 어둡게
        shade = pygame.Surface(area.size, pygame.SRCALPHA)
        pygame.draw.rect(shade, (0, 0, 0, 140), shade.get_rect(), border_radius=16)
        surface.blit(shade, area.topleft)

        # 2) 카드 그림 (작게 시작해서 커지며 나타남)
        t = min(1.0, elapsed / max(1, _cfg("CARD_POPUP_ANIM_MS")))
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
        text = self._font.render(self.card.description, True, (255, 255, 255))
        box = text.get_rect(midtop=(area.centerx, img_rect.bottom + 12)).inflate(28, 14)
        pygame.draw.rect(surface, (40, 30, 10), box, border_radius=10)
        pygame.draw.rect(surface, (240, 196, 60), box, width=3, border_radius=10)
        surface.blit(text, text.get_rect(center=box.center))

        hint = self._small_font.render("클릭하면 닫힙니다", True, (220, 220, 220))
        surface.blit(hint, hint.get_rect(midtop=(area.centerx, box.bottom + 6)))

    # ----- 내부 도우미 -----
    def _elapsed(self):
        return pygame.time.get_ticks() - self._start_ms

    def _center_area(self):
        """칸들로 둘러싸인 판 안쪽 사각형."""
        rects = [pygame.Rect(self.board.tile_rect(i)) for i in range(self.board.size)]
        outer = rects[0].unionall(rects[1:])
        tile_w = min(r.width for r in rects)
        tile_h = min(r.height for r in rects)
        inner = outer.inflate(-2 * tile_w, -2 * tile_h)
        return inner if inner.width > 0 and inner.height > 0 else outer

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
        pygame.draw.rect(surf, (250, 210, 80), surf.get_rect(), border_radius=24)
        pygame.draw.rect(surf, (150, 100, 20), surf.get_rect(), width=8, border_radius=24)
        font = _make_font(48)
        text = font.render(card.title, True, (60, 40, 10))
        surf.blit(text, text.get_rect(center=surf.get_rect().center))
        return surf

    def _ensure_fonts(self, area):
        if self._font is None:
            size = max(16, int(area.height * 0.055))
            self._font = _make_font(size)
            self._small_font = _make_font(max(12, int(size * 0.6)))


def _make_font(size):
    """한글이 나오는 폰트. config.FONT_PATH가 있으면 그것을 쓴다."""
    if not pygame.font.get_init():
        pygame.font.init()
    path = _cfg("FONT_PATH")
    if path and os.path.exists(path):
        return pygame.font.Font(path, size)
    return pygame.font.SysFont("malgungothic,applegothic,nanumgothic,notosanscjkkr", size, bold=True)
