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
| 자동 시험 | `lune run tests/all.luau` |
| 코드 모양 정리 | `stylua src tests` |
| 흔한 실수 검사 | `selene src` |
| 스튜디오와 실시간 연결 | `rojo serve default.project.json` (스튜디오에서 Rojo 플러그인의 Connect를 누름) |

만든 `build/roblox-factory.rbxlx`를 스튜디오에서 열고 실행하면 됩니다.

## 조작

| 입력 | 동작 |
|---|---|
| 1~9, 0 | 아이템 바의 열 칸 고르기. 고른 것이 손에 들림 |
| 좌클릭 | 손에 든 것 쓰기: 블록·기계는 놓기, 도구는 부수기(누르고 있으면 계속), 그 밖의 아이템은 떨어뜨리기 |
| R | 기계 방향 돌리기 |
| E / B / C / T / V | 놓을 것 목록 / 가방 / 조합 / 거래 / 다른 섬 구경 |
| F | 포탈, 상인, 기계 설정, 상자 꺼내기, 가까운 아이템 줍기 |
| 채팅 `/mode creative` | 무엇이든 무한히 놓는 시험 모드. `/mode survival`로 되돌림 |
| 채팅 `/give 철주괴 50` | 가방에 넣기(크리에이티브에서만) |
| 채팅 `/speed 5`, `/wipe` | 추출기와 식물 5배속, 굴러다니는 아이템 지우기 |

나머지 채팅 명령과 해 볼 순서는 [베타판 설계](../docs/specs/2026-10-05-beta.md)에 있습니다.

## 폴더

- `src/shared`: 서버와 클라이언트가 함께 쓰는 정의와 계산. 로블록스 기능을 쓰지 않는 부분은 스튜디오 없이 시험합니다. `Defs.luau`, `Recipes.luau`, `ModelPalette.luau`, `Models/`는 `tools/gen_data.py`가 만드는 파일이라 손으로 고치지 않습니다.
- `tools`: 모델과 레시피를 게임 자료로 바꾸는 스크립트
- `src/server`: 섬, 놓기와 부수기, 아이템, 기계, 저장
- `src/client`: 입력과 화면
- `tests`: 자동 시험. `run.luau`가 핵심, `<이름>_test.luau`가 각 시스템. `all.luau`가 전부 돌림
