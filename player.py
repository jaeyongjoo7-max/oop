from abc import ABC, abstractmethod
import random
import config

WAIT = None    # 사람: "버튼을 기다려 주세요" (지침서 5쪽)


class Player(ABC):
    """사람과 AI의 공통 틀. 직접 객체로 만들지 않는다 (6강 추상화)."""

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self.position = 0                  # 지금 서 있는 칸 번호 (0 = 정문)
        self._money = config.START_MONEY   # 숨기는 값: 밖에서 직접 못 바꿈
        self._tiles = []                   # 내가 가진 땅 (PropertyTile 객체들)
        self.rest_turns = 0
    # ---------- 돈 (캡슐화) ----------
    @property
    def money(self):            # getter만 있고 setter가 없음 → 읽기만 가능
        return self._money

    def pay(self, amount):      # 돈은 pay / receive 로만 바뀐다
        self._money -= amount

    def receive(self, amount):
        self._money += amount

    def is_bankrupt(self):
        return self._money < 0

    # ---------- 위치 ----------
    def move(self, steps, size):
        """steps 칸 앞으로. 정문을 지나면 True를 돌려준다 (월급 판단용)."""
        passed_start = self.position + steps >= size
        self.position = (self.position + steps) % size
        return passed_start

    def move_to(self, i):
        self.position = i

    # ---------- 땅 ----------
    def add_tile(self, tile):       # A의 buy(p), acquire(p)가 부름
        self._tiles.append(tile)

    def remove_tile(self, tile):    # 인수당했을 때 A가 부름
        self._tiles.remove(tile)

    @property
    def tiles(self):                # 읽기만 (목록 복사본을 줌)
        return list(self._tiles)

    def total_assets(self):
        """돈 + 땅값 + 건물값. 건물값 계산법은 A의 건물 규칙이 정해지면 맞춘다."""
        total = self._money
        for tile in self._tiles:
            total += tile.price
            if tile.building:
                total += tile.building.cost
        return total

    # ---------- 결정 (사람/AI가 다르게 구현) ----------
    @abstractmethod
    def decide_buy(self, tile):         # True / False / WAIT
        pass

    @abstractmethod
    def decide_build(self, tile):       # True / False / WAIT
        pass

    @abstractmethod
    def decide_acquire(self, tile):     # True / False / WAIT
        pass

    @abstractmethod
    def choose_roll(self):              # 게이지 구간 0/1/2 또는 WAIT
        pass


class HumanPlayer(Player):
    """사람: 바로 답하지 않고 버튼을 기다린다."""

    def decide_buy(self, tile):
        return WAIT

    def decide_build(self, tile):
        return WAIT

    def decide_acquire(self, tile):
        return WAIT

    def choose_roll(self):
        return WAIT         # 굴리기 버튼을 누를 때까지 기다림


class AIPlayer(Player):
    """AI: 그 자리에서 바로 답한다."""

    def decide_buy(self, tile):
        return self.money - tile.price >= config.AI_SAFE_MONEY

    def decide_build(self, tile):
        return False    # 임시: A의 건물 규칙(짓는 값)이 정해지면 채운다

    def decide_acquire(self, tile):
        return False    # 임시: 인수 가격이 정해지면 채운다

    def choose_roll(self):
        return random.randint(0, 2)     # 임시: 게이지 구간을 아무거나 고름


if __name__ == "__main__":
    # 혼자 확인용 (2강: import될 때는 실행되지 않음)
    p1 = HumanPlayer("1P", config.P1_RED)
    print(p1.money)              # 1500
    p1.pay(200)
    p1.receive(50)
    print(f"{p1.money:,}원")      # 1,350원

    print(p1.move(5, 20), p1.position)     # False 5
    print(p1.move(17, 20), p1.position)    # True 2  (정문 지나감)

    print(p1.decide_buy(None) is WAIT)     # True

    try:
        p1.money = 0                       # 막혀야 정상
    except AttributeError as e:
        print("직접 못 바꿈:", e)

    try:
        Player("x", config.WHITE)          # 추상 클래스라 못 만듦
    except TypeError as e:
        print("추상 클래스:", e)
