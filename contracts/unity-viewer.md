# Unity 샘플 뷰어 계약 (F10)

업무 API·인증과 무관한 정적 빌드다. 토큰이나 업무 데이터를 Unity에 전달하지 않는다.

## 버전과 빌드

- Unity 6000.5.10f1 (`unity/ShipyardViewer/ProjectSettings/ProjectVersion.txt`), Web Build Support 필요. 6000.3.23f1에는 이 모듈이 없다.
- 렌더 파이프라인: Built-in, 그래픽 API: WebGL2, 압축: Disabled.
- 씬·재질은 `Assets/Editor/BuildViewer.cs`가 매번 재생성하고, 선박 메시는 런타임에 코드로 만든다.

```bash
/Applications/Unity/Hub/Editor/6000.5.10f1/Unity.app/Contents/MacOS/Unity -batchmode -quit \
  -projectPath "$PWD/unity/ShipyardViewer" -buildTarget WebGL \
  -executeMethod BuildViewer.Build -logFile /tmp/unity-build.log
```

저장소 루트에서 실행한다. 같은 프로젝트를 Editor로 열어 둔 상태에서는 실행할 수 없다.

## 출력

`frontend/public/unity/ship-viewer/Build/` — 로더·framework·data·wasm과 `build.json`.

`build.json`은 빌드 스크립트가 실제 파일에서 생성하는 매니페스트이며, Vue는 파일명을 하드코딩하지 않고 이 파일을 읽는다.
필드: `loaderUrl`, `dataUrl`, `frameworkUrl`, `codeUrl`(Build 폴더 기준 상대), `companyName`, `productName`, `productVersion`.

## 메시지

| 방향 | 경로 | 내용 |
| --- | --- | --- |
| Vue → Unity | `instance.SendMessage('ShipViewer', 'SetView', view)` | `view`: `front` / `side` / `top` / `reset` |
| Unity → Vue | canvas의 `shipviewer-ready` CustomEvent | 첫 프레임 렌더 후 1회 (`ViewerBridge.jslib`) |

`createUnityInstance`가 끝나도 씬 준비 전일 수 있으므로, 시점 버튼은 두 신호가 모두 도착한 뒤에 활성화한다.

## 수명주기 (`frontend/src/components/unityRuntime.js`)

- canvas에는 **id가 반드시 있어야 한다.** Unity 런타임이 `'#' + canvas.id`로 조회하며, 없으면 시작 단계에서 실패한다.
- 로더 스크립트는 첫 진입에서 한 번만 불러온다. 실패하면 태그를 제거해 재시도할 수 있게 한다.
- 인스턴스는 동시에 하나만 둔다. 새 시작은 이전 인스턴스의 로딩 완료·`Quit()`까지 기다린다(`createUnityInstance`는 취소할 수 없다).
- 로딩 중 닫으면 늦게 도착한 인스턴스를 바로 `Quit()`한다. 종료 후 WebGL 컨텍스트를 해제한다.
- 재시도는 새 canvas를 쓴다. 준비 신호가 20초 안에 오지 않으면 실패로 처리한다.
- 오류 표시는 `config.showBanner`로 받는다(공식 매뉴얼에는 없고 6000.5 로더 코드에서 확인). 버전을 올릴 때 다시 확인한다.
- `WebGLInput.captureAllKeyboardInput = false`로 Esc와 입력 폼의 키를 페이지에 남긴다.

## 호선 상세 연동

`3D 보기`는 호선 상세의 서브탭이다(신규 등록 시 없음). 탭에 들어갈 때 Unity를 시작하고 탭이나 모달을 떠나면 종료한다. 3D 탭에서는 모달이 `xl`로 넓어진다. 3D 탭은 데이터가 없으므로, 직전 데이터 탭으로 돌아올 때는 재조회하지 않아 작성 중인 내용이 유지된다. 모달이 하나뿐이므로 Esc는 호선 상세를 닫는다.

## 배포

- 로컬은 압축 없이 Vite 정적 제공으로 동작한다. `.wasm`은 `Content-Type: application/wasm`이 필요하다.
- 압축을 켜면 서버가 `Content-Encoding: gzip` 또는 `br`과 올바른 Content-Type을 함께 보내야 하며, 실제 서버에서 다시 검증해야 한다(미검증).
