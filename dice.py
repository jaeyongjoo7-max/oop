import random
import pygame
import config


class Die:
    """주사위 하나: 눈(value)을 기억하고 자기 모습만 그린다."""

    # 눈마다 점이 찍히는 자리 (열, 행). 3×3 칸 기준
    PIPS = {
        1: [(1, 1)],
        2: [(0, 0), (2, 2)],
        3: [(0, 0), (1, 1), (2, 2)],
        4: [(0, 0), (2, 0), (0, 2), (2, 2)],
        5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
        6: [(0, 0), (2, 0), (0, 1), (2, 1), (0, 2), (2, 2)],
    }

    def __init__(self):
        self.value = 1

    def draw(self, surface, rect):
        radius = config.DIE_RADIUS
        shadow = rect.move(0, config.DIE_SHADOW)                       # 아래 그림자
        pygame.draw.rect(surface, config.INK, shadow, border_radius=radius)
        pygame.draw.rect(surface, config.DIE_COLOR, rect, border_radius=radius)
        pygame.draw.rect(surface, config.INK, rect, width=3, border_radius=radius)

        pad = config.DIE_PADDING
        cell = (rect.width - pad * 2) / 3                              # 3×3 칸 하나 크기
        for col, row in Die.PIPS[self.value]:
            x = rect.x + pad + cell * col + cell / 2
            y = rect.y + pad + cell * row + cell / 2
            pygame.draw.circle(surface, config.INK, (x, y), config.PIP_RADIUS)


class DiceSet:
    """주사위 두 개 묶음: 굴리기, 굴러가는 연출, 결과 알려 주기."""

    def __init__(self):
        self.dice = [Die(), Die()]
        self._rolling = False
        self._result = (1, 1)      # 굴리기 시작할 때 미리 정해 둔 결과
        self._elapsed = 0          # 굴리기 시작한 뒤 지난 시간 (ms)
        self._flip_time = 0        # 눈을 마지막으로 바꾼 뒤 지난 시간 (ms)

    def reset(self):
        """새 판: 두 주사위를 1로 되돌린다 (시안의 첫 턴 모습)"""
        self._rolling = False
        for die in self.dice:
            die.value = 1

    def roll(self, strategy):
        """strategy가 RandomRoll이든 GaugeRoll이든 똑같이 부른다 (다형성)."""
        self._result = strategy.roll_values()
        self._rolling = True
        self._elapsed = 0
        self._flip_time = 0

    def update(self, dt):
        if not self._rolling:
            return
        self._elapsed += dt
        self._flip_time += dt
        if self._elapsed >= config.DICE_ROLL_TIME:          # 연출 끝 → 진짜 결과
            self._rolling = False
            for i in range(2):
                self.dice[i].value = self._result[i]
        elif self._flip_time >= config.DICE_FLIP_TIME:     # 굴러가는 동안 눈이 바뀜
            self._flip_time = 0
            for die in self.dice:
                die.value = random.randint(1, 6)

    # ---------- C가 읽는 값 (읽기만) ----------
    @property
    def is_rolling(self):
        return self._rolling

    @property
    def values(self):
        return (self.dice[0].value, self.dice[1].value)

    @property
    def total(self):
        return self.dice[0].value + self.dice[1].value

    @property
    def is_double(self):
        return self.dice[0].value == self.dice[1].value

    # ---------- 그리기 ----------
    def draw(self, surface, center):
        size = config.DIE_SIZE
        gap = config.DIE_GAP
        cx, cy = center
        lefts = [cx - gap // 2 - size, cx + gap // 2]      # 왼쪽 주사위, 오른쪽 주사위
        for i in range(2):
            shake = random.randint(-4, 4) if self._rolling else 0   # 구를 때 흔들림
            rect = pygame.Rect(lefts[i], cy - size // 2 + shake, size, size)
            self.dice[i].draw(surface, rect)


if __name__ == "__main__":
    # 혼자 확인용: 클릭 = 일반 굴리기, 키보드 1/2/3 = 게이지 굴리기 (작은/중간/큰 수)
    from roll_strategies import RandomRoll, GaugeRoll

    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    clock = pygame.time.Clock()
    dice = DiceSet()
    center = (config.SCREEN_W // 2, config.SCREEN_H // 2)
    was_rolling = False
    running = True

    while running:
        dt = clock.tick(config.FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not dice.is_rolling:
                dice.roll(RandomRoll())
            elif event.type == pygame.KEYDOWN and not dice.is_rolling:
                if event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    dice.roll(GaugeRoll(event.key - pygame.K_1))

        dice.update(dt)
        if was_rolling and not dice.is_rolling:              # 방금 멈췄을 때 한 번만
            print(dice.values, "합", dice.total, "더블!" if dice.is_double else "")
        was_rolling = dice.is_rolling

        screen.fill(config.NAVY)
        dice.draw(screen, center)
        pygame.display.flip()

    pygame.quit()
