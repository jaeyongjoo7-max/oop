# 파일별 객체지향 요소 대본 (11/26 수정본 기준)

기준 코드: 11/26 수정본(`hufs_marble_수정본_11월26일.zip`). 강의 용어 그대로, 패턴 이름은 "강의 범위 밖"이라고 표시했다.
각 파일마다 **① 클래스 → ② 객체지향 요소 표 → ③ 말할 대본 → ④ 외울 키워드** 순서. 대본은 파일 하나에 20~30초.

---

## 한눈에 보기: 어느 파일에서 무엇을 보여 주나

| 요소 (강의) | 대표 파일 | 한 줄 |
|---|---|---|
| 추상화 (6강) | tiles.py, player.py, states.py, win_conditions.py | 부모가 "꼭 가질 메서드"만 정하고 객체로 못 만든다 |
| 캡슐화 (6강) | player.py, turns.py, dice.py | 값은 밑줄로 숨기고, 바꾸는 문(메서드)만 연다 |
| 상속·재사용 (5강) | states.py(PopupState), cards.py, win_conditions.py | 부모에 실제 코드를 두고 자식은 물려받는다 |
| 다형성 (5강) | tiles.py, player.py, states.py, win_conditions.py | 같은 이름을 불러도 객체마다 다르게 움직인다 |
| 클래스 하나·객체 여러 개 (4강) | cards.py, buildings.py, ui.py(Button) | 데이터만 다르면 클래스를 새로 만들지 않는다 |
| 클래스 변수 (4강) | dice.py(PIPS), cards.py(_image_cache) | 모든 객체가 같이 쓰는 값 |
| 컴포지션 | game.py, board.py, dice.py | 객체가 다른 객체를 가지고 쓴다 |
| 모듈 (2강) | ui.py, config.py | 다른 파일에서 불러 쓴다 |
| User ↔ Client ↔ 객체 (6강·8강 과제) | game.py, states.py | 클릭 → Game → 상태 → 객체 |

---

# A · 판과 규칙

## board.py

**클래스:** Board

| 요소 | 코드 |
|---|---|
| 컴포지션 | Board가 칸 객체 20개(`self.tiles`)를 가진다 |
| 팩토리 (강의 범위 밖) | `TILE_TYPES` + `config.BOARD_LAYOUT`: 표 한 줄을 보고 칸 객체를 만든다 |
| 캡슐화 | `size`, `side_len`, `pixel_size`, `center_rect`는 `@property`로 읽기만 |
| 다형성 | `draw()`가 칸 종류를 묻지 않고 `tile.draw()`만 부른다 |
| 재사용 | 한 바퀴 도는 계산 `steps_between`, 말 위치 `pawn_pos`를 한 곳에 두고 Game·카드·테스트가 같이 쓴다 |

**대본**
> board.py의 Board는 판 하나입니다. 판은 칸 객체 20개를 가지고 있습니다. 칸은 직접 하나씩 만들지 않고, config에 있는 배치 표를 한 줄씩 읽어서 만듭니다. 그래서 새 칸 종류가 생기면 표에 한 줄만 추가하면 됩니다. 판을 그릴 때도 칸 종류를 묻지 않고 각 칸의 draw만 부릅니다. 판을 한 바퀴 도는 계산과 말을 세울 위치는 Board 한 곳에만 두고, 게임과 카드가 가져다 씁니다.

**외울 키워드:** 칸 20개를 가짐 / 배치 표 한 줄 = 칸 하나 / draw만 부름 / 한 바퀴 계산은 판이 안다

## tiles.py

**클래스:** Tile(추상), StartTile, IslandTile, ChanceTile, PropertyTile

| 요소 | 코드 |
|---|---|
| 추상화 | `Tile(ABC)`, `on_land`는 `@abstractmethod` → 모든 칸이 꼭 가진다 |
| 상속·재사용 | `super().__init__(index, name)`, 정문·학사경고가 부모의 `_draw_special()`을 같이 씀 |
| 다형성 | `on_land(player, game)`: 칸마다 다른 일 |
| 캡슐화 | 통행료·인수가는 `@property toll`, `acquire_price` 한 곳에서만 계산. 학사경고는 `player.start_rest()`로만 쉬는 턴을 정함 |
| 재사용 | 통행료 상승 `raise_toll()`은 buildings.py의 단계 데이터를 그대로 씀. 글자 도구는 ui.py 것을 씀 |

