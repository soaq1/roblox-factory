# 다른 컴퓨터에서 이어서 하기

집 컴퓨터처럼 새 컴퓨터에서 이 프로젝트를 이어받는 방법입니다.

## 설치할 것

| 프로그램 | 쓰임 | 받는 곳 |
|---|---|---|
| Git | 저장소 내려받기와 올리기 | git-scm.com |
| Claude Code | 코드 작업 | claude.com/claude-code |
| 로블록스 스튜디오 | 게임 열고 실행하기 | create.roblox.com |
| Blender | 모델을 다시 만들 때만 필요 | blender.org |

## 순서

1. 저장소를 내려받습니다.

   ```
   git clone https://github.com/soaq1/roblox-factory.git
   ```

2. 내려받은 `roblox-factory` 폴더에서 Claude Code를 엽니다.

3. Claude에게 이렇게 말합니다.

   > CLAUDE.md 읽고 이어서 하자. 도구부터 설치해 줘.

   Claude가 `CLAUDE.md`와 설계 문서를 읽고, 필요한 도구(Rokit, Rojo 등)를 설치하고, 게임 파일을 만들어 줍니다.

4. 만들어진 `game/build/roblox-factory.rbxlx`를 로블록스 스튜디오에서 열고 실행 버튼을 누릅니다.

5. 화면에 무엇이 보이는지, 출력 창에 빨간 글씨가 있는지를 Claude에게 알려 줍니다.

## 올리기 위한 준비

집 컴퓨터에서 고친 것을 깃허브에 올리려면 그 컴퓨터에서도 깃허브 로그인이 필요합니다. Claude에게 "깃허브 로그인 도와줘"라고 하면 안내해 줍니다.

## 맥과 윈도우의 차이

- 설계 문서의 Blender 명령은 맥 기준입니다. 윈도우에서는 Blender 실행 파일의 경로가 다르고, Claude가 알아서 맞춥니다.
- 그 밖의 도구(Rojo, Lune 등)는 두 쪽 모두에서 같게 동작합니다.
