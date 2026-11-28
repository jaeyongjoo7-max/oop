import os
import pygame
import config
from roll_strategies import RandomRoll, GaugeRoll

# ================================================================
# 공통 도구: 글자 그리기, 반투명 막, 말 모양 그리기
#   판(A)·화면(B)·상태(C)가 모두 이 모듈의 도구를 가져다 쓴다 (2강 모듈, 재사용).
#   예전에는 tiles.py와 states.py에도 글자 도구가 따로 있었다 → 하나로 합침 (11/26)
# ================================================================

_fonts = {}         # (폰트 파일, 크기) → 폰트 객체. 크기마다 한 번만 만든다 (지침서 6쪽)
_text_images = {}   # (글자, 폰트, 색) → 글자 그림. 같은 글자는 한 번만 만든다 (A의 tiles.py에서 옮김)


def get_font(path, size):
    key = (path, size)
    if key not in _fonts:
        if os.path.exists(path):
            _fonts[key] = pygame.font.Font(path, size)
        else:   # 폰트 파일이 아직 없으면 컴퓨터에 있는 한글 폰트로 대신 (9강)
            _fonts[key] = pygame.font.SysFont(config.FONT_FALLBACK, size, bold=True)
    return _fonts[key]


def draw_text(surface, text, font, color, pos, align="center"):
    """align이 "center"면 pos가 글자 가운데, "left"면 글자 왼쪽 가운데."""
    key = (text, font, color)
    if key not in _text_images:
        _text_images[key] = font.render(text, True, color)
    image = _text_images[key]
    rect = image.get_rect()
    pos = (int(pos[0]), int(pos[1]))     # 칸 위치 계산에서 소수가 와도 괜찮게
    if align == "center":
        rect.center = pos
    else:
        rect.midleft = pos
    surface.blit(image, rect)


def draw_shade(surface, rect, rgba, radius=0):
    """rect 위에 반투명 색을 덮는다. rgba = (R, G, B, 투명도 0~255).
    팝업 뒤 어두운 막, 칸 주인 색, 반짝임, 카드 뒤 막이 모두 이걸 쓴다.
    (강의 범위 밖: pygame.SRCALPHA — 투명도가 있는 그림판을 만들어 뒤가 비쳐 보이게 한다)"""
    shade = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shade, rgba, shade.get_rect(), border_radius=radius)
    surface.blit(shade, rect.topleft)


_images = {}       # 파일 경로 → 불러온 그림. 같은 그림은 한 번만 불러온다 (지침서에 없는 새 이름)


def load_image(path):
    """그림 파일을 불러온다 (8강 pygame.image.load). 파일이 없으면 None → 부르는 쪽이 그냥 건너뛴다."""
    if path not in _images:
        try:
            _images[path] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            _images[path] = None
    return _images[path]


def draw_background(surface, shade=None):
    """네이비 캠퍼스 배경 그림. 그림이 없으면 네이비로 칠한다. shade를 주면 그 위를 어둡게 덮는다.
    메인·게임 준비(states)와 플레이 화면(Game)이 같이 쓴다."""
    image = load_image(config.BG_IMAGE)
    if image:
        surface.blit(image, (0, 0))
    else:
        surface.fill(config.NAVY)
    if shade:
        draw_shade(surface, surface.get_rect(), shade)


def draw_panel(surface, rect, radius=22, border=2):
    """아이보리 패널 + 진한 테두리 + 바깥 가는 골드 선. 게임 준비·도움말·종료 확인·팝업이 같이 쓴다."""
    pygame.draw.rect(surface, config.PANEL_RIM, rect.inflate(2, 2), width=1, border_radius=radius + 1)
    pygame.draw.rect(surface, config.IVORY, rect, border_radius=radius)
    pygame.draw.rect(surface, config.INK, rect, width=border, border_radius=radius)


def draw_divider(surface, left, right, y):
    """패널 안 가는 구분선"""
    pygame.draw.line(surface, config.DIVIDER, (left, y), (right, y), 1)


