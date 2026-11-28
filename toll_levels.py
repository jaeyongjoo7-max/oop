"""통행료 단계: 땅 하나에 단계 하나. 0단계(기본)에서 시작해 최대 단계까지 오른다.

11/22 결정: 건물을 짓지 않는다. 자기 땅에 다시 오면 공짜로 통행료가 한 단계 오른다.
11/26: 건물 이름(별장·빌딩·호텔·랜드마크)과 집 아이콘도 없앴다. 칸에는 지금 통행료 금액만 쓴다.

보통 단계는 데이터(단계 번호, 통행료 배수)만 다르므로 TollLevel 객체로 만든다.
최대 단계는 "인수할 수 없다"는 행동이 다르므로 MaxTollLevel 클래스로 상속한다.
→ "행동이 다르면 상속, 데이터만 다르면 객체" (지침서 4쪽)
"""
import pygame

import config
from ui import draw_text, get_font


class TollLevel:
    def __init__(self, level, toll_rate):
        self.level = level            # 0 기본, 1, 2, ... (마지막이 최대)
        self.toll_rate = toll_rate    # 통행료 배수 (PropertyTile.toll이 씀)

    def can_be_acquired(self):
        return True

    def draw(self, surface, rect, toll):
        """이름 아래에 지금 통행료 금액. (칸 아래쪽은 말, 오른쪽 아래는 주인 깃발 자리)"""
        draw_text(surface, f"통행료 {toll:,}", get_font(config.FONT_BODY, 11), config.SUB_TEXT,
                  (rect.centerx, rect.y + 66))

    def __repr__(self):
        return f"<{type(self).__name__} {self.level}단계 x{self.toll_rate}>"


class MaxTollLevel(TollLevel):
    """최대 단계: 인수할 수 없고, 칸에 금색 테두리를 두른다 (행동이 달라서 상속)."""

    def can_be_acquired(self):
        return False

    def draw(self, surface, rect, toll):
        pygame.draw.rect(surface, config.MAX_TOLL_GOLD, rect.inflate(-8, -8), 3, border_radius=4)
        super().draw(surface, rect, toll)    # 금액 글자는 부모 것을 그대로 (5강 재사용)


def make_toll_level(level):
    """level 단계 객체를 만든다. 마지막 단계는 MaxTollLevel."""
    toll_rate = config.TOLL_STEPS[level]
    level_class = MaxTollLevel if level == len(config.TOLL_STEPS) - 1 else TollLevel
    return level_class(level, toll_rate)