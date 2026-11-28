# game.py : 게임 루프, 상태 바꾸기, 그리는 순서
import pygame
import config
from states import TitleState, RollState, BuyState, AcquireState, GameOverState
from turns import TurnManager
from win_conditions import BankruptcyWin, TurnLimitWin
from board import Board
from cards import CardDeck, CardPopup
from player import HumanPlayer, AIPlayer
from dice import DiceSet
from ui import RollGauge, MessageLog, PlayerInfo, draw_background, draw_pawn, draw_text, get_font


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # 판이 바뀌어도 그대로 다시 쓰는 부품 (컴포지션)
        self.dice = DiceSet()                                  # B
        self.gauge = RollGauge(config.GAUGE_CENTER, config.ROLL_BUTTON_CENTER)
        self.win_conditions = [BankruptcyWin(), TurnLimitWin()]   # 새 조건은 여기에 객체 하나만 추가

        self.mode = "ai"                                       # "ai" = 사람 vs AI, "person" = 사람 vs 사람
        self.names = ["플레이어 1", "플레이어 2"]                  # 게임 설정 화면에서 바꾼다
        self.players = []                                      # 아직 판이 없음 → 시작 화면
        self.change_state(TitleState(self))                    # 처음엔 타이틀부터

    # ---------- 한 판 시작 ----------
    def make_players(self, mode, names):
        """사람/AI는 여기 한 곳에서만 정한다. 그 뒤로는 아무도 종류를 묻지 않는다 (다형성).
        사람 vs 사람은 새 클래스 없이 HumanPlayer 객체를 하나 더 만들면 된다 (재사용)."""
        p1 = HumanPlayer(names[0], config.P1_RED)
        if mode == "person":
            return [p1, HumanPlayer(names[1], config.P2_BLUE)]
        return [p1, AIPlayer(names[1], config.P2_BLUE)]

    def start(self, players):
        """새 판을 시작한다: 판·카드·패널·턴을 새로 만든다 (다시 하기, 나중엔 상대 고르기에서도 부름)."""
        self.players = players
        self.board = Board()                                   # A
        self.deck = CardDeck()                                 # A
        self.card_popup = CardPopup(self.board)                # A: 황금열쇠 그림
        self.message_log = MessageLog(config.LOG_RECT)         # B
        self.infos = [PlayerInfo(players[0], config.P1_PANEL_POS, "1P"),
                      PlayerInfo(players[1], config.P2_PANEL_POS, "2P")]
        self.dice.reset()                                      # 다시 쓰는 부품은 처음 모습으로
        self.gauge.reset()
        self.turns = TurnManager(players, config.MAX_TURNS)    # C: 턴 관리는 이 객체 하나에게 맡김
        self.change_state(RollState(self))
        self.log(f"{self.current_player.name} 차례")

    def restart(self):
        self.start(self.make_players(self.mode, self.names))

    def go_title(self):
        """판을 치우고 메인으로. players를 비우면 draw가 판·패널·카드 그림을 더 그리지 않는다."""
        self.players = []
        self.change_state(TitleState(self))

    # ---------- 다른 객체가 부르는 메서드 ----------
    def change_state(self, new_state):
        self.state = new_state

    def log(self, msg):
        self.message_log.add(msg)      # 화면 오른쪽 아래 말풍선

    @property
    def current_player(self):          # 지금 차례인 사람 (A·B가 부르는 이름은 그대로)
        return self.turns.current

    @property
    def opponent(self):                # 상대
        return self.turns.opponent

    def end_turn(self):
        """한 차례가 끝났을 때. 순서: ① 승리 조건 → ② 더블 → ③ 다음 사람 → ④ 승리 조건(턴 다 씀)"""
        if self.check_win():
            return
        player = self.current_player
        if self.dice.is_double and player.rest_turns == 0:     # 학사경고에 갔으면 더블이어도 끝
            self.log(f"{player.name}: 더블이라 한 번 더!")
            self.change_state(RollState(self))
            return
        for skipped in self.turns.next():                      # 차례 넘기기는 TurnManager가
            self.log(f"{skipped.name}: 학사경고라 한 번 쉼")
        if self.check_win():
            return
        self.log(f"{self.current_player.name} 차례")
        self.change_state(RollState(self))

    def check_win(self):
        """승리 조건 목록을 돌며 check만 부른다. 조건이 몇 개든 이 코드는 그대로 (다형성)."""
        for condition in self.win_conditions:
            result = condition.check(self)
            if result:
                winner, reason = result
                self.change_state(GameOverState(self, winner, reason))
                return True
        return False

    # A의 칸이 부르는 메서드
    def ask_buy(self, tile):                   # 빈 땅 도착 (살 돈이 있는지는 칸이 이미 확인함)
        self.change_state(BuyState(self, tile))

    def ask_acquire(self, tile):               # 상대 땅에서 통행료를 낸 뒤
        self.change_state(AcquireState(self, tile))

    def move_player(self, p, steps, salary=True):
        """p를 steps칸 앞으로. 정문을 지나면 월급. 주사위 이동(MovingState)과 카드 이동이 같이 쓴다."""
        passed_start = p.move(steps, self.board.size)
        if salary and passed_start:
            p.receive(config.SALARY)
            self.log(f"{p.name}: 정문 통과, 월급 {config.SALARY:,}원")

    def move_player_to(self, p, i, salary):    # 플레이어 p를 i번 칸으로 옮기기 (카드가 부름)
        """앞으로 가서 i번 칸에 선다. 도착한 칸의 on_land()는 부르는 쪽(카드)이 정한다."""
        self.move_player(p, self.board.steps_between(p.position, i), salary)

    # ---------- 게임 루프 ----------
    def run(self):
        while self.running:                        # 무한 루프
            dt = self.clock.tick(config.FPS)       # 갱신 주기, 지난 시간(ms)
            for event in pygame.event.get():       # 이벤트 수집
                self.handle_event(event)
            self.state.update(dt)
            self.draw()
        pygame.quit()

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif self.players and self.card_popup.handle_event(event):
            pass                                   # 카드 그림이 떠 있으면 클릭은 그림을 닫는 데만 씀
        else:
            self.state.handle_event(event)         # User → Game → 상태

    def draw(self):
        # 그리는 순서는 Game이 정한다: 뒤에 그린 것이 위에 보인다
        if self.players:                           # 판이 있을 때만 (메인·게임 준비는 상태가 직접 그림)
            draw_background(self.screen, config.PLAY_BG_SHADE)   # 1) 배경
            self.board.draw(self.screen)           # 2) 판
            self._draw_pawns()                     # 3) 말
            self._update_panels()
            for info in self.infos:                # 4) 1P·2P 카드
                info.draw(self.screen)
            self.message_log.draw(self.screen)     # 5) 기록
            self.dice.draw(self.screen, config.DICE_CENTER)   # 6) 주사위·게이지 (모든 상태가 같이 씀)
            self.gauge.draw(self.screen)
            self._draw_turn_count()
        self.state.draw(self.screen)               # 7) 지금 상태가 자기 화면을 그림 (팝업, 메인 화면)
        if self.players:
            self.card_popup.draw(self.screen)      # 8) 황금열쇠 그림 (맨 위)
        pygame.display.flip()                      # 윈도우 업데이트

    def _draw_pawns(self):
        """말을 칸 아래쪽에 그린다 (1P 왼쪽, 2P 오른쪽)."""
        for i, p in enumerate(self.players):
            draw_pawn(self.screen, p.color, self.board.pawn_pos(p.position, i), 24)

    def _draw_turn_count(self):
        now = min(self.turns.count + 1, self.turns.max_turns)
        pill = pygame.Rect(config.TURN_PILL_RECT)
        pygame.draw.rect(self.screen, config.TURN_BG, pill, border_radius=pill.height // 2)
        pygame.draw.rect(self.screen, config.TURN_BORDER, pill, width=1, border_radius=pill.height // 2)
        draw_text(self.screen, f"턴 {now} / {self.turns.max_turns}",
                  get_font(config.FONT_BODY, 14), config.WHITE, pill.center)

    def _update_panels(self):
        """카드에 차례와 순위를 알려 준다 (카드는 보여주기만 한다). 총자산이 같으면 둘 다 1위."""
        for i, info in enumerate(self.infos):
            me, other = self.players[i], self.players[1 - i]
            info.is_turn = (me is self.current_player)
            info.rank = 1 if me.total_assets() >= other.total_assets() else 2
