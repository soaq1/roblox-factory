# 게임 코드

로블록스 게임의 코드입니다. 지금 판에 무엇이 들어 있는지는 [베타판 설계](../docs/specs/2026-10-05-beta.md)에 있습니다.

**바로 해 보기**: `build/roblox-factory.rbxlx`를 로블록스 스튜디오에서 열고 실행(F5)합니다. 도구를 설치하지 않아도 됩니다.

## 필요한 것

- 로블록스 스튜디오
- [Rokit](https://github.com/rojo-rbx/rokit): 이 폴더에서 `rokit install`을 실행하면 `rokit.toml`에 적힌 도구(Rojo, Lune, StyLua, Selene, luau-lsp)가 설치됩니다.

## 명령

이 폴더(`game/`)에서 실행합니다.

| 하려는 일 | 명령 |
|---|---|
| 게임 파일 만들기 | `rojo build default.project.json -o build/roblox-factory.rbxlx` |
| 모델과 레시피를 게임 자료로 바꾸기 | `python3 tools/gen_data.py` (모델이나 레시피를 고친 뒤) |
| 자동 시험 | `lune run tests/run.luau` |
| 코드 모양 정리 | `stylua src tests` |
| 흔한 실수 검사 | `selene src` |
| 스튜디오와 실시간 연결 | `rojo serve default.project.json` (스튜디오에서 Rojo 플러그인의 Connect를 누름) |

만든 `build/roblox-factory.rbxlx`를 스튜디오에서 열고 실행하면 됩니다.

## 조작

| 입력 | 동작 |
|---|---|
| 우클릭 | 선택한 것을 놓기. 아이템을 골랐으면 그 자리에 8개를 떨어뜨림 |
| 좌클릭 | 부수기 |
| R | 기계의 방향 돌리기 |
| 1~9 | 단축 칸 고르기 |
| E | 목록 열기(블록 / 기계 / 아이템). 고른 것이 선택된 칸에 들어감 |
| F | 가까운 아이템 줍기, 상자에서 꺼내기 |
| 채팅 `/speed 5` | 추출기와 식물을 5배속으로 |
| 채팅 `/wipe` | 굴러다니는 아이템 모두 지우기 |
| 채팅 `/mode survival` | 생존 모드(가방에 있는 것만 놓음). `/mode creative`로 되돌림 |
| 채팅 `/can`, `/craft`, `/hand`, `/upgrade`, `/give` | 조합과 손 작업. 자세한 것은 [베타판 설계](../docs/specs/2026-10-05-beta.md)의 채팅 명령 표 |
| 채팅 `/trade`, `/offer`, `/coins`, `/ready`, `/cancel` | 플레이어 간 거래 |

## 폴더

- `src/shared`: 서버와 클라이언트가 함께 쓰는 정의와 계산. 로블록스 기능을 쓰지 않는 부분은 스튜디오 없이 시험합니다. `Defs.luau`, `Recipes.luau`, `ModelPalette.luau`, `Models/`는 `tools/gen_data.py`가 만드는 파일이라 손으로 고치지 않습니다.
- `tools`: 모델과 레시피를 게임 자료로 바꾸는 스크립트
- `src/server`: 섬, 놓기와 부수기, 아이템, 기계, 저장
- `src/client`: 입력과 화면
- `tests`: 자동 시험
