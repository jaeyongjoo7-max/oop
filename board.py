"""외대 마블 판: 배치 표로 칸 20개를 만들고, 칸 위치를 계산하고, 판을 그린다."""
import pygame

import config
from tiles import ChanceTile, IslandTile, PropertyTile, StartTile, draw_text


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

    def tile_at(self, pos):
        """화면 좌표 → 그 자리의 칸 (없으면 None). 칸을 클릭할 때 쓸 수 있다."""
        for tile in self.tiles:
            if self.tile_rect(tile.index).collidepoint(pos):
                return tile
        return None

    def lines(self):
        """네 변의 땅 목록 (MonopolyWin이 한 줄 독점을 볼 때 쓴다).
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
        draw_text(surface, "외대 마블", 56, config.INK, (center.centerx + 4, logo_y + 4), config.FONT_LOGO)
        draw_text(surface, "외대 마블", 56, config.YELLOW, (center.centerx, logo_y), config.FONT_LOGO)
        draw_text(surface, "HUFS MARBLE", 15, config.WHITE, (center.centerx, logo_y + 44))
