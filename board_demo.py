"""판 혼자 테스트하기 (A 확인용, 게임에는 안 들어감).

실행: python board_demo.py
- 땅 칸 왼쪽 클릭: 지금 차례인 사람이 그 땅을 산다 → "구매!" 표시
- 내 땅 오른쪽 클릭: 다음 단계 건물 짓기 (별장 → 빌딩 → 호텔 → 랜드마크) → 통행료가 오른다
- 상대 땅 왼쪽 클릭: 인수 → "인수!" 표시 (랜드마크는 안 됨)
- K: 황금열쇠 한 장 뽑기 → 카드 그림 팝업 + 효과 실행
- 스페이스: 1P ↔ 2P 차례 바꾸기
"""
import pygame

import config
from board import Board
from cards import CardDeck, CardPopup
from player import HumanPlayer
from tiles import PropertyTile, draw_text
from ui import draw_pawn


class DemoGame:
    """카드가 부르는 Game 메서드만 흉내 내는 가짜 Game (C의 Game과 이름을 똑같이)."""

    def __init__(self):
        self.board = Board()
        self.deck = CardDeck()
        self.card_popup = CardPopup(self.board)
        self.message = "땅을 클릭하거나 K를 눌러 보세요"

    def log(self, msg):
        self.message = msg
        print(msg)

    def move_player_to(self, p, i, salary):
        steps = (i - p.position) % self.board.size
        passed_start = p.move(steps, self.board.size)
        if salary and passed_start:
            p.receive(config.SALARY)

    def ask_buy(self, tile):
        self.log(f"{tile.name}: 살 수 있는 땅")

    def ask_build(self, tile):
        self.log(f"{tile.name}: 내 땅")

    def ask_acquire(self, tile):
        self.log(f"{tile.name}: 인수할 수 있는 땅")


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    pygame.display.set_caption("외대 마블 - 판 테스트")
    clock = pygame.time.Clock()

    game = DemoGame()
    board = game.board
    players = [HumanPlayer("1P", config.P1_RED), HumanPlayer("2P", config.P2_BLUE)]
    turn = 0

    running = True
    while running:
        clock.tick(config.FPS)
        me, other = players[turn], players[1 - turn]
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue
            if game.card_popup.handle_event(event):     # 팝업이 떠 있으면 클릭은 팝업이 씀
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                turn = 1 - turn
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_k:
                board.get_tile(3).on_land(me, game)     # 3번 = 황금열쇠 칸
            elif event.type == pygame.MOUSEBUTTONDOWN:
                tile = board.tile_at(event.pos)
                if not isinstance(tile, PropertyTile):
                    continue
                if event.button == 1 and tile.owner is None:
                    ok = tile.buy(me)
                    game.log(f"{me.name} {tile.name} 구매" if ok else "돈이 부족해요")
                elif event.button == 1 and tile.owner is other:
                    price = tile.acquire_price
                    ok = tile.acquire(me)
                    game.log(f"{me.name} {tile.name} 인수 ({price:,}원)" if ok else "인수할 수 없어요")
                elif event.button == 3 and tile.owner is me:
                    building = tile.next_building()
                    ok = building is not None and tile.upgrade(building)
                    game.log(f"{tile.name} {tile.building.name} · 통행료 {tile.toll:,}원" if ok
                             else "더 지을 수 없어요")

        screen.fill(config.NAVY)
        board.draw(screen)
        for i, p in enumerate(players):
            rect = board.tile_rect(p.position)
            x = rect.x + 24 if i == 0 else rect.right - 24
            draw_pawn(screen, p.color, (x, rect.bottom - 10), 36)
        center = board.center_rect
        draw_text(screen, f"{me.name} 차례 · {me.money:,}원 · 땅 {len(me.tiles)}", 20, me.color,
                  (center.centerx, center.centery + 40))
        draw_text(screen, game.message, 16, config.WHITE, (center.centerx, center.centery + 80))
        game.card_popup.draw(screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