**대본**
> tiles.py는 칸입니다. 모든 칸의 부모 Tile은 추상 클래스라서, 모든 칸이 on_land를 꼭 가집니다. 정문, 학사경고, 황금열쇠, 땅은 on_land를 각자 다르게 채웠습니다. 그래서 게임은 tile.on_land 한 줄만 부르면 됩니다. 통행료와 인수 가격은 property 한 곳에서만 계산해서, 규칙이 바뀌어도 그 한 곳만 고칩니다. 자기 땅에 다시 오면 통행료가 오르는 규칙도 새 변수를 만들지 않고 단계 객체를 다시 썼습니다.

**외울 키워드:** Tile 추상 / on_land 각자 / 한 줄만 부름 / 통행료는 한 곳 / 단계 객체 재사용

## buildings.py

**클래스:** Building, Landmark(Building) + 함수 `make_building()`

| 요소 | 코드 |
|---|---|
| 클래스 하나·객체 여러 개 | 별장·빌딩·호텔은 이름과 배수만 다름 → Building 객체 3개 |
| 상속 | 랜드마크는 "인수 불가"라는 행동이 다름 → Landmark 클래스 |
| 오버라이딩 + `super()` | `Landmark.draw()`가 금색 테두리를 더하고 `super().draw()`로 집 아이콘은 부모 것 재사용 |
| 다형성 | 땅은 `building.can_be_acquired()`만 물어본다 |

**대본**
> buildings.py는 통행료 단계입니다. 별장, 빌딩, 호텔은 이름과 통행료 배수만 달라서 클래스를 셋 만들지 않고 Building 객체 셋으로 만들었습니다. 랜드마크만 인수할 수 없다는 행동이 달라서 상속했습니다. 랜드마크는 금색 테두리만 더 그리고, 집 아이콘은 super로 부모 것을 그대로 씁니다. 저희 팀 기준인 "행동이 다르면 상속, 데이터만 다르면 객체"를 보여 주는 파일입니다.

**외울 키워드:** 데이터만 다름 = 객체 셋 / 행동이 다름 = Landmark / super().draw / 팀 기준 한 문장

## cards.py

**클래스:** ChanceCard(추상), MoneyCard, MoveCard, CardDeck, CardPopup

| 요소 | 코드 |
|---|---|
| 추상화 | `ChanceCard.execute()`는 추상 메서드 |
| 상속·재사용 | 제목·설명·그림(`__init__`)과 기록 남기기(`log_effect`)는 부모에만 있고 자식은 물려받음 |
| 클래스 하나·객체 여러 개 | MoneyCard 1개로 8장, MoveCard 1개로 2장 → **클래스 2개로 카드 10장** |
| 다형성 | 황금열쇠 칸은 카드 종류를 모르고 `card.execute()`만 부름. 커맨드 패턴 (강의 범위 밖) |
| 캡슐화 | CardDeck의 `_draw_pile`, `_discard`는 숨기고 `draw()`, `shuffle()` 문만 엶 |
| 클래스 변수 | `CardPopup._image_cache`: 한 번 불러온 카드 그림을 모든 팝업이 같이 씀 (4강) |

**대본**
> cards.py는 황금열쇠입니다. 모든 카드의 부모 ChanceCard에는 제목, 설명, 그림과 기록 남기는 코드가 있고, 자식 카드는 이걸 물려받아 씁니다. 돈을 내거나 받는 카드는 금액만 다르니 MoneyCard 하나로 여덟 장, 칸을 옮기는 카드는 갈 칸만 다르니 MoveCard 하나로 두 장을 만들었습니다. 클래스 두 개로 카드 열 장입니다. 황금열쇠 칸은 카드 종류를 몰라도 execute만 부르면 됩니다.

**외울 키워드:** 부모에 log_effect / MoneyCard 8장, MoveCard 2장 / 클래스 2개 = 카드 10장 / execute만

---

# B · 플레이어와 화면

## player.py

**클래스:** Player(추상), HumanPlayer, AIPlayer

| 요소 | 코드 |
|---|---|
| 추상화 | `Player(ABC)`: `decide_buy`, `decide_acquire`, `choose_roll`은 추상 메서드 |
| 캡슐화 | `_money`, `_position`, `_rest_turns`는 숨기고 getter만. 바꾸는 문은 `pay`·`receive`·`pay_to`·`move`·`start_rest`·`take_rest` |
| 상속·재사용 | 돈·위치·땅·쉬는 턴은 Player에만 있고 사람·AI가 물려받음. AI는 `super().__init__()` |
| 다형성 | 같은 `decide_buy`: 사람은 `WAIT`, AI는 바로 `True`/`False` |
| 클래스 하나·객체 여러 개 | `AIPlayer(…, safe_money=500)`: 남길 돈만 다른 AI는 객체로 만듦 |
| 재사용 | AI 판단 기준은 `_can_afford()` 한 곳, 사기·인수가 같이 씀 |

