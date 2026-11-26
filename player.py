from abc import ABC, abstractmethod
import random
import config

WAIT = None    # 사람: "버튼을 기다려 주세요" (지침서 5쪽)


class Player(ABC):
    """사람과 AI의 공통 틀. 직접 객체로 만들지 않는다 (6강 추상화).
    돈·위치·땅·쉬는 턴은 여기 한 곳에만 있고, 자식(HumanPlayer, AIPlayer)은 물려받아 쓴다 (5강 재사용)."""

    def __init__(self, name, color):
        self.name = name
        self.color = color
        self._position = 0                 # 숨기는 값: 지금 서 있는 칸 번호 (0 = 정문)
        self._money = config.START_MONEY   # 숨기는 값: 밖에서 직접 못 바꿈
        self._tiles = []                   # 내가 가진 땅 (PropertyTile 객체들)
        self._rest_turns = 0               # 숨기는 값: 남은 쉬는 턴 (학사경고)

    # ---------- 돈 (캡슐화) ----------
    @property
    def money(self):            # getter만 있고 setter가 없음 → 읽기만 가능
        return self._money

    def pay(self, amount):      # 돈은 pay / receive 로만 바뀐다
        self._money -= amount

    def receive(self, amount):
        self._money += amount

    def pay_to(self, other, amount):
        """다른 플레이어에게 돈을 준다 (통행료, 인수). pay와 receive를 그대로 다시 쓴다."""
        self.pay(amount)
        other.receive(amount)

    def is_bankrupt(self):
        return self._money < 0

    # ---------- 위치 (캡슐화) ----------
    @property
    def position(self):         # getter만 → 밖에서는 읽기만. 바꾸는 문은 move / move_to
        return self._position

    def move(self, steps, size):
        """steps 칸 앞으로. 정문을 지나면 True를 돌려준다 (월급 판단용)."""
        passed_start = self._position + steps >= size
        self._position = (self._position + steps) % size
        return passed_start

    def move_to(self, i):
        self._position = i

    # ---------- 쉬는 턴 (캡슐화) ----------
    @property
    def rest_turns(self):       # 읽기만
        return self._rest_turns

    def start_rest(self, turns):
        """학사경고에 도착했을 때 IslandTile이 부른다."""
        self._rest_turns = turns

    def take_rest(self):
        """쉬는 턴이 남았으면 하나 쓰고 True. TurnManager가 차례를 넘길 때 부른다."""
        if self._rest_turns > 0:
            self._rest_turns -= 1
            return True
        return False

    # ---------- 땅 ----------
    def add_tile(self, tile):       # A의 buy(p), acquire(p)가 부름
        self._tiles.append(tile)

    def remove_tile(self, tile):    # 인수당했을 때 A가 부름
        self._tiles.remove(tile)

    @property
    def tiles(self):                # 읽기만 (목록 복사본을 줌)
        return list(self._tiles)

    def total_assets(self):
        """돈 + 땅값. (11/22부터 통행료 단계는 공짜로 오르므로 자산에 더하지 않는다)"""
        total = self._money
        for tile in self._tiles:
            total += tile.price
        return total

    # ---------- 결정 (사람/AI가 다르게 구현) ----------
    @abstractmethod
    def decide_buy(self, tile):         # True / False / WAIT
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

    def decide_acquire(self, tile):
        return WAIT

    def choose_roll(self):
        return WAIT         # 굴리기 버튼을 누를 때까지 기다림


class AIPlayer(Player):
    """AI: 그 자리에서 바로 답한다.
    돈·위치·땅은 Player에서 물려받고, 결정하는 방법만 다르게 만든다."""

    def __init__(self, name, color, safe_money=config.AI_SAFE_MONEY):
        super().__init__(name, color)          # 돈·위치·땅은 부모 것을 그대로 (5강 재사용)
        self.safe_money = safe_money           # AI마다 다른 데이터: 사고 나서 남겨 둘 돈

    def _can_afford(self, cost):
        """판단 기준은 여기 한 곳에만: cost를 내고도 safe_money 이상 남는가"""
        return self.money - cost >= self.safe_money

    def decide_buy(self, tile):
        return self._can_afford(tile.price)

    def decide_acquire(self, tile):
        return self._can_afford(tile.acquire_price)

    def choose_roll(self):
        return random.randint(0, 2)     # 게이지 구간을 아무거나 고름


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

    for wrong in ("money", "position", "rest_turns"):
        try:
            setattr(p1, wrong, 0)          # 막혀야 정상
        except AttributeError as e:
            print("직접 못 바꿈:", e)

    p1.start_rest(1)
    print(p1.take_rest(), p1.take_rest())  # True False (한 번만 쉼)

    ai = AIPlayer("AI", config.P2_BLUE)
    careful = AIPlayer("조심 AI", config.P2_BLUE, safe_money=1300)   # 같은 클래스, 다른 데이터
    print(ai._can_afford(250), careful._can_afford(250))              # True False

    try:
        Player("x", config.WHITE)          # 추상 클래스라 못 만듦
    except TypeError as e:
        print("추상 클래스:", e)
