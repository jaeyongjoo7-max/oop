# win_conditions.py : 승리 조건 (C 담당, 11/26 채움)
#
# Game.end_turn()은 조건 목록을 돌면서 check(game)만 부른다 (다형성).
# 새 승리 조건이 필요하면 end_turn에 if를 더하지 않고, WinCondition을 상속한 클래스를 하나 더 만든다.
# MonopolyWin(한 줄 독점)은 11/26 추천안대로 뺐다.
from abc import ABC, abstractmethod


class WinCondition(ABC):
    """모든 승리 조건의 공통 틀 (6강 추상 클래스)"""

    @abstractmethod
    def check(self, game):
        """게임이 끝났으면 (승자, 이유)를, 아니면 None을 돌려준다. 승자가 None이면 무승부."""

    def richest(self, players):
        """총자산 → 현금 순으로 가장 많은 사람. 완전히 같으면 None(무승부).
        자식 클래스들이 물려받아 같이 쓴다 (5강 재사용)."""
        best = None
        tie = False
        for p in players:
            score = (p.total_assets(), p.money)     # 앞의 값부터 비교: 총자산, 같으면 현금
            if best is None or score > (best.total_assets(), best.money):
                best, tie = p, False
            elif score == (best.total_assets(), best.money):
                tie = True
        return None if tie else best


class BankruptcyWin(WinCondition):
    """누군가 파산하면 끝. 남은 사람 중 가장 부자가 승자."""

    def check(self, game):
        for player in game.players:
            if player.is_bankrupt():
                others = [p for p in game.players if p is not player]
                return self.richest(others), f"{player.name} 파산"
        return None


class TurnLimitWin(WinCondition):
    """정해진 턴(40)을 다 쓰면 끝. 총자산이 많은 사람이 승자."""

    def check(self, game):
        if game.turns.is_over():
            return self.richest(game.players), "턴 다 씀"
        return None
