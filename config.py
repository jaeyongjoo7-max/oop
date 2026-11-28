# config.py : 모든 설정값. 숫자·색·파일 경로는 이 모듈에만 둔다.

# 화면
SCREEN_W = 1100
SCREEN_H = 760
FPS = 60                  # 1초에 화면을 60번 갱신
TITLE = "외대 마블"

# 색 (R, G, B) : 11/29 최종 시안 (네이비 #102848, 진한 테두리 #091A33, 아이보리 #FFF2DB, 골드 #FFC342)
NAVY = (16, 40, 72)       # 배경, 진한 글자
INK = (9, 26, 51)         # 테두리, 그림자
IVORY = (255, 242, 219)   # 패널·카드 바탕 (지침서에 없는 새 이름)
GOLD = (255, 195, 66)     # 강조 버튼 (지침서에 없는 새 이름)
YELLOW = GOLD             # 예전 이름 그대로 쓰는 곳이 많아서 같은 색으로 둔다
P1_RED = (190, 50, 66)    # 1P
P2_BLUE = (46, 98, 182)   # 2P
BAND_100 = (181, 101, 43) # 아랫줄 띠
BAND_150 = (51, 116, 91)  # 왼쪽 띠
BAND_200 = (35, 119, 133) # 윗줄 띠
BAND_250 = (112, 81, 155) # 오른쪽 띠
WHITE = (255, 255, 255)

# 게임 규칙 : 임시값, 팀 합의 후 확정
START_MONEY = 1500        # 시작 돈
SALARY = 200              # 정문을 지날 때 받는 월급
TOLL_RATE = 0.5           # 통행료 = 땅값 × 이 비율
MAX_TURNS = 40            # 턴 다 씀 판정 기준 (1턴 = 한 사람의 차례, 각자 20번)

# 연출 시간 (ms)
MOVE_TIME = 1000          # 임시: 이동 상태가 유지되는 시간
STEP_TIME = 150           # 말이 한 칸 이동하는 데 걸리는 시간

# 판 크기와 위치 (판 640x640을 화면 가운데에)
TILE_SIZE = 104
BOARD_BORDER = 8
BOARD_POS = (230, 60)

# 돈 규칙 (11/26 추천안)
ACQUIRE_RATE = 2           # 인수 가격 = 땅값 × 2
ISLAND_REST_TURNS = 1      # 학사경고에서 쉬는 턴

# 칸 색
TILE_BG = (255, 250, 238)
START_BG = (224, 240, 224)
START_TEXT = (31, 122, 77)
ISLAND_BG = (247, 230, 222)
ISLAND_TEXT = (163, 52, 52)
ISLAND_SUB = (110, 72, 66)
CHANCE_BG = (255, 230, 168)
CHANCE_TEXT = (122, 83, 21)
KEY_GOLD = (242, 183, 5)
TILE_GAP = 4               # 칸 사이 틈 (판 바탕 INK가 보여서 칸이 나뉘어 보임)
TILE_RADIUS = 5

# ----- A 추가 (11/18): 통행료 단계·황금열쇠 -----
# 통행료 단계 (11/22: 건물 짓기 대신, 자기 땅에 다시 오면 공짜로 한 단계씩 오른다)
# 통행료 배수. 0단계(기본) = 1배, 맨 마지막 단계가 최대(인수 불가)
TOLL_STEPS = [1, 2, 4, 7, 10]
MAX_TOLL_GOLD = (242, 183, 5)   # 최대 단계 칸 금색 테두리

# 황금열쇠 카드
CARD_IMAGE_DIR = "assets/images/cards"
CARD_AMOUNTS = {                # 카드 금액 (원)
    "tuition": 200,             # 등록금 납부
    "f_grade": 100,             # F학점 멘탈치료비
    "kospi": 150,               # 코스피 급락
    "hangover": 50,             # 과음의 대가
    "assignment": 50,           # 과제폭탄 (지침서: -50)
    "dept_fee": 30,             # 과회비 징수
    "sports_win": 150,          # 왕산체전 우승 상금
    "scholarship": 100,         # 장학금 (지침서: +100)
}
CARD_POPUP_MS = 2500            # 카드 그림이 저절로 닫히기까지 (ms)
CARD_POPUP_ANIM_MS = 250        # 카드 그림이 튀어나오는 시간 (ms)
CARD_SHADE = (0, 0, 0, 140)     # 카드가 뜰 때 판 가운데를 어둡게
CARD_TEXT_BG = IVORY            # 카드 설명 상자 (팝업과 같은 아이보리)
CARD_TEXT_COLOR = INK
CARD_TEXT_BORDER = GOLD
CARD_HINT_TEXT = (220, 226, 236)
CARD_PLACEHOLDER_BG = (250, 210, 80)       # 그림 파일이 없을 때 대신 그리는 카드
CARD_PLACEHOLDER_BORDER = (150, 100, 20)
CARD_PLACEHOLDER_TEXT = (60, 40, 10)
# ----- A 추가 끝 -----

