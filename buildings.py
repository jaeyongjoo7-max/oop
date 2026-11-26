"""통행료 단계: 땅 하나에 단계 하나. 별장 → 빌딩 → 호텔 → 랜드마크 순서로 오른다.

11/22 결정: 건물을 돈 내고 짓지 않고, 자기 땅에 다시 오면 공짜로 한 단계 오른다.
그래서 "짓는 값"은 없애고, 이름과 통행료 배수만 남겼다.

별장·빌딩·호텔은 데이터(이름, 통행료 배수)만 다르므로 Building 객체로 만든다.
랜드마크는 "인수할 수 없다"는 행동이 다르므로 Landmark 클래스로 상속한다.
→ "행동이 다르면 상속, 데이터만 다르면 객체" (지침서 4쪽)
"""
import pygame

import config


class Building:
    def __init__(self, name, level, toll_rate):
        self.name = name              # 별장 / 빌딩 / 호텔 / 랜드마크
        self.level = level            # 1 별장, 2 빌딩, 3 호텔, 4 랜드마크
        self.toll_rate = toll_rate    # 통행료 배수 (PropertyTile.toll이 씀)

    def can_be_acquired(self):
        return True

    def draw(self, surface, rect):
        """칸 왼쪽 아래에 작은 집 아이콘. (단계 이름 글자는 PropertyTile이 옆에 쓴다)"""
        x, y = rect.x + 12, rect.bottom - 22
        roof = [(x, y + 6), (x + 8, y - 2), (x + 16, y + 6)]
        pygame.draw.rect(surface, config.WHITE, (x + 2, y + 6, 12, 10))
        pygame.draw.rect(surface, config.INK, (x + 2, y + 6, 12, 10), 2)
        pygame.draw.polygon(surface, self.icon_color(), roof)
        pygame.draw.polygon(surface, config.INK, roof, 2)

    def icon_color(self):
        return config.P1_RED

    def __repr__(self):
        return f"<{type(self).__name__} {self.name} x{self.toll_rate}>"


class Landmark(Building):
    """랜드마크: 인수할 수 없고, 칸에 금색 테두리를 두른다 (행동이 달라서 상속)."""

    def can_be_acquired(self):
        return False

    def icon_color(self):
        return config.LANDMARK_GOLD

    def draw(self, surface, rect):
        pygame.draw.rect(surface, config.LANDMARK_GOLD, rect.inflate(-10, -10), 3)
        super().draw(surface, rect)          # 집 아이콘은 부모 것을 그대로 (5강 재사용)


def make_building(level):
    """level 단계 객체를 만든다. 마지막 단계는 Landmark (팩토리)."""
    name, toll_rate = config.BUILDING_STEPS[level - 1]
    building_class = Landmark if level == len(config.BUILDING_STEPS) else Building
    return building_class(name, level, toll_rate)