def wrap_text(text, font, max_width, max_lines):
    """글자를 max_width에 맞춰 여러 줄로 나눈다 (한 글자씩 재서 넘치면 다음 줄). 마지막 줄은 "…"로 자른다."""
    lines, line = [], ""
    for ch in text:
        if font.size(line + ch)[0] > max_width and line:
            lines.append(line)
            line = ch.lstrip()
        else:
            line += ch
    lines.append(line)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = fit_text(lines[-1] + "…", font, max_width)
    return lines


def fit_text(text, font, max_width):
    """글자가 너무 길면 뒤를 잘라 "…"을 붙인다."""
    if font.size(text)[0] <= max_width:
        return text
    while len(text) > 1 and font.size(text + "…")[0] > max_width:
        text = text[:-1]
    return text + "…"


def lighten(color):
    """색을 흰색 쪽으로 밝게 (패널 칸 배경용)."""
    r, g, b = color
    rate = 0.88
    return (int(r + (255 - r) * rate), int(g + (255 - g) * rate), int(b + (255 - b) * rate))


def draw_pawn(surface, color, bottom_center, height):
    """졸(폰) 모양 말. 판 위의 말도 나중에 이걸로 그린다."""
    x, y = bottom_center
    half = height * 0.3
    body = [(x - half, y), (x + half, y),
            (x + half * 0.4, y - height * 0.5), (x - half * 0.4, y - height * 0.5)]
    head = (x, y - height * 0.68)
    head_radius = height * 0.22
    pygame.draw.polygon(surface, color, body)
    pygame.draw.polygon(surface, config.INK, body, 2)
    pygame.draw.circle(surface, color, head, head_radius)
    pygame.draw.circle(surface, config.INK, head, head_radius, 2)
    shine = (head[0] - head_radius * 0.35, head[1] - head_radius * 0.35)   # 머리 위 반짝임
    pygame.draw.circle(surface, lighten(color), shine, max(1, head_radius * 0.3))


# ================================================================
# Button (9강 Button: normal / hover / active)
# ================================================================

class Button:
    def __init__(self, center, size, text, color=config.YELLOW, font_size=None, radius=None):
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.radius = radius or size[1] // 2      # 모서리 둥글기 (안 주면 알약 모양)
        self.rect.center = center
        self.text = text
        self.color = color
        self.text_color = config.INK             # 글자 색 (자식 클래스가 바꿀 수 있게 변수로)
        self.hover_color = config.BUTTON_HOVER   # 마우스를 올렸을 때 색
        self.shine_color = config.BUTTON_SHINE   # 위쪽 반사 줄 색
        self.font_size = font_size or size[1] * 2 // 5
        self.state = "normal"       # normal / hover / active

    def reset(self):
        """화면이 바뀔 때 hover·active로 남지 않게 처음 상태로"""
        self.state = "normal"

    def handle_event(self, event):
        """버튼 위에서 눌렀다가 버튼 위에서 떼면 True (클릭 완료)."""
        if event.type == pygame.MOUSEMOTION and self.state != "active":
            if self.rect.collidepoint(event.pos):
                self.state = "hover"
            else:
                self.state = "normal"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos):
            self.state = "active"
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.state == "active":
            inside = self.rect.collidepoint(event.pos)
            if inside:
                self.state = "hover"
            else:
                self.state = "normal"
            return inside
        return False

    def draw(self, surface):
        radius = self.radius
        shadow = config.BUTTON_SHADOW
        rect = self.rect
        if self.state == "active":                  # 누르면 그림자 쪽으로 내려감
            rect = self.rect.move(0, shadow - 2)
        color = self.color
        if self.state == "hover":
            color = self.hover_color

        pygame.draw.rect(surface, config.INK, self.rect.move(0, shadow), border_radius=radius)
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        shine = pygame.Rect(rect.x + radius, rect.y + 5, rect.width - radius * 2, 4)    # 위쪽 반사 줄
        pygame.draw.rect(surface, self.shine_color, shine, border_radius=2)
        pygame.draw.rect(surface, config.INK, rect, width=3, border_radius=radius)
        font = get_font(config.FONT_BUTTON, self.font_size)
        draw_text(surface, self.text, font, self.text_color, (rect.centerx, rect.centery + 1))


