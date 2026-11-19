# game.py : 게임 루프, 상태 바꾸기, 그리는 순서
import pygame
import config
from states import RollState, GameOverState, BuyState
from board import Board
from cards import CardDeck, CardPopup
from player import HumanPlayer, AIPlayer
from dice import DiceSet
from ui import RollGauge, MessageLog, PlayerInfo, draw_pawn


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # 팀원이 만든 부품을 Game이 가지고 있다 (컴포지션)
        self.board = Board()                                   # A
        self.deck = CardDeck()                                 # A
        self.players = [HumanPlayer("플레이어 1", config.P1_RED),   # B
                        AIPlayer("플레이어 2", config.P2_BLUE)]
        self.dice = DiceSet()                                  # B
        self.gauge = RollGauge(config.GAUGE_CENTER, config.ROLL_BUTTON_CENTER)
        self.message_log = MessageLog(config.LOG_POS)
        self.infos = [PlayerInfo(self.players[0], config.P1_PANEL_POS),
                      PlayerInfo(self.players[1], config.P2_PANEL_POS)]
        self.card_popup = CardPopup(self.board)                # A: 황금열쇠 그림
        
        self.turn_index = 0            # 지금 차례인 사람의 번호 (0 또는 1)
        self.turn_count = 0            # 지금까지 턴 수
        self.state = RollState(self)   # 현재 상태 객체 하나
        self.log(f"{self.current_player.name} 차례")

    def change_state(self, new_state):
        self.state = new_state

    def log(self, msg):
        self.message_log.add(msg)      # 화면 오른쪽 아래 말풍선

    @property
    def current_player(self):          # 지금 차례인 사람
        return self.players[self.turn_index]

    @property
    def opponent(self):                # 상대
        return self.players[1 - self.turn_index]

    def next_player(self):
        self.turn_index = 1 - self.turn_index      # 0이면 1로, 1이면 0으로

    def end_turn(self):                # 턴 끝내기: 순서는 ① 파산 → ② 더블 → ③ 다음 사람
        p = self.current_player
        if p.is_bankrupt():                              # ① 돈이 0원보다 적으면 끝
            self.change_state(GameOverState(self, self.opponent, "파산"))
            return
        if self.dice.is_double and p.rest_turns == 0:    # ② 더블 (학사경고에 갔으면 넘김)
            self.log(f"{p.name}: 더블! 한 번 더")
            self.change_state(RollState(self))
            return
        self.pass_turn()                                 # ③ 다음 사람에게

    def pass_turn(self):               # 다음 사람에게 차례 넘기기 (1턴 = 한 사람의 차례)
        while True:                    # 두 사람이 모두 쉬는 중일 수도 있어서 while
            self.turn_count += 1       # 방금 끝난 차례를 1턴으로 센다 (쉰 차례도 셈)
            if self.turn_count >= config.MAX_TURNS:
                self.change_state(GameOverState(self, self.winner_by_assets(), "턴 다 씀"))
                return
            self.next_player()
            p = self.current_player
            if p.rest_turns > 0:       # 학사경고: 이번 차례는 쉬고 다음 사람으로
                p.rest_turns -= 1
                self.log(f"{p.name}: 학사경고로 이번 차례 쉼")
                continue
            self.log(f"{p.name} 차례")
            self.change_state(RollState(self))
            return

    def winner_by_assets(self):        # 턴 다 씀일 때 승자: 총자산 → 현금 → 무승부(None)
        a, b = self.players
        if a.total_assets() != b.total_assets():
            return a if a.total_assets() > b.total_assets() else b
        if a.money != b.money:
            return a if a.money > b.money else b
        return None

    # A의 칸·카드가 부르는 메서드. 지금은 이름만 있고, 다음 단계에서 채운다.
    def ask_buy(self, tile):                   # 빈 땅 도착: 살지 묻기
        if tile.can_buy(self.current_player):
            self.change_state(BuyState(self, tile))
        else:
            self.log(f"{tile.name}: 돈이 부족해 못 삼")

    def ask_build(self, tile):                 # 내 땅 도착: 지을지 묻기
        self.log(f"{tile.name}: 내 땅")

    def ask_acquire(self, tile):               # 상대 땅 도착: 인수할지 묻기
        self.log(f"{tile.name}: 인수할 수 있는 땅")

    def move_player_to(self, p, i, salary):    # 플레이어 p를 i번 칸으로 옮기기 (카드가 부름)
        """앞으로 가서 i번 칸에 선다. salary가 True면 정문을 지나거나 도착할 때 월급.
        도착한 칸의 on_land()는 부르는 쪽(카드)이 정한다."""
        steps = (i - p.position) % self.board.size
        passed_start = p.move(steps, self.board.size)
        if salary and passed_start:
            p.receive(config.SALARY)
            self.log(f"{p.name}: 정문 통과, 월급 {config.SALARY:,}원")

    def run(self):
        while self.running:                        # 무한 루프
            dt = self.clock.tick(config.FPS)       # 갱신 주기, 지난 시간(ms)
            for event in pygame.event.get():       # 이벤트 수집
                if event.type == pygame.QUIT:
                    self.running = False
                elif self.card_popup.handle_event(event):
                    pass                           # 카드 그림이 떠 있으면 클릭은 그림을 닫는 데만 씀
                else:
                    self.state.handle_event(event) # User → Game → 상태
            self.state.update(dt)
            self.draw()
        pygame.quit()

    def draw(self):
        # 그리는 순서는 Game이 정한다: 뒤에 그린 것이 위에 보인다
        self.screen.fill(config.NAVY)              # 1) 배경
        self.board.draw(self.screen)               # 2) 판
        self._draw_pawns()                         # 3) 말
        self._update_panels()
        for info in self.infos:                    # 4) 1P·2P 패널
            info.draw(self.screen)
        self.message_log.draw(self.screen)         # 5) 기록
        self.state.draw(self.screen)               # 6) 지금 상태가 자기 화면을 그림
        self.card_popup.draw(self.screen)          # 7) 황금열쇠 그림 (맨 위)
        pygame.display.flip()                      # 윈도우 업데이트

    def _draw_pawns(self):
        """임시: 말을 칸 아래쪽에 바로 그린다. 나중에 B의 MoveAnimation으로 바꾼다."""
        for i, p in enumerate(self.players):
            rect = self.board.tile_rect(p.position)
            x = rect.x + 24 if i == 0 else rect.right - 24    # 1P 왼쪽, 2P 오른쪽
            draw_pawn(self.screen, p.color, (x, rect.bottom - 10), 36)

    def _update_panels(self):
        """패널에 차례와 순위를 알려 준다 (패널은 보여주기만 한다)."""
        for i, info in enumerate(self.infos):
            me, other = self.players[i], self.players[1 - i]
            info.is_turn = (i == self.turn_index)
            info.rank = 1 if me.total_assets() >= other.total_assets() else 2
