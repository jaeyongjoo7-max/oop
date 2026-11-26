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
    rate = config.TINT_RATE
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


# ================================================================
# Button (9강 Button: normal / hover / active)
# ================================================================

class Button:
    def __init__(self, center, size, text, color=config.YELLOW):
        self.rect = pygame.Rect(0, 0, size[0], size[1])
        self.rect.center = center
        self.text = text
        self.color = color
        self.state = "normal"       # normal / hover / active

    def handle_event(self, event):
        """버튼 위에서 눌렀다가 버튼 위에서 떼면 True (클릭 완료)."""
        if event.type == pygame.MOUSEMOTION and self.state != "active":
            if self.rect.collidepoint(event.pos):
                self.state = "hover"
            else:
                self.state = "normal"
        elif event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            self.state = "active"
        elif event.type == pygame.MOUSEBUTTONUP and self.state == "active":
            inside = self.rect.collidepoint(event.pos)
            if inside:
                self.state = "hover"
            else:
                self.state = "normal"
            return inside
        return False

    def draw(self, surface):
        radius = self.rect.height // 2
        shadow = config.BUTTON_SHADOW
        rect = self.rect
        if self.state == "active":                  # 누르면 그림자 쪽으로 내려감
            rect = self.rect.move(0, shadow - 2)
        color = self.color
        if self.state == "hover":
            color = config.BUTTON_HOVER

        pygame.draw.rect(surface, config.INK, self.rect.move(0, shadow), border_radius=radius)
        pygame.draw.rect(surface, color, rect, border_radius=radius)
        shine = pygame.Rect(rect.x + 18, rect.y + 6, rect.width - 36, 12)    # 위쪽 반사 줄
        pygame.draw.rect(surface, config.BUTTON_SHINE, shine, border_radius=6)
        pygame.draw.rect(surface, config.INK, rect, width=3, border_radius=radius)
        font = get_font(config.FONT_BUTTON, rect.height * 2 // 5)
        draw_text(surface, self.text, font, config.NAVY, rect.center)


# ================================================================
# RollGauge: 굴리기 버튼 + 게이지 막대
#   짧게 클릭 → RandomRoll,  꾹 눌렀다 떼기 → GaugeRoll(구간)
# ================================================================

class RollGauge:
    def __init__(self, gauge_center, button_center):
        self.button = Button(button_center, config.ROLL_BUTTON_SIZE, "꾹 눌러서 굴리기")
        self.rect = pygame.Rect(0, 0, config.GAUGE_WIDTH, config.GAUGE_HEIGHT)
        self.rect.center = gauge_center
        self._holding = False       # 지금 누르고 있는지
        self._held_time = 0         # 누른 시간 (ms)
        self._marker = 0.0          # 빨간 표시 위치: 0.0(왼쪽 끝) ~ 1.0(오른쪽 끝)
        self._direction = 1         # 1이면 오른쪽으로, -1이면 왼쪽으로

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
        radius = r.height // 2
        width = r.width // 3
        font = get_font(config.FONT_BODY, 11)

        pygame.draw.rect(surface, config.INK, r.move(0, 4), border_radius=radius)    # 그림자
        for i in range(3):
            x = r.x + width * i
            w = width if i < 2 else r.right - x            # 마지막 칸은 남은 폭 전부
            zone_rect = pygame.Rect(x, r.y, w, r.height)
            color = config.GAUGE_COLORS[i]
            if i == 0:
                pygame.draw.rect(surface, color, zone_rect,
                                 border_top_left_radius=radius, border_bottom_left_radius=radius)
            elif i == 2:
                pygame.draw.rect(surface, color, zone_rect,
                                 border_top_right_radius=radius, border_bottom_right_radius=radius)
            else:
                pygame.draw.rect(surface, color, zone_rect)
            low, high = config.GAUGE_ZONES[i]
            label = f"{config.GAUGE_NAMES[i]} {low}~{high}"
            draw_text(surface, label, font, config.INK, zone_rect.center)
        for i in range(1, 3):                                # 칸 사이 선
            x = r.x + width * i
            pygame.draw.line(surface, config.INK, (x, r.y), (x, r.bottom - 1), 2)
        pygame.draw.rect(surface, config.INK, r, width=3, border_radius=radius)

        if self._is_long_press():                            # 빨간 표시
            x = r.x + int(self._marker * r.width)
            marker = pygame.Rect(x - 3, r.y - 8, 6, r.height + 16)
            pygame.draw.rect(surface, config.WHITE, marker.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surface, config.P1_RED, marker, border_radius=3)
            if self._holding:                                # "확률 UP!" 말풍선
                tag = pygame.Rect(0, 0, 70, 20)
                tag.midbottom = (x, r.y - 10)
                pygame.draw.rect(surface, config.P1_RED, tag, border_radius=10)
                pygame.draw.rect(surface, config.INK, tag, width=2, border_radius=10)
                draw_text(surface, "확률 UP!", font, config.WHITE, tag.center)

        self.button.draw(surface)


# ================================================================
# MessageLog: 오른쪽 아래 말풍선 3개, 최신 것만 흰색
# ================================================================

class MessageLog:
    def __init__(self, bottomright):
        self.bottomright = bottomright
        self.messages = []

    def add(self, msg):
        self.messages.append(msg)
        if len(self.messages) > config.LOG_COUNT:       # 오래된 것부터 버림
            self.messages.pop(0)

    def draw(self, surface):
        right, bottom = self.bottomright
        height = config.LOG_HEIGHT
        y = bottom - 4                                   # 맨 아래 말풍선 그림자 자리
        newest = True
        for msg in reversed(self.messages):             # 최신 것부터 아래에서 위로
            rect = pygame.Rect(right - config.LOG_WIDTH, y - height, config.LOG_WIDTH, height)
            if newest:
                font = get_font(config.FONT_BODY, 13)
                pygame.draw.rect(surface, config.INK, rect.move(0, 4), border_radius=14)
                pygame.draw.rect(surface, config.WHITE, rect, border_radius=14)
                pygame.draw.rect(surface, config.INK, rect, width=3, border_radius=14)
                color = config.INK
            else:
                font = get_font(config.FONT_BODY, 12)
                pygame.draw.rect(surface, config.LOG_OLD_BG, rect, border_radius=14)
                pygame.draw.rect(surface, config.LOG_OLD_BORDER, rect, width=2, border_radius=14)
                color = config.LOG_OLD_TEXT
            text = fit_text(msg, font, rect.width - 24)
            draw_text(surface, text, font, color, (rect.x + 12, rect.centery), align="left")
            y -= height + config.LOG_GAP
            newest = False


# ================================================================
# PlayerInfo: 1P·2P 패널 (보여주기만, 게임 규칙은 모름)
# ================================================================

class PlayerInfo:
    def __init__(self, player, topleft):
        self.player = player
        self.rect = pygame.Rect(topleft[0], topleft[1], config.PANEL_WIDTH, config.PANEL_HEIGHT)
        self.is_turn = False    # C가 차례마다 정해 줌 → "내 차례!" 표시
        self.rank = 1           # C가 정해 줌 → 1위면 왕관

    def _count_buildings(self):
        count = 0
        for tile in self.player.tiles:
            if tile.building:
                count += 1
        return count

    def draw(self, surface):
        p = self.player
        r = self.rect
        tint = lighten(p.color)

        # 판넬 바탕
        if self.is_turn:                                         # 노란 테두리 빛
            pygame.draw.rect(surface, config.YELLOW, r.inflate(10, 10), border_radius=22)
        pygame.draw.rect(surface, config.INK, r.move(0, 8), border_radius=18)       # 그림자
        pygame.draw.rect(surface, config.WHITE, r, border_radius=18)

        # 머리 띠: 플레이어 색, 말 아이콘, 이름, 1위 왕관
        head = pygame.Rect(r.x, r.y, r.width, config.PANEL_HEAD)
        pygame.draw.rect(surface, p.color, head,
                         border_top_left_radius=18, border_top_right_radius=18)
        pygame.draw.line(surface, config.INK, head.bottomleft, head.bottomright, 3)
        icon = (r.x + 32, head.centery)
        pygame.draw.circle(surface, config.WHITE, icon, 20)
        pygame.draw.circle(surface, config.INK, icon, 20, 3)
        draw_pawn(surface, p.color, (icon[0], icon[1] + 12), 26)
        draw_text(surface, p.name, get_font(config.FONT_BUTTON, 21), config.WHITE,
                  (r.x + 60, head.centery), align="left")
        if self.rank == 1:
            x, y = r.right - 36, head.centery - 9
            crown = [(x + 2, y + 16), (x + 1, y + 4), (x + 7, y + 9), (x + 11, y + 2),
                     (x + 15, y + 9), (x + 21, y + 4), (x + 20, y + 16)]
            pygame.draw.polygon(surface, config.YELLOW, crown)
            pygame.draw.polygon(surface, config.INK, crown, 2)

        # 돈: 동전 + 1,350원
        coin = (r.x + 24, head.bottom + 24)
        pygame.draw.circle(surface, config.YELLOW, coin, 11)
        pygame.draw.circle(surface, config.INK, coin, 11, 2)
        pygame.draw.circle(surface, config.COIN_RIM, coin, 6, 2)
        draw_text(surface, f"{p.money:,}원", get_font(config.FONT_BODY, 24), config.INK,
                  (r.x + 42, coin[1]), align="left")

        # 땅 수, 건물 수
        font = get_font(config.FONT_BODY, 13)
        box_w = (r.width - 30) // 2
        land = pygame.Rect(r.x + 12, head.bottom + 46, box_w, 26)
        building = pygame.Rect(land.right + 6, land.y, box_w, 26)
        pygame.draw.rect(surface, tint, land, border_radius=10)
        pygame.draw.rect(surface, tint, building, border_radius=10)
        draw_text(surface, f"땅 {len(p.tiles)}", font, config.INK, land.center)
        draw_text(surface, f"건물 {self._count_buildings()}", font, config.INK, building.center)

        # 총자산 · 순위
        draw_text(surface, f"총자산 {p.total_assets():,}원 · {self.rank}위",
                  get_font(config.FONT_BODY, 12), config.SUB_TEXT,
                  (r.centerx, head.bottom + 90))

        pygame.draw.rect(surface, config.INK, r, width=4, border_radius=18)         # 테두리

        if self.is_turn:                                         # "내 차례!" 표
            tag = pygame.Rect(0, 0, 92, 28)
            tag.center = (r.centerx, r.y - 4)
            pygame.draw.rect(surface, config.INK, tag.move(0, 3), border_radius=12)
            pygame.draw.rect(surface, config.YELLOW, tag, border_radius=12)
            pygame.draw.rect(surface, config.INK, tag, width=3, border_radius=12)
            draw_text(surface, "내 차례!", get_font(config.FONT_BUTTON, 17), config.INK,
                      tag.center)


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
    infos = [PlayerInfo(players[0], config.P1_PANEL_POS),
             PlayerInfo(players[1], config.P2_PANEL_POS)]
    dice = DiceSet()
    gauge = RollGauge(config.GAUGE_CENTER, config.ROLL_BUTTON_CENTER)
    log = MessageLog(config.LOG_POS)
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
