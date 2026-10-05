# 게임 코드

로블록스 게임의 코드입니다. 무엇을 만드는지는 [첫 실행판 설계](../docs/specs/2026-10-05-first-playable.md)에 있습니다.

## 필요한 것

- 로블록스 스튜디오
- [Rokit](https://github.com/rojo-rbx/rokit): 이 폴더에서 `rokit install`을 실행하면 `rokit.toml`에 적힌 도구(Rojo, Lune, StyLua, Selene, luau-lsp)가 설치됩니다.

## 명령

이 폴더(`game/`)에서 실행합니다.

| 하려는 일 | 명령 |
|---|---|
| 게임 파일 만들기 | `rojo build default.project.json -o build/roblox-factory.rbxlx` |
| 자동 시험 | `lune run tests/run.luau` |
| 코드 모양 정리 | `stylua src tests` |
| 흔한 실수 검사 | `selene src` |
| 스튜디오와 실시간 연결 | `rojo serve default.project.json` (스튜디오에서 Rojo 플러그인의 Connect를 누름) |

만든 `build/roblox-factory.rbxlx`를 스튜디오에서 열고 실행하면 됩니다.

## 조작

| 입력 | 동작 |
|---|---|
| 우클릭 | 선택한 것을 놓기 |
| 좌클릭 | 부수기 |
| R | 기계의 방향 돌리기 |
| 1~9 | 단축 칸 고르기 |
| E | 목록 열기. 고른 것이 선택된 칸에 들어감 |
| F | 가까운 아이템 줍기, 상자에서 꺼내기 |
| 채팅 `/speed 5` | 추출기를 5배속으로 |
| 채팅 `/clear` | 굴러다니는 아이템 모두 지우기 |

## 폴더

- `src/shared`: 서버와 클라이언트가 함께 쓰는 정의와 계산. 로블록스 기능을 쓰지 않는 부분은 스튜디오 없이 시험합니다.
- `src/server`: 섬, 놓기와 부수기, 아이템, 기계, 저장
- `src/client`: 입력과 화면
- `tests`: 자동 시험
