"""board.py / tiles.py가 쓰는 config 값.

config.py는 C 담당이라, 아래 [A가 새로 요청하는 값]을 C에게 보내서 config.py에 넣어 달라고 하세요.
config.py가 아직 없으면 이 파일 이름을 config.py로 바꿔서 혼자 테스트할 때 써도 돼요.
"""

# ===== 지침서에 이미 정해진 값 (config.py에 있을 것) =====
SCREEN_W, SCREEN_H = 1100, 760
FPS = 60
NAVY = (19, 41, 75)
INK = (11, 26, 51)
YELLOW = (255, 201, 60)
P1_RED = (214, 40, 57)
P2_BLUE = (29, 78, 216)
BAND_100 = (242, 140, 40)
BAND_150 = (31, 122, 77)
BAND_200 = (14, 124, 134)
BAND_250 = (115, 64, 184)
FONT_LOGO = "assets/fonts/BlackHanSans-Regular.ttf"
FONT_BODY = "assets/fonts/NotoSansKR-Bold.ttf"

# ===== A가 새로 요청하는 값 =====
# 판 크기와 위치 (판 640x640을 화면 가운데에)
TILE_SIZE = 104
BOARD_BORDER = 8
BOARD_POS = (230, 60)

# 돈 규칙 (팀에서 정할 임시 값)
TOLL_RATE = 0.5            # 통행료 = 땅값 × 0.5 × 건물 배수
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

# 구매 표시
OWNER_TINT_ALPHA = 45      # 주인 색으로 칸을 옅게 칠하는 정도 (0~255)
FLASH_MS = 900             # 사거나 지었을 때 반짝이는 시간 (ms)

# 폰트 파일이 없을 때 대신 쓸 한글 폰트 (윈도우, 맥, 리눅스 순)
FALLBACK_FONTS = "malgungothic,applegothic,applesdgothicneo,nanumgothic,notosanscjkkr"

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
