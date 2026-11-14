# game.py : 게임 루프, 상태 바꾸기, 그리는 순서
import pygame
import config
from states import RollState, GameOverState


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
        pygame.display.set_caption(config.TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.players = ["1P", "2P"]    # 임시: B의 Player 객체로 바꾼다
        self.turn_index = 0            # 지금 차례인 사람의 번호 (0 또는 1)
        self.turn_count = 0            # 지금까지 턴 수
        self.deck = None               # 임시: A의 CardDeck 객체로 바꾼다
        self.state = RollState(self)   # 현재 상태 객체 하나

    def change_state(self, new_state):
        self.state = new_state

    def log(self, msg):
        print(msg)                     # 임시: B의 MessageLog가 오면 바꾼다
    
    @property
    def current_player(self):          # 지금 차례인 사람
        return self.players[self.turn_index]

    @property
    def opponent(self):                # 상대
        return self.players[1 - self.turn_index]

    def next_player(self):
        self.turn_index = 1 - self.turn_index      # 0이면 1로, 1이면 0으로

    def end_turn(self):                # 턴 끝내기
        if self.turn_count >= config.MAX_TURNS:
            self.change_state(GameOverState(self, None, "턴 다 씀"))
            return
        self.turn_count += 1
        self.next_player()
        self.log(f"{self.current_player} 차례")
        self.change_state(RollState(self))

    # A의 칸·카드가 부르는 메서드. 지금은 이름만 있고, 합친 뒤에 채운다.
    def ask_buy(self, tile):                   # 빈 땅 도착: 살지 묻기
        self.log("ask_buy 호출됨")

    def ask_build(self, tile):                 # 내 땅 도착: 지을지 묻기
        self.log("ask_build 호출됨")

    def ask_acquire(self, tile):               # 상대 땅 도착: 인수할지 묻기
        self.log("ask_acquire 호출됨")

    def move_player_to(self, p, i, salary):    # 플레이어 p를 i번 칸으로 옮기기
        self.log("move_player_to 호출됨")

    def run(self):
        while self.running:                        # 무한 루프
            dt = self.clock.tick(config.FPS)       # 갱신 주기, 지난 시간(ms)
            for event in pygame.event.get():       # 이벤트 수집
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle_event(event) # User → Game → 상태
            self.state.update(dt)
            self.draw()
        pygame.quit()

    def draw(self):
        self.screen.fill(config.NAVY)              # 배경 채우기
        self.state.draw(self.screen)               # 지금 상태가 자기를 그림
        pygame.display.flip()                      # 윈도우 업데이트