class LightButton(Button):
    """아이보리 버튼 (게임 방법·게임 종료·메인으로·취소). 부모 Button을 물려받고 색만 바꾼다 (5강)
    (지침서에 없는 새 이름)"""
    def __init__(self, center, size, text, font_size=None, color=config.LIGHT_BUTTON, radius=None):
        super().__init__(center, size, text, color, font_size, radius)
        self.hover_color = config.LIGHT_HOVER
        self.shine_color = config.LIGHT_SHINE


# ================================================================
# RollGauge: 굴리기 버튼 + 게이지 막대
#   짧게 클릭 → RandomRoll,  꾹 눌렀다 떼기 → GaugeRoll(구간)
# ================================================================

class RollGauge:
    def __init__(self, gauge_center, button_center):
        self.button = Button(button_center, config.ROLL_BUTTON_SIZE, "꾹 눌러서 굴리기", font_size=27)
        self.rect = pygame.Rect(0, 0, config.GAUGE_WIDTH, config.GAUGE_HEIGHT)
        self.rect.center = gauge_center
        self.reset()

    def reset(self):
        """새 판을 시작할 때 누르던 상태를 지운다"""
        self._holding = False       # 지금 누르고 있는지
        self._held_time = 0         # 누른 시간 (ms)
        self._marker = 0.0          # 빨간 표시 위치: 0.0(왼쪽 끝) ~ 1.0(오른쪽 끝)
        self._direction = 1         # 1이면 오른쪽으로, -1이면 왼쪽으로
        self.button.reset()

    @property
    def zone(self):
        """빨간 표시가 있는 구간 번호: 0 작은 수, 1 중간, 2 큰 수"""
        return min(int(self._marker * 3), 2)

    def _is_long_press(self):
        return self._held_time >= config.LONG_PRESS_TIME

    def handle_event(self, event):
        """굴리기가 정해지면 RollStrategy 객체를, 아니면 None을 돌려준다."""
        clicked = self.button.handle_event(event)
        if self.button.state == "active" and not self._holding:      # 막 누르기 시작
            self._holding = True
            self._held_time = 0
            self._marker = 0.0
            self._direction = 1
        if event.type == pygame.MOUSEBUTTONUP and self._holding:      # 뗐을 때
            self._holding = False
            if clicked:
                if self._is_long_press():
                    return GaugeRoll(self.zone)
                return RandomRoll()
        return None

    def update(self, dt):
        if not self._holding:
            return
        self._held_time += dt
        if not self._is_long_press():           # 짧은 클릭이면 게이지가 안 움직임
            return
        self._marker += self._direction * dt / config.GAUGE_SWEEP_TIME
        if self._marker >= 1:                   # 오른쪽 끝 → 방향 바꾸기
            self._marker = 1
            self._direction = -1
        elif self._marker <= 0:                 # 왼쪽 끝 → 방향 바꾸기
            self._marker = 0
            self._direction = 1

    def draw(self, surface):
        r = self.rect
        pygame.draw.rect(surface, config.INK, r, border_radius=r.height // 2)        # 바깥 틀
        inner = r.inflate(-8, -8)
        gap = 4
        width = (inner.width - gap * 2) / 3
        font = get_font(config.FONT_BODY, 13)
        for i in range(3):
            x = inner.x + i * (width + gap)
            zone_rect = pygame.Rect(round(x), inner.y, round(width), inner.height)
            pygame.draw.rect(surface, config.GAUGE_COLORS[i], zone_rect, border_radius=inner.height // 2)
            if self._is_long_press() and self._holding and i == self.zone:      # 지금 고른 구간 테두리
                pygame.draw.rect(surface, config.P1_RED, zone_rect, width=2, border_radius=inner.height // 2)
            low, high = config.GAUGE_ZONES[i]
            draw_text(surface, f"{config.GAUGE_NAMES[i]} {low}–{high}", font, config.INK, zone_rect.center)

        if self._is_long_press():                            # 빨간 표시
            x = r.x + 4 + int(self._marker * (r.width - 8))
            marker = pygame.Rect(x - 3, r.y - 7, 6, r.height + 14)
            pygame.draw.rect(surface, config.WHITE, marker.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surface, config.P1_RED, marker, border_radius=3)
            if self._holding:                                # "확률 UP!" 말풍선
                tag = pygame.Rect(0, 0, 72, 22)
                tag.midbottom = (x, r.y - 9)
                pygame.draw.rect(surface, config.P1_RED, tag, border_radius=11)
                pygame.draw.rect(surface, config.INK, tag, width=2, border_radius=11)
                draw_text(surface, "확률 UP!", get_font(config.FONT_BODY, 12), config.WHITE, tag.center)

        self.button.draw(surface)


# ================================================================
# MessageLog: 오른쪽 아래 '진행 기록' 상자. 최신 기록은 흰 글자로 아래에
# ================================================================

class MessageLog:
    def __init__(self, rect):
        x, y, w, h = rect
        self.bottom = y + h          # 상자 아래쪽은 고정, 기록이 늘면 위로 커진다
        self.left = x
        self.width = w
        self.min_height = h
        self.messages = []

    def add(self, msg):
        self.messages.append(msg)
        if len(self.messages) > config.LOG_COUNT:       # 오래된 것부터 버림
            self.messages.pop(0)

    def draw(self, surface):
        label_font = get_font(config.FONT_BODY, 11)
        new_font = get_font(config.FONT_BODY, 14)
        old_font = get_font(config.FONT_BODY, 12)
        text_w = self.width - 28
        rows = []                                        # (글자, 폰트, 색, 줄 높이)
        for msg in self.messages[:-1]:                   # 지난 기록: 한 줄, 흐린 글자
            rows.append((fit_text(msg, old_font, text_w), old_font, config.LOG_OLD_TEXT, 18))
        if self.messages:                                # 최신 기록: 두 줄까지, 흰 글자
            for line in wrap_text(self.messages[-1], new_font, text_w, 2):
                rows.append((line, new_font, config.WHITE, 21))

        height = max(self.min_height, 30 + sum(row[3] for row in rows) + 8)
        rect = pygame.Rect(self.left, self.bottom - height, self.width, height)
        pygame.draw.rect(surface, config.LOG_BG, rect, border_radius=14)
        pygame.draw.rect(surface, config.LOG_BORDER, rect, width=1, border_radius=14)
        draw_text(surface, "진행 기록", label_font, config.LOG_LABEL, (rect.x + 14, rect.y + 15), align="left")
        y = rect.y + 28
        for text, font, color, line_h in rows:
            draw_text(surface, text, font, color, (rect.x + 14, y + line_h // 2), align="left")
            y += line_h


# ================================================================
# PlayerInfo: 1P·2P 카드 (보여주기만, 게임 규칙은 모름)
# ================================================================

class PlayerInfo:
    def __init__(self, player, topleft, tag):
        self.player = player
        self.tag = tag          # "1P" / "2P"
        self.rect = pygame.Rect(topleft[0], topleft[1], config.PANEL_WIDTH, config.PANEL_HEIGHT)
        self.is_turn = False    # C가 차례마다 정해 줌 → "내 차례!" 표시와 골드 테두리
        self.rank = 1           # C가 정해 줌 → "· 1위"

    def _count_raised(self):
        """통행료가 한 번이라도 오른 땅 수."""
        count = 0
        for tile in self.player.tiles:
            if tile.toll_level.level > 0:
                count += 1
        return count

    def draw(self, surface):
        p = self.player
        r = self.rect

        # 카드 바탕: 그림자 → 아이보리 → 테두리 (차례면 골드, 아니면 회색)
        pygame.draw.rect(surface, config.INK, r.move(0, 6), border_radius=16)
        pygame.draw.rect(surface, config.IVORY, r, border_radius=16)
        if self.is_turn:
            pygame.draw.rect(surface, config.GOLD, r, width=3, border_radius=16)
        else:
            pygame.draw.rect(surface, config.CARD_IDLE_BORDER, r, width=2, border_radius=16)

        # 머리: 1P/2P 표 + 이름
        chip = pygame.Rect(r.x + 12, r.y + 10, 34, 30)
        pygame.draw.rect(surface, p.color, chip, border_radius=8)
        draw_text(surface, self.tag, get_font(config.FONT_BODY, 13), config.WHITE, chip.center)
        name_font = get_font(config.FONT_BODY, 17)
        draw_text(surface, fit_text(p.name, name_font, r.width - 70), name_font, config.INK,
                  (chip.right + 10, chip.centery), align="left")
        draw_divider(surface, r.x + 12, r.right - 12, r.y + 49)

        # 돈: 동전 + 1,500원
        coin = (r.x + 24, r.y + 73)
        pygame.draw.circle(surface, config.COIN, coin, 9)
        pygame.draw.circle(surface, config.COIN_RIM, coin, 9, 2)
        pygame.draw.circle(surface, config.COIN_RIM, coin, 4, 1)
        draw_text(surface, f"{p.money:,}원", get_font(config.FONT_BODY, 22), config.INK,
                  (r.x + 40, coin[1]), align="left")

        # 땅 수, 통행료 오른 땅 수
        font = get_font(config.FONT_BODY, 12)
        box_w = (r.width - 30) // 2
        land = pygame.Rect(r.x + 12, r.y + 93, box_w, 24)
        raised = pygame.Rect(land.right + 6, land.y, box_w, 24)
        for box in (land, raised):
            pygame.draw.rect(surface, config.PILL_BG, box, border_radius=7)
        draw_text(surface, f"땅 {len(p.tiles)}", font, config.INK, land.center)
        draw_text(surface, f"오른 땅 {self._count_raised()}", font, config.INK, raised.center)

        # 총자산 · 순위
        draw_text(surface, f"총자산 {p.total_assets():,}원 · {self.rank}위",
                  get_font(config.FONT_BODY, 11), config.SUB_TEXT, (r.centerx, r.y + 134))

        if self.is_turn:                                         # "내 차례!" 표
            tag = pygame.Rect(0, 0, 92, 24)
            tag.midbottom = (r.centerx, r.y + 1)
            pygame.draw.rect(surface, config.GOLD, tag, border_top_left_radius=10,
                             border_top_right_radius=10, border_bottom_left_radius=4,
                             border_bottom_right_radius=4)
            draw_text(surface, "내 차례!", get_font(config.FONT_BODY, 13), config.INK, tag.center)


# ================================================================
# 혼자 확인용: B 부품만 모아서 띄워 보기
#   - 짧게 클릭 = 일반 굴리기, 꾹 눌렀다 떼기 = 게이지 굴리기
#   - 주사위가 멈추면 (합 × 10)원을 받고 차례가 넘어감 (테스트용 규칙)
# ================================================================

if __name__ == "__main__":
    from player import HumanPlayer
    from dice import DiceSet

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    pygame.display.set_caption("B 부품 테스트")
    clock = pygame.time.Clock()

    players = [HumanPlayer("플레이어 1", config.P1_RED), HumanPlayer("플레이어 2", config.P2_BLUE)]
    infos = [PlayerInfo(players[0], config.P1_PANEL_POS, "1P"),
             PlayerInfo(players[1], config.P2_PANEL_POS, "2P")]
    dice = DiceSet()
    gauge = RollGauge(config.GAUGE_CENTER, config.ROLL_BUTTON_CENTER)
    log = MessageLog(config.LOG_RECT)
    turn = 0
    was_rolling = False
    log.add("게임 시작!")
    log.add("플레이어 1 차례")
    running = True

    while running:
        dt = clock.tick(config.FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif not dice.is_rolling:
                strategy = gauge.handle_event(event)
                if strategy:
                    dice.roll(strategy)

        gauge.update(dt)
        dice.update(dt)
        if was_rolling and not dice.is_rolling:          # 주사위가 방금 멈춤
            p = players[turn]
            p.receive(dice.total * 10)
            double = " 더블!" if dice.is_double else ""
            log.add(f"{p.name}: {dice.total} 나옴, +{dice.total * 10}원{double}")
            turn = 1 - turn
        was_rolling = dice.is_rolling

        for i in range(2):
            infos[i].is_turn = (i == turn)
            infos[i].rank = 1 if players[i].money >= players[1 - i].money else 2

        screen.fill(config.NAVY)
        dice.draw(screen, config.DICE_CENTER)
        gauge.draw(screen)
        for info in infos:
            info.draw(screen)
        log.draw(screen)
        pygame.display.flip()

    pygame.quit()