# 구매 표시
OWNER_TINT_ALPHA = 45      # 주인 색으로 칸을 옅게 칠하는 정도 (0~255)
FLASH_MS = 900             # 사거나 지었을 때 반짝이는 시간 (ms)

# 판 배치 표: 0번 = 정문, 진행 방향(정문에서 왼쪽) 순서
BOARD_LAYOUT = [
    ("start", "정문"),
    ("land", "기숙사", 100, BAND_100),
    ("land", "백년관", 100, BAND_100),
    ("chance", "황금열쇠"),
    ("land", "자연과학관", 100, BAND_100),
    ("land", "공학관", 100, BAND_100),
    ("land", "세향관", 150, BAND_150),
    ("land", "도서관", 150, BAND_150),
    ("chance", "황금열쇠"),
    ("land", "학생회관", 150, BAND_150),
    ("island", "학사경고"),
    ("land", "후생관", 200, BAND_200),
    ("land", "명수당", 200, BAND_200),
    ("chance", "황금열쇠"),
    ("land", "어문관", 200, BAND_200),
    ("land", "교양관", 200, BAND_200),
    ("land", "교수연구동", 250, BAND_250),
    ("land", "인문경상관", 250, BAND_250),
    ("chance", "황금열쇠"),
    ("land", "노천극장", 250, BAND_250),
]


AI_SAFE_MONEY = 300          # AI는 사고 나서 이만큼은 남아야 산다

# 주사위 (시안 크기)
DIE_SIZE = 70
DIE_GAP = 20                 # 주사위 두 개 사이 간격
DIE_RADIUS = 16              # 모서리 둥글기
DIE_PADDING = 11             # 테두리 안쪽 여백
DIE_SHADOW = 6               # 아래 그림자 두께
PIP_RADIUS = 6               # 눈(점) 반지름
DIE_COLOR = (255, 246, 230)  # 주사위 몸통 (아이보리)
DICE_ROLL_TIME = 800         # 굴러가는 연출 시간 (ms)
DICE_FLIP_TIME = 70          # 굴러가는 동안 눈이 바뀌는 간격 (ms)

# 게이지 굴리기 (시안: 작은 수 2–6 · 중간 5–9 · 큰 수 8–12)
GAUGE_ZONES = [(2, 6), (5, 9), (8, 12)]
GAUGE_NAMES = ["작은 수", "중간", "큰 수"]
GAUGE_COLORS = [(243, 212, 168), (188, 218, 200), (197, 218, 233)]
GAUGE_TRIES = 3              # 구간에 들어올 때까지 최대 몇 번 다시 굴려 볼지
GAUGE_SWEEP_TIME = 900       # 빨간 표시가 끝에서 끝까지 가는 시간 (ms)
LONG_PRESS_TIME = 250        # 이보다 오래 누르면 게이지 굴리기 (ms)

# 폰트 (assets/fonts/ 에 TTF. 파일이 없으면 FONT_FALLBACK으로 대신)
#   버튼·짧은 제목 = 주아, 설명·이름·금액·칸 이름 = Noto Sans KR Bold (요청서)
FONT_BUTTON = "assets/fonts/Jua-Regular.ttf"
FONT_BODY = "assets/fonts/NotoSansKR-Bold.ttf"
FONT_FALLBACK = "malgungothic,applesdgothicneo,nanumgothic"

# 그림 (시안 PNG에서 잘라 낸 고정 그림. 버튼·숫자는 그림에 없고 코드로 그린다)
IMAGE_DIR = "assets/images/ui"
BG_IMAGE = "assets/images/ui/bg_campus.png"        # 네이비 캠퍼스 (단풍 없음)
LOGO_IMAGE = "assets/images/ui/logo.png"           # 외대마블 로고 (메인·판 공용, 크기만 다름)
DECO_PAWNS_IMAGE = "assets/images/ui/deco_pawns.png"
DECO_DICE_IMAGE = "assets/images/ui/deco_dice.png"
LOGO_POS = (375, 62)           # 메인 로고 왼쪽 위
DECO_PAWNS_POS = (37, 586)     # 좌하단 빨강·파랑 말
DECO_DICE_POS = (882, 581)     # 우하단 주사위
BOARD_LOGO_WIDTH = 220         # 판 가운데 작은 로고 폭
BOARD_LOGO_CENTER = (550, 250)

