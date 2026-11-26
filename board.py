"""외대 마블 판: 배치 표로 칸 20개를 만들고, 칸 위치를 계산하고, 판을 그린다."""
import pygame

import config
from tiles import ChanceTile, IslandTile, PropertyTile, StartTile
from ui import draw_text, get_font


class Board:
    # 배치 표의 종류 이름 → 칸 클래스 (팩토리)
    # 새로운 칸이 생기면 클래스를 만들고 여기에 한 줄만 추가하면 된다.
    TILE_TYPES = {
        "start": StartTile,
        "island": IslandTile,
        "chance": ChanceTile,
        "land": PropertyTile,
    }

    def __init__(self, layout=None):
        layout = layout or config.BOARD_LAYOUT
        if len(layout) % 4 != 0:
            raise ValueError("칸 수는 4의 배수여야 네모난 판이 돼요")
        self.tiles = [self._make_tile(i, entry) for i, entry in enumerate(layout)]
        self.x, self.y = config.BOARD_POS
        self.tile_size = config.TILE_SIZE
        self.border = config.BOARD_BORDER

    def _make_tile(self, index, entry):
        kind, name, *extra = entry          # 예: ("land", "기숙사", 100, BAND_100)
        tile_class = self.TILE_TYPES[kind]
        return tile_class(index, name, *extra)

    # ----- 다른 사람이 쓰는 정보 -----
    @property
    def size(self):
        """칸 수 (20)."""
        return len(self.tiles)

    @property
    def side_len(self):
        """한 변에서 모서리 하나를 뺀 칸 수 (5)."""
        return self.size // 4

    @property
    def pixel_size(self):
        """판 전체 너비 = 높이 (640)."""
        return self.tile_size * (self.side_len + 1) + self.border * 2

    @property
    def center_rect(self):
        """칸으로 둘러싸인 가운데 빈 곳 (주사위·게이지·버튼 자리)."""
        start = self.border + self.tile_size
        width = self.tile_size * (self.side_len - 1)
        return pygame.Rect(self.x + start, self.y + start, width, width)

    def get_tile(self, index):
        return self.tiles[index % self.size]

    def steps_between(self, start, end):
        """start번 칸에서 end번 칸까지 앞으로 몇 칸인지.
        판을 한 바퀴 도는 계산(% size)은 판이 안다 (카드가 말을 옮길 때 Game이 씀)."""
        return (end - start) % self.size

    def grid_pos(self, index):
        """칸 번호 → (행, 열). 0번(정문)이 오른쪽 아래, 진행 방향은 왼쪽."""
        n = self.side_len
        side, k = divmod(index % self.size, n)
        if side == 0:
            return n, n - k      # 아랫줄: 오른쪽 → 왼쪽
        if side == 1:
            return n - k, 0      # 왼쪽 줄: 아래 → 위
        if side == 2:
            return 0, k          # 윗줄: 왼쪽 → 오른쪽
        return k, n              # 오른쪽 줄: 위 → 아래

    def tile_rect(self, index):
        """칸 번호 → 화면 위의 사각형 (말을 놓을 위치도 이걸로 계산)."""
        row, col = self.grid_pos(index)
        return pygame.Rect(self.x + self.border + col * self.tile_size,
                           self.y + self.border + row * self.tile_size,
                           self.tile_size, self.tile_size)

    def pawn_pos(self, index, slot):
        """index번 칸에 선 말의 발 위치. slot 0(1P)은 왼쪽, 1(2P)은 오른쪽.
        말을 그리는 곳(Game, board_demo)이 모두 이걸 쓴다."""
        rect = self.tile_rect(index)
        x = rect.x + 24 if slot == 0 else rect.right - 24
        return x, rect.bottom - 10

    def tile_at(self, pos):
        """화면 좌표 → 그 자리의 칸 (없으면 None). 칸을 클릭할 때 쓸 수 있다."""
        for tile in self.tiles:
            if self.tile_rect(tile.index).collidepoint(pos):
                return tile
        return None

    def lines(self):
        """네 변의 땅 목록 (한 줄 독점 승리를 만들 때 쓸 수 있다. MonopolyWin은 11/26에 빼기로 함).
        각 변 = 그 변의 가운데 칸들 + 변이 끝나는 모서리."""
        n = self.side_len
        result = []
        for side in range(4):
            indexes = range(side * n + 1, side * n + n + 1)
            result.append([self.get_tile(i) for i in indexes
                           if isinstance(self.get_tile(i), PropertyTile)])
        return result

    def find_tile(self, tile_class):
        """그 종류의 첫 칸 (예: board.find_tile(IslandTile)). 카드가 이동할 칸을 찾을 때 쓴다.
        칸 번호를 숫자로 적어 두지 않으므로 배치 표가 바뀌어도 카드를 고치지 않아도 된다."""
        for tile in self.tiles:
            if isinstance(tile, tile_class):
                return tile
        return None

    # ----- 그리기 -----
    def draw(self, surface):
        outer = pygame.Rect(self.x, self.y, self.pixel_size, self.pixel_size)
        pygame.draw.rect(surface, config.YELLOW, outer, border_radius=14)
        pygame.draw.rect(surface, config.INK, outer.inflate(-self.border * 2, -self.border * 2))
        pygame.draw.rect(surface, config.NAVY, self.center_rect)
        self._draw_logo(surface)
        for tile in self.tiles:
            tile.draw(surface, self.tile_rect(tile.index))   # 칸마다 자기 모양대로 (다형성)

    def _draw_logo(self, surface):
        center = self.center_rect
        logo_y = center.y + 70
        logo_font = get_font(config.FONT_LOGO, 56)
        draw_text(surface, "외대 마블", logo_font, config.INK, (center.centerx + 4, logo_y + 4))
        draw_text(surface, "외대 마블", logo_font, config.YELLOW, (center.centerx, logo_y))
        draw_text(surface, "HUFS MARBLE", get_font(config.FONT_BODY, 15), config.WHITE,
                  (center.centerx, logo_y + 44))
