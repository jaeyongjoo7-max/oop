"""판 혼자 테스트하기 (A 확인용, 게임에는 안 들어감).

실행: python board_demo.py
- 땅 칸 왼쪽 클릭: 지금 차례인 사람이 그 땅을 산다 → "구매!" 표시
- 내 땅 오른쪽 클릭: 별장 짓기 → 통행료가 오른다
- 상대 땅 왼쪽 클릭: 인수 → "인수!" 표시
- 스페이스: 1P ↔ 2P 차례 바꾸기
"""
import pygame

import config
from board import Board
from tiles import PropertyTile, draw_text


class DemoPlayer:
    """B의 Player가 생기기 전까지 쓰는 가짜 플레이어."""

    def __init__(self, name, color, money):
        self.name, self.color, self._money = name, color, money

    @property
    def money(self):
        return self._money

    def pay(self, amount):
        self._money -= amount

    def receive(self, amount):
        self._money += amount


class DemoBuilding:
    """buildings.py가 생기기 전까지 쓰는 가짜 별장."""
    name, cost, toll_rate = "별장", 50, 2

    def can_be_acquired(self):
        return True


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    pygame.display.set_caption("외대 마블 - 판 테스트")
    clock = pygame.time.Clock()

    board = Board()
    players = [DemoPlayer("1P", config.P1_RED, 1500), DemoPlayer("2P", config.P2_BLUE, 1500)]
    turn = 0
    message = "땅을 클릭해 보세요"

    running = True
    while running:
        clock.tick(config.FPS)
        me, other = players[turn], players[1 - turn]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                turn = 1 - turn
            elif event.type == pygame.MOUSEBUTTONDOWN:
                tile = board.tile_at(event.pos)
                if not isinstance(tile, PropertyTile):
                    continue
                if event.button == 1 and tile.owner is None:
                    ok = tile.buy(me)
                    message = f"{me.name} {tile.name} 구매" if ok else "돈이 부족해요"
                elif event.button == 1 and tile.owner is other:
                    ok = tile.acquire(me)
                    message = f"{me.name} {tile.name} 인수 ({tile.acquire_price:,}원)" if ok else "인수할 수 없어요"
                elif event.button == 3 and tile.owner is me:
                    ok = tile.upgrade(DemoBuilding())
                    message = f"{tile.name} 통행료 {tile.toll:,}원" if ok else "돈이 부족해요"

        screen.fill(config.NAVY)
        board.draw(screen)
        center = board.center_rect
        draw_text(screen, f"{me.name} 차례 · {me.money:,}원", 20, me.color,
                  (center.centerx, center.centery + 40))
        draw_text(screen, message, 16, config.WHITE, (center.centerx, center.centery + 80))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
