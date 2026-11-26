from abc import ABC, abstractmethod
import random
import config


class RollStrategy(ABC):
    """주사위 두 개를 '어떻게' 굴릴지 정하는 틀 (강의 범위 밖: 전략 패턴)."""

    @abstractmethod
    def roll_values(self):
        """주사위 두 개의 눈을 (a, b) 튜플로 돌려준다."""
        pass


class RandomRoll(RollStrategy):
    """일반 굴리기: 짧게 클릭했을 때."""

    def roll_values(self):
        return random.randint(1, 6), random.randint(1, 6)


class GaugeRoll(RollStrategy):
    """게이지 굴리기: 꾹 눌렀다 뗀 구간의 수가 나올 확률이 올라간다."""

    def __init__(self, zone):
        self.zone = zone    # 0 = 작은 수, 1 = 중간, 2 = 큰 수

    def roll_values(self):
        low, high = config.GAUGE_ZONES[self.zone]
        for _ in range(config.GAUGE_TRIES):        # 최대 몇 번 다시 굴려 보기
            a = random.randint(1, 6)
            b = random.randint(1, 6)
            if low <= a + b <= high:                # 구간에 들어오면 바로 결정
                return a, b
        return a, b                                 # 끝까지 못 들어오면 마지막 값


if __name__ == "__main__":
    # 혼자 확인용: 1000번씩 굴려서 구간에 들어온 비율 비교
    for zone in range(3):
        low, high = config.GAUGE_ZONES[zone]
        normal = 0
        gauge = 0
        for _ in range(1000):
            a, b = RandomRoll().roll_values()
            if low <= a + b <= high:
                normal += 1
            a, b = GaugeRoll(zone).roll_values()
            if low <= a + b <= high:
                gauge += 1
        print(f"구간 {low}~{high}: 일반 {normal / 10:.0f}%  게이지 {gauge / 10:.0f}%")