**대본**
> player.py는 플레이어입니다. 돈, 위치, 쉬는 턴은 모두 밑줄을 붙여 숨겼고, 밖에서는 볼 수만 있습니다. 돈은 pay와 receive로만, 위치는 move로만 바뀝니다. 사람과 AI는 이 코드를 한 줄도 다시 쓰지 않고 Player에게서 물려받았습니다. 다른 건 결정하는 방법뿐입니다. 같은 "살래?"에 사람은 버튼을 기다리고, AI는 300원 이상 남으면 바로 삽니다. AI의 판단 기준은 _can_afford 한 곳에 모았고, 성격이 다른 AI는 남길 돈만 바꿔 객체로 만듭니다.

**외울 키워드:** 밑줄 셋(돈·위치·쉬는 턴) / 문으로만 / 한 줄도 다시 안 씀 / "살래?" 기다림 vs 바로 / _can_afford 한 곳 / 남길 돈 = 객체

## dice.py

**클래스:** Die, DiceSet

| 요소 | 코드 |
|---|---|
| 컴포지션 | DiceSet이 Die 객체 2개를 가짐 |
| 캡슐화 | `_result`, `_rolling`은 숨김. `total`, `values`, `is_double`, `is_rolling`은 getter만 |
| 다형성 | `roll(strategy)`: RandomRoll이든 GaugeRoll이든 똑같이 부름 |
| 클래스 변수 | `Die.PIPS`: 눈마다 점 자리. 모든 주사위가 같이 씀 (4강) |

**대본**
> dice.py는 주사위입니다. DiceSet은 주사위 객체 두 개를 가지고 있고, 각 주사위는 자기 모양만 그립니다. 굴린 결과는 숨겨 두고, 다른 사람은 합과 더블 여부를 읽기만 합니다. 굴리는 방법은 주사위가 정하지 않고 밖에서 객체로 넣어 줍니다. 짧게 누르든 꾹 누르든 주사위 코드는 똑같습니다.

**외울 키워드:** 주사위 두 개를 가짐 / 결과는 읽기만 / 굴리는 방법은 밖에서 넣어 줌

## roll_strategies.py

**클래스:** RollStrategy(추상), RandomRoll, GaugeRoll

| 요소 | 코드 |
|---|---|
| 추상화 | `roll_values()`는 추상 메서드 |
| 다형성 | 두 방법 모두 `roll_values()`로 (a, b)를 돌려줌 |
| 전략 패턴 (강의 범위 밖) | 굴리는 방법을 객체로 갈아 끼움. 새 방법 = 클래스 하나 추가, 주사위 코드는 그대로 |

**대본**
> roll_strategies.py는 굴리는 방법입니다. 일반 굴리기와 게이지 굴리기는 같은 부모를 물려받아 같은 이름의 메서드를 가집니다. 굴리는 방법이 하나 더 생기면 이 파일에 클래스 하나만 추가하고, 주사위 코드는 고치지 않습니다. 이렇게 방법을 갈아 끼우는 구조를 전략 패턴이라고 부르는데, 강의 범위 밖 이름입니다.

**외울 키워드:** 같은 부모·같은 이름 / 새 방법 = 클래스 하나 / 주사위는 그대로 / 전략 패턴(범위 밖)

## ui.py

**클래스:** Button, RollGauge, MessageLog, PlayerInfo + 공통 도구(`get_font`, `draw_text`, `draw_shade`, `draw_pawn`)

| 요소 | 코드 |
|---|---|
| 9강 Button | normal / hover / active 상태에 따라 다르게 그림 |
| 클래스 하나·객체 여러 개 | Button 하나로 굴리기·사기·안 사기·인수·다시 하기 버튼 |
| 컴포지션 | RollGauge가 Button을 가지고 씀 |
| 모듈 재사용 (2강) | 글자·반투명 막 도구를 A·B·C가 모두 여기서 가져다 씀 (예전 3벌 → 1벌) |
| 캡슐화 | RollGauge의 `_holding`, `_marker`는 숨기고 `zone`은 읽기만 |
| 역할 나누기 | PlayerInfo는 게임 규칙을 모르고 보여주기만 함 |

**대본**
> ui.py는 화면 부품입니다. Button은 9강에서 배운 버튼처럼 마우스에 따라 모양이 바뀝니다. 이 Button 클래스 하나로 굴리기, 땅 사기, 인수, 다시 하기 버튼을 모두 만들었습니다. 글자를 그리는 도구도 원래 세 파일에 따로 있었는데, 이 모듈 하나로 모아서 판과 화면과 게임 흐름이 같이 씁니다. 패널은 게임 규칙을 모르고, 받은 값을 보여주기만 합니다.