# UI 색 (시안)
BUTTON_HOVER = (255, 210, 105)
BUTTON_SHINE = (255, 214, 120)     # 버튼 위쪽 반사 줄
LIGHT_BUTTON = (255, 250, 240)     # 밝은 버튼 (메인으로·취소·안 사기 …)
MENU_LIGHT_BUTTON = (253, 233, 196)  # 메인의 아이보리 버튼 (게임 방법·게임 종료)
LIGHT_HOVER = (255, 239, 205)
LIGHT_SHINE = (255, 252, 246)
SUB_TEXT = (74, 86, 110)           # 패널 작은 글자
DIVIDER = (215, 200, 174)          # 패널 안 구분선
PILL_BG = (241, 227, 200)          # 플레이어 카드의 '땅 0' 칸
COIN = (230, 169, 39)
COIN_RIM = (190, 128, 10)          # 동전 안쪽 테
CARD_IDLE_BORDER = (150, 165, 185) # 차례가 아닌 카드 테두리
PLAY_BG_SHADE = (12, 30, 56, 120)  # 플레이 화면 배경을 조금 어둡게
MENU_SHADE = (4, 12, 28, 165)      # 게임 준비·도움말·종료 확인 뒤를 어둡게
PANEL_RIM = (142, 119, 75)         # 패널 바깥 가는 골드 선
BOARD_CENTER_SHADE = (16, 40, 73, 200)   # 판 가운데 (뒤 풍경이 살짝 비침)
LOG_BG = (16, 35, 62)
LOG_BORDER = (78, 98, 128)
LOG_LABEL = (150, 165, 186)
LOG_OLD_TEXT = (170, 184, 204)
TURN_BG = (13, 32, 58)
TURN_BORDER = (78, 98, 128)

# UI 위치·크기 (시안, 1100×760 기준)
MARGIN = 22
PANEL_WIDTH = 190
PANEL_HEIGHT = 152
P1_PANEL_POS = (22, 578)           # 왼쪽 아래
P2_PANEL_POS = (888, 30)           # 오른쪽 위
LOG_RECT = (888, 674, 190, 54)     # 진행 기록 상자 (아래쪽 기준, 줄이 늘면 위로 커짐)
LOG_COUNT = 3                      # 보여 줄 기록 수
DICE_CENTER = (550, 352)
GAUGE_CENTER = (550, 420)
GAUGE_WIDTH = 328
GAUGE_HEIGHT = 34
ROLL_BUTTON_CENTER = (551, 487)
ROLL_BUTTON_SIZE = (270, 58)
BUTTON_SHADOW = 6
TURN_PILL_RECT = (492, 538, 116, 28)   # 판 가운데 아래 "턴 3 / 40"

# 팝업 (땅 사기·인수·게임 끝)
POPUP_SIZE = (440, 250)
POPUP_BUTTON_SIZE = (150, 48)
POPUP_SHADE = (4, 12, 28, 150)     # 팝업 뒤 화면을 어둡게 (R, G, B, 투명도)

# 메인 (11/29 최종 시안)
MENU_BUTTON_SIZE = (372, 64)
MENU_BUTTON_YS = [491, 576, 659]   # 게임 시작 / 게임 방법 / 게임 종료
MENU_FONT_SIZE = 38

# 게임 준비
SETUP_PANEL_RECT = (246, 280, 608, 418)
TOGGLE_SIZE = (254, 46)
NAME_BOX_SIZE = (452, 48)
NAME_BOX_BG = (255, 253, 248)
NAME_LINE = (176, 186, 200)        # 입력 중이 아닌 이름 칸 테두리
LOCKED_BG = (232, 232, 228)        # 잠긴 이름 칸 (AI)
LOCKED_LINE = (196, 196, 190)
LOCKED_TEXT = (90, 102, 124)
HINT_TEXT = (128, 138, 160)        # 이름 칸이 비었을 때 보이는 회색 글자
NAME_MAX_LEN = 6                   # 이름은 6글자까지 (카드 폭 190에 맞춤)

# 게임 방법 / 종료 확인
HELP_PANEL_RECT = (176, 170, 748, 533)
EXIT_PANEL_RECT = (306, 282, 488, 214)
ICON_BG = (243, 228, 200)
PANEL_BUTTON_RADIUS = 14         # 패널 안 버튼 모서리 (메인 버튼은 알약 모양)
