# turns.py : 턴 관리 (C 담당, 11/26 새로 만듦)
#
# 누구 차례인지, 몇 턴째인지, 쉬는 사람을 건너뛰는 규칙을 이 클래스 하나가 맡는다.
# 예전에는 Game 안에 turn_index, turn_count 변수로 흩어져 있었다 → 하나로 모아 숨김 (6강 캡슐화)
#
# 11/18 팀 규칙
#   1턴 = 한 사람의 차례. MAX_TURNS = 40이면 두 사람 모두 정확히 20번씩
#   쉰 차례도 1턴으로 센다. 더블로 한 번 더 굴린 것은 세지 않는다 (next를 부르지 않으므로)


class TurnManager:
    def __init__(self, players, max_turns):
        self._players = list(players)      # 숨기는 값: 순서대로 선 플레이어들
        self._max_turns = max_turns
        self._index = 0                    # 숨기는 값: 지금 차례인 사람의 번호 (1P부터)
        self._count = 0                    # 숨기는 값: 끝난 턴 수

    # ---------- 밖에서 읽기만 하는 값 (getter만, setter 없음) ----------
    @property
    def current(self):
        """지금 차례인 사람"""
        return self._players[self._index]

    @property
    def opponent(self):
        """다음 차례인 사람 (2인용이라 곧 상대)"""
        return self._players[(self._index + 1) % len(self._players)]

    @property
    def count(self):
        """끝난 턴 수 (0부터)"""
        return self._count

    @property
    def max_turns(self):
        return self._max_turns

    def is_over(self):
        """정해진 턴을 다 썼는가 (TurnLimitWin이 부른다)"""
        return self._count >= self._max_turns

    # ---------- 차례를 바꾸는 문은 이것 하나 ----------
    def next(self):
        """다음 사람에게 차례를 넘긴다.
        넘길 때마다 턴을 1 세고, 쉬는 턴이 남은 사람은 하나 쓰고 건너뛴다.
        건너뛴 사람 목록을 돌려준다 (Game이 기록에 남기려고)."""
        skipped = []
        while True:                        # 두 사람이 모두 쉬는 중일 수도 있어서 while
            self._index = (self._index + 1) % len(self._players)
            self._count += 1
            if self.is_over():
                return skipped
            if not self.current.take_rest():   # 쉬는 턴은 Player 안에 숨겨져 있음
                return skipped
            skipped.append(self.current)