**외울 키워드:** 9강 Button / 클래스 하나로 버튼 다섯 / 글자 도구 3벌 → 1벌 / 패널은 보여주기만

---

# C · 게임 흐름과 통합

## main.py · config.py

| 파일 | 요소 | 코드 |
|---|---|---|
| main.py | 모듈 (2강) | `Game()`을 만들고 `run()`만 부른다. 나머지는 모두 다른 모듈에 |
| config.py | 유지보수 (1강) | 숫자·색·파일 경로는 이 모듈에만. 게임 중에 바뀌지 않는 설정값 |

**대본**
> main.py는 게임 객체를 만들고 실행만 합니다. 숫자와 색은 config.py 한 모듈에 모아서, 값을 바꿀 때 이 한 곳만 고치면 세 사람 파일에 모두 반영됩니다.

**외울 키워드:** 만들고 실행만 / 숫자는 한 곳

## game.py

**클래스:** Game

| 요소 | 코드 |
|---|---|
| Client Program (6강) | 칸·플레이어·상태 객체를 만들고 부르는 쪽 |
| 컴포지션 | 판, 카드 더미, 주사위, 게이지, 기록, 패널, 턴 관리자, 승리 조건을 가짐 |
| 다형성 | `self.state.handle_event / update / draw`, `condition.check(game)`: 종류를 묻지 않음 |
| User ↔ Client ↔ 객체 | 클릭 → `Game.handle_event` → 지금 상태 → 객체 |
| 재사용 | `move_player()` 하나를 주사위 이동과 카드 이동이 같이 씀. `start(players)`로 새 판. 사람 vs 사람은 HumanPlayer 객체 하나 더 |
| 캡슐화 | `current_player`, `opponent`는 `@property`로 TurnManager에서 읽어 옴 |

**대본**
> game.py의 Game은 6강에서 배운 Client Program입니다. 사용자가 클릭하면 Game이 받아서 지금 상태 객체에게 넘기고, 상태가 칸이나 플레이어 객체를 부릅니다. Game은 지금 상태가 무엇인지, 승리 조건이 무엇인지 묻지 않고 같은 이름의 메서드만 부릅니다. 한 칸씩 옮기고 월급을 주는 코드는 move_player 하나라서, 주사위로 움직일 때와 카드로 움직일 때 같이 씁니다. 사람 대 사람 모드도 새 클래스 없이 사람 객체를 하나 더 만들면 됩니다.

**외울 키워드:** Client Program / 클릭 → Game → 상태 → 객체 / 묻지 않고 부르기만 / move_player 하나 / 사람 객체 하나 더

## turns.py (11/26 새로 만듦)

**클래스:** TurnManager

| 요소 | 코드 |
|---|---|
| 캡슐화 (6강) | `_players`, `_index`, `_count`는 숨김. `current`, `opponent`, `count`는 getter만 |
| 문은 하나 | 차례를 바꾸는 방법은 `next()` 하나뿐 |
| 객체끼리 메시지 (1강) | 쉬는 턴은 TurnManager가 직접 깎지 않고 `player.take_rest()`에게 물어봄 |
| 재사용 | `is_over()`를 Game과 TurnLimitWin이 같이 씀. 플레이어 수가 늘어도 그대로 |

**대본**
> turns.py의 TurnManager는 턴을 관리하는 객체입니다. 원래 누구 차례인지와 몇 턴째인지가 Game 안에 변수로 흩어져 있어서, 아무 데서나 바꿀 수 있었습니다. 지금은 이 객체 안에 숨겨 두고, 밖에서는 읽기만 합니다. 차례를 넘기는 문은 next 하나뿐이고, 넘길 때마다 턴을 하나 세고 쉬는 사람은 건너뜁니다. 쉬는 턴은 플레이어 안에 있으니 직접 건드리지 않고 플레이어에게 물어봅니다. 그래서 40턴이면 두 사람이 정확히 20번씩 합니다.

**외울 키워드:** 흩어진 변수 → 객체 하나 / 읽기만 / 문은 next 하나 / 쉬는 턴은 플레이어에게 묻기 / 20번씩

## states.py

**클래스:** GameState(추상), RollState, MovingState, PopupState(추상), BuyState, AcquireState, GameOverState

