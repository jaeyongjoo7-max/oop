# config.py : 모든 설정값. 숫자·색·파일 경로는 이 모듈에만 둔다.

# 화면
SCREEN_W = 1100
SCREEN_H = 760
FPS = 60                  # 1초에 화면을 60번 갱신
TITLE = "외대 마블"

# 색 (R, G, B) : 시안 값 그대로
NAVY = (19, 41, 75)       # 배경, 진한 글자
INK = (11, 26, 51)        # 테두리, 그림자
YELLOW = (255, 201, 60)   # 판 테두리, 굴리기 버튼, 강조
P1_RED = (214, 40, 57)    # 1P
P2_BLUE = (29, 78, 216)   # 2P
BAND_100 = (242, 140, 40) # 아랫줄 띠
BAND_150 = (31, 122, 77)  # 왼쪽 띠
BAND_200 = (14, 124, 134) # 윗줄 띠
BAND_250 = (115, 64, 184) # 오른쪽 띠
WHITE = (255, 255, 255)

# 게임 규칙 : 임시값, 팀 합의 후 확정
START_MONEY = 1500        # 시작 돈
SALARY = 200              # 정문을 지날 때 받는 월급
TOLL_RATE = 0.5           # 통행료 = 땅값 × 이 비율
MAX_TURNS = 40           # 턴 다 씀 판정 기준 (1턴 = 한 사람의 차례, 각자 20번)

# 연출 시간 (ms)
MOVE_TIME = 1000          # 임시: 이동 상태가 유지되는 시간
STEP_TIME = 150           # 말이 한 칸 이동하는 데 걸리는 시간

# 판 크기와 위치 (판 640x640을 화면 가운데에)
TILE_SIZE = 104
BOARD_BORDER = 8
BOARD_POS = (230, 60)

# 돈 규칙 (팀에서 정할 임시 값)
ACQUIRE_RATE = 2           # 인수 가격 = (땅값 + 건물값) × 2
ISLAND_REST_TURNS = 1      # 학사경고에서 쉬는 턴

# 칸 색
WHITE = (255, 255, 255)
TILE_BG = (255, 253, 247)
START_BG = (221, 242, 229)
START_TEXT = (31, 122, 77)
ISLAND_BG = (251, 225, 222)
ISLAND_TEXT = (181, 48, 44)
CHANCE_BG = (255, 233, 168)
CHANCE_TEXT = (138, 90, 0)
KEY_GOLD = (242, 183, 5)

# ----- A 추가 (11/18): 건물·황금열쇠 -----
# 건물 단계 (임시값, 팀 합의 후 확정. 지침서 4쪽 예시 기준)
# (이름, 짓는 값 = 땅값 × 이 배수, 통행료 배수). 맨 마지막 단계가 랜드마크(인수 불가)
BUILDING_STEPS = [
    ("별장", 0.5, 2),
    ("빌딩", 1.0, 4),
    ("호텔", 2.5, 7),
    ("랜드마크", 3.0, 10),
]
LANDMARK_GOLD = (242, 183, 5)   # 랜드마크 칸 금색 테두리

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
DIE_SIZE = 74
DIE_GAP = 20                 # 주사위 두 개 사이 간격
DIE_RADIUS = 17              # 모서리 둥글기
DIE_PADDING = 11             # 테두리 안쪽 여백
DIE_SHADOW = 6               # 아래 그림자 두께
PIP_RADIUS = 6               # 눈(점) 반지름
DICE_ROLL_TIME = 800         # 굴러가는 연출 시간 (ms)
DICE_FLIP_TIME = 70          # 굴러가는 동안 눈이 바뀌는 간격 (ms)

# 게이지 굴리기 (시안: 작은 수 2~6 · 중간 5~9 · 큰 수 8~12)
GAUGE_ZONES = [(2, 6), (5, 9), (8, 12)]
GAUGE_NAMES = ["작은 수", "중간", "큰 수"]
GAUGE_COLORS = [(255, 211, 154), (169, 229, 191), (181, 206, 255)]
GAUGE_TRIES = 3              # 구간에 들어올 때까지 최대 몇 번 다시 굴려 볼지
GAUGE_SWEEP_TIME = 900       # 빨간 표시가 끝에서 끝까지 가는 시간 (ms)
LONG_PRESS_TIME = 250        # 이보다 오래 누르면 게이지 굴리기 (ms)

# 폰트 (assets/fonts/ 에 TTF. 파일이 없으면 FONT_FALLBACK으로 대신)
FONT_LOGO = "assets/fonts/BlackHanSans-Regular.ttf"
FONT_BUTTON = "assets/fonts/Jua-Regular.ttf"
FONT_BODY = "assets/fonts/NotoSansKR-Bold.ttf"
FONT_FALLBACK = "malgungothic,applesdgothicneo,nanumgothic"

# UI 색 (시안)
BUTTON_HOVER = (255, 214, 102)
BUTTON_SHINE = (255, 233, 170)     # 버튼 위쪽 반사 줄
SUB_TEXT = (58, 74, 102)           # 패널 작은 글자
COIN_RIM = (201, 148, 0)           # 동전 안쪽 테
LOG_OLD_BG = (47, 67, 97)          # 지난 기록 말풍선
LOG_OLD_BORDER = (58, 90, 140)
LOG_OLD_TEXT = (220, 230, 245)
TINT_RATE = 0.88                   # 플레이어 색을 얼마나 밝게 할지 (패널 칸 배경)

# UI 위치·크기 (시안, 1100×760 기준)
MARGIN = 16
PANEL_WIDTH = 196
PANEL_HEIGHT = 160
PANEL_HEAD = 56
P1_PANEL_POS = (MARGIN, SCREEN_H - MARGIN - PANEL_HEIGHT)     # 왼쪽 아래
P2_PANEL_POS = (SCREEN_W - MARGIN - PANEL_WIDTH, MARGIN + 16)       # 오른쪽 위
LOG_POS = (SCREEN_W - MARGIN, SCREEN_H - MARGIN)          # 기록 오른쪽 아래 끝
LOG_WIDTH = 196
LOG_HEIGHT = 32
LOG_GAP = 8
LOG_COUNT = 3
DICE_CENTER = (550, 345)           # 판 가운데 (550, 380) 근처
GAUGE_CENTER = (550, 410)
GAUGE_WIDTH = 310
GAUGE_HEIGHT = 32
ROLL_BUTTON_CENTER = (550, 480)
ROLL_BUTTON_SIZE = (270, 62)
BUTTON_SHADOW = 7