| 요소 | 코드 |
|---|---|
| 추상화 | 모든 상태는 `handle_event`, `update`, `draw`를 꼭 가짐 |
| 다형성 | Game은 지금 상태에게 같은 세 메서드만 부름 |
| 상태 패턴 (강의 범위 밖) | 참/거짓 변수 대신 단계마다 클래스. 9강 Button의 상태를 게임 전체로 넓힘 |
| 상속·재사용 (11/26) | PopupState에 흐름·버튼·그리기를 두고, 땅 사기·인수는 다른 세 가지만 채움 (BuyState 53줄 → 20줄) |
| 재사용 | 팝업 버튼은 B의 Button 객체 |

**대본**
> states.py는 게임의 단계입니다. 굴리기, 이동, 땅 사기, 인수, 게임 끝을 각각 클래스로 나눴고, 모두 같은 세 메서드를 꼭 가집니다. 중간발표 뒤에는 땅 사기와 인수 팝업이 거의 같다는 걸 보고, 공통 부모 PopupState를 만들었습니다. 화면을 어둡게 하고 버튼을 기다리는 흐름은 부모에 한 번만 있고, 자식은 묻는 글자, 누구에게 물을지, 고른 뒤 할 일만 채웁니다. 그래서 땅 사기 코드는 53줄에서 20줄로 줄었고, 인수 팝업은 같은 모양으로 금방 붙였습니다.

**외울 키워드:** 단계 = 클래스 / 세 메서드 / PopupState = 흐름은 부모 / 자식은 세 가지 / 53줄 → 20줄

## win_conditions.py (11/26 채움)

**클래스:** WinCondition(추상), BankruptcyWin, TurnLimitWin

| 요소 | 코드 |
|---|---|
| 추상화 | `check(game)`은 추상 메서드 |
| 다형성 | Game은 목록을 돌며 `check`만 부름 |
| 상속·재사용 | "가장 부자 찾기" `richest()`는 부모에 한 번만, 두 조건이 같이 씀 |
| 확장 (1강) | 새 승리 조건 = 클래스 하나 + 목록에 객체 하나. `end_turn`은 그대로 |

**대본**
> win_conditions.py는 승리 조건입니다. 파산과 턴 다 씀을 각각 클래스로 만들었고, 게임은 목록을 돌며 check만 부릅니다. 누가 가장 부자인지 찾는 코드는 두 조건 모두 필요해서 부모에 한 번만 적었습니다. 새 승리 조건이 생겨도 클래스 하나를 만들어 목록에 넣으면 되고, 턴을 끝내는 코드는 바꾸지 않습니다.

**외울 키워드:** 조건 = 클래스 / check만 / richest는 부모에 / 새 조건 = 클래스 하나

## board_demo.py (A 혼자 확인용, 게임에는 안 들어감)

| 요소 | 코드 |
|---|---|
| 약속된 메서드로만 만난다 | DemoGame이 Game과 같은 이름(`log`, `move_player_to`, `ask_buy` …)만 가지고 있어서, 칸·카드 코드를 한 줄도 안 고치고 그대로 테스트 |

**대본 (질문 받으면)**
> 판을 혼자 테스트할 때는 진짜 Game 대신, 같은 메서드 이름만 가진 작은 가짜 게임을 넣었습니다. 칸과 카드는 약속된 메서드만 부르기 때문에 상대가 진짜인지 몰라도 그대로 동작합니다.

---

## 예상 질문과 답변 방향

**Q1. 상속을 여기저기 썼는데, 재사용과 다형성 중 무엇을 위한 상속인지 구분할 수 있나요?**
→ 부모에 실제 코드가 있고 자식이 그걸 물려받아 쓰면 재사용입니다(PopupState의 흐름, ChanceCard의 log_effect, WinCondition의 richest, Player의 돈·위치). 부모에 이름만 있고 자식이 각자 채우면 다형성입니다(on_land, execute, check, decide_buy). PopupState처럼 둘 다인 경우도 있습니다.

**Q2. 턴 수를 TurnManager 안에 숨겼는데, 화면에 "턴 3 / 40"은 어떻게 보여 주나요?**
→ `count`를 getter로 열어 두어서 읽기만 합니다. 바꾸는 문은 `next()`뿐이라 화면 코드가 실수로 턴 수를 바꿀 수 없습니다.

**Q3. 클래스 변수(Die.PIPS, CardPopup._image_cache)는 왜 인스턴스 변수로 안 했나요?**
→ 주사위마다, 팝업마다 다를 이유가 없는 값이라 4강에서 배운 대로 모든 객체가 하나를 같이 씁니다. 인스턴스 변수로 하면 같은 값을 객체마다 따로 만들게 됩니다.
