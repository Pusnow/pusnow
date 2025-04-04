---
title: "KENS 리뉴얼 Part 2: 개발 환경과 빌드 시스템"
date: 2022-11-16
lang: ko-kr
tags:
    - System
---

* [Source code available](https://github.com/ANLAB-KAIST/KENSv3)
* [Part 1](https://yoon.ws/note/kens-renewal-part1/)

## KENS 개발 환경

[기존 KENS 시스템](https://github.com/ANLAB-KAIST/KENSv3/tree/v3.0)은 과제를 수행하기 위한 개발 환경을 셋업하는 것이 학생들에게 조금 까다로웠다.
KENS 개발 환경의 빌드 시스템은 순수 Makefile 이루어져 있고, 빌드 시 [GoogleTest](https://google.github.io/googletest/) 라이브러리를 설치해 주어야 하므로, C/C++을 처음 혹은 두 번째로 사용하는 학생들은 이 둘에 익숙하지 못하다.
따라서, 학생 중 상당수가 과제를 시작하는 데 어려움을 겪고 관련 질의응답도 많이 있었다.

이 문제의 질의응답이 어려운 점은 학생들의 개발 환경이 매우 다양하다는 점이다.
많은 학생이 리눅스가 아닌 macOS와 Windows를 사용하고 있고, 리눅스를 사용하더라도 배포판, GCC 및 GoogleTest 버전 등 개발 환경이 다양하기 때문이다.
또, 학생들이 질문을 할 때부터 필요한 정보를 제공하지 않아 여러 번 질문해야 하는 경우도 많아 조교들의 부담도 컸었다.

솔루션 파일도 빌드 시스템을 복잡하게 하는 요인이었다. KENS의 테스트(혹은 채점) 과정은 학생들이 작성한 TCP 구현과 조교가 작성한 TCP 구현이 호환되는가를 평가한다.
여기서 조교가 작성한 TCP 구현의 소스 코드는 학생들이 참고하지 못하도록, 컴파일된 바이너리의 형태로 제공된다. 간혹 이 바이너리가 개발 환경에 따라서 호환 문제를 일으킨다.

따라서, 학생들이 쉽게 과제를 시작할 수 있는 개발 환경을 만드는 것이 필요했다.
이 글에서는 KENS의 개발 환경과 빌드 시스템이 어떻게 변했는지를 설명한다.

## 사용하기 쉬운 빌드 시스템

KENS의 빌드시스템은 단순한 Makefile로 구성되어 있다.
간단한 구성이지만 이 Makefile에는 여러 문제가 있었는데, 대표적으로 빌드 방법과 사용법이 조금 특이한 커맨드를 사용해야 하고 `configure` 스크립트가 없어 GoogleTest 라이브러리 설치 유무를 판단하지 못했다.
이 문제를 모두 해결하도록 Makefile을 수정할 수도 있지만, 새로운 빌드 시스템을 사용하여 빌드 스크립트를 다시 작성하여 현대적 빌드 시스템의 이점을 수용하기로 했다.

다양한 빌드 시스템이 있지만, KENS를 위해서는 CMake를 사용하기로 했다.
CMake는 비교적 사용 방법이 간단하고 (automake 대비), Windows/macOS 지원도 잘 동작하며, 다양한 IDE 프로젝트 파일(Visual Studio, Xcode) 생성 기능도 가지고 있어서, KENS처럼 초심자가 다양한 환경을 주로 사용하는 프로젝트에 적합하다고 판단했다.

CMake의 장점 중 하나는 많은 프로젝트가 사용하고 있고, 이런 프로젝트를 쉽게 다운로드 및 링크할 수 있다는 점이다.
KENS가 의존하는 GoogleTest도 CMake를 사용하는 프로젝트이기 때문에, CMake 빌드 스크립트로 [자동으로 GoogleTest를 다운로드하고 링크](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/CMakeLists.txt#L133-L144)하도록 했다.
또, 솔루션 바이너리 파일도 이 기능을 활용하여 CMake 스크립트로 작성하여 자동으로 개발 환경(운영체제, 컴파일러)에 맞는 솔루션을 다운로드할 수 있도록 하였다.
결과적으로 인터넷에만 연결되어 있다면 GoogleTest와 솔루션 바이너리 파일이 자동으로 다운로드/링크되기 때문에, 학생들은 따로 신경 쓰지 않아도 과제를 바로 시작할 수 있게 되었다.

CMake 도입은 학생들의 과제 수행에 많은 부분을 차지하는 디버깅에도 추가적인 이점을 가져왔다.
CMake의 IDE 프로젝트 파일 생성 기능을 사용하면 강력한 디버깅 기능이 있는 IDE(Visual Studio, Xcode)에서 과제를 수행할 수 있게 된다.
또, 직접적인 프로젝트 생성 기능은 없지만, [플러그인](https://marketplace.visualstudio.com/items?itemName=ms-vscode.cmake-tools)을 활용하면 Visual Studio Code에서도 디버깅 기능을 사용할 수 있다.
이런 IDE를 이용한 개발은 CLI 개발과 달리 단순 클릭만으로 브레이크 포인트, 스택 트레이스 등의 기능을 쉽게 사용할 수 있게 하므로, GDB등의 CLI 기반의 디버거에 익숙하지 않은 학생들도 쉽게 디버깅을 할 수 있게 되었다.

CMake로의 전환은 수업에 많은 도움이 되었다.
기존에 많은 학생이 겪었던 빌드 관련 질의응답은 대부분 사라졌으며, 학생들이 디버거를 활용하여 쉽게 버그를 고칠 수 있게 돼 과제의 본래 목적인 TCP 스택 구현에 집중할 수 있게 되었다.

## 솔루션 바이너리 배포 시스템

학생들이 작성한 TCP 구현을 채점하기 위해서 KENS는 조교들이 작성한 구현과 호환성 테스트를 진행한다.
따라서, 학생들이 조교들의 코드를 참고할 수 없도록 솔루션은 바이너리 형태로 제공돼야 한다.
기존 시스템에서는 Git 커밋 속에 오브젝트 파일로 제공이 되었는데 이는 여러 문제점이 발생하였다.

이 중 하나는 학생들이 사용하는 GCC의 버전이 솔루션을 컴파일한 버전과 달라 생기는 호환성 문제였다.
대부분은 별문제 없이 두 버전이 달라도 링크가 되고 실행에 문제가 없었지만, 매우 드물게 링크 과정에서 오류가 생겨 잘못된 결과가 나타나는 경우가 있었다.
솔루션 바이너리 난독화 옵션과 [GCC 혹은 libstdc++의 ABI 관련 문제](https://gcc.gnu.org/onlinedocs/libstdc++/manual/abi.html)로 추측은 하지만 명확한 원인은 찾지 못하였다.
현실적으로 해결책으로 GCC의 메이저 버전별로 솔루션 바이너리를 컴파일하고, 빌드 시스템에서 적합한 바이너리를 다운로드/링크하는 방법을 사용하였다.
마이너 버전 차이에 따른 호환성 문제는 아직 해결하지 못했지만, 아직 관련하여 발생한 문제는 없었다.

그 밖에도 Git 저장소가 아닌 HTTPS로 바이너리를 배포하고, KENS 버전별 솔루션 바이너리 배포, 오브젝트 파일이 아닌 공유 오브젝트 파일 사용 등의 작은 개선점이 있었다.

## Windows 호환 레이어 (현재는 삭제됨)

KENS는 POSIX 호환 BSD 소켓 API 기반 TCP 네트워크 스택을 구현하는 과제이다.
하지만, 많은 학생이 사용하는 Windows 개발 환경(MSVC기반)은 POSIX와 완전하게 호환되지 않고,
KENS가 요구하는 몇 POSIX 호환 헤더를 다른 헤더로 제공하거나 호환성에 문제를 일으켰다.
결과적으로 성공하지 못했지만, Windows 환경을 지원하기 위한 여러 방법을 고민했었다.

우선 C++ 표준으로 대체할 수 있는 기능을 C++ 표준으로 대체하였다.
최신 버전의 MSVC 컴파일러와 Windows 개발 환경은 POSIX는 제대로 지원하지 않지만, [C++ 표준은 공식적으로 지원](https://learn.microsoft.com/en-us/cpp/overview/visual-cpp-language-conformance?view=msvc-170)한다.
따라서, [`rand_r`](https://man7.org/linux/man-pages/man3/srand.3.html), [`setenv`](https://man7.org/linux/man-pages/man3/setenv.3.html)와 같은 POSIX 표준이지만 C/C++ 표준이 아닌 함수를 비슷한 역할을 하는 C++ 표준 기능으로 대체하거나 삭제하였다.

KENS에서 모든 POSIX 전용 함수를 제거하거나 대체할 수는 없었다.
[`netinet/tcp.h`](https://pubs.opengroup.org/onlinepubs/009695399/basedefs/netinet/tcp.h.html)와 같은 네트워크 프로토콜 헤더, [`arpa/inet.h`](https://pubs.opengroup.org/onlinepubs/7908799/xns/arpainet.h.html) 등은 C/C++ 표준에서 제공하지 않은 구조체 및 함수를 포함하고 있고, Windows에서 제공하지 않거나 구현에서 조금 차이가 있었다.

이 문제를 해결하기 위해 제작했던 것이 Windows 호환 레이어이다.
KENS가 요구하는 POSIX 표준 함수들은 모두 시스템 콜을 이용하지 않는 함수들이고, 따라서 적당한 POSIX 구현을 찾아 링크시키면, Windows에서 해당하는 POSIX 함수를 사용할 수 있게 된다.
[4.4 BSD-Lite2](https://github.com/sergev/4.4BSD-Lite2)와 같은 여러 POSIX 구현체를 검토했지만, [musl libc](https://musl.libc.org)가 제일 유지보수가 잘 되고 있고 소스 코드에서 몇 함수만 선별적으로 링크하기 쉬운 구조로 되어 있으므로 이를 선택했다.
musl libc의 일부 소스 코드와 Windows 호환을 위한 몇 패치[^1]를 포함하여 [Windows 호환 레이어](https://github.com/ANLAB-KAIST/KENSv3/tree/v3.2.7/musl)를 제작했다. 이를 이용해 별도의 과정 없이 Windows에서 MSVC 개발 환경으로 KENS 과제를 수행할 수 있도록 했다.

Windows 호환 레이어를 이용하면 Windows에서 큰 문제 없이 과제를 수행할 수 있었지만, 다음 이유로 지원을 포기했다.

1. `cl.exe`의 이질적인 컴파일러 옵션: KENS에서는 솔루션 등을 위해 GCC/Clang에 있는 여러 컴파일 옵션을 사용한다. 이 두 컴파일러는 완벽히 일치하지는 않더라도 어느 정도 호환되는 컴파일러 옵션을 지원하고 있어서 빌드 스크립트를 작성하고 관리하는 데 큰 노력이 들지 않는다. MSVC의 `cl.exe`는 전혀 다른 컴파일러 옵션을 사용하고 이를 따로 관리하기에는 유지보수가 번거로워졌다.
2. 솔루션 링크 문제: 솔루션 바이너리는 Release 옵션을 사용하여 컴파일하고 배포된다. Visual Studio는 최적화 옵션이 다른 정적 라이브러리[^2]와 애플리케이션을 링크하는 것을 허용하지 않으므로, 솔루션을 링크할 때 조금 특수한 작업을 해주어야 한다.
3. Visual Studio: KAIST 전산학부 1학년 과목들은 Python을 이용하여 진행한다. 과거 C/C++로 프로그래밍을 학습하던 때와는 달리 학생들이 Visual Studio에 익숙한 상태가 아니다. Visual Studio를 사용한다는 점은 학생들을 편하게 하는 것이 아닌, 큰 용량의 소프트웨어를 설치해야 하고 익숙지 않은 개발 환경을 제공하여 오히려 불편을 발생시킨다.
4. WSL: 최신 Windows에서는 Windows Subsystem for Linux와 같이 리눅스와 GNU 소프트웨어를 쉽게 사용할 수 있는 방법과 이를 위한 소프트웨어 지원도 발전했다. WSL을 사용하면 KENS 과제를 가장 잘 지원하는 환경에서 수행할 수 있으므로, 꼭 네이티브 환경에서 과제를 수행해야 하는 당위성이 떨어진다.
5. Unknown unknowns: 내가 Windows 네이티브 개발 환경에 익숙하지 못해서 호환 레이어 사용으로 어떤 문제가 발생할지 모른다.

한 학기 동안 Windows 호환 레이어를 사용하는 KENS를 활용하여 수업을 진행했고 큰 문제가 없었다. 하지만, Windows 네이티브 환경의 채택률[^3]은 크게 높지 않았고, WSL을 이용하여 과제를 수행하는 데 큰 문제가 없으므로 더 이상 Windows 호환 레이어를 지원하지 않도록 결정했다.

## 결론

과거 KENS는 학생들이 개발 환경을 조성하는 데도 큰 어려움을 겪었고, 조교들은 개발 환경 조성을 위해서만 오피스아워를 운영하기도 했었다.
이번 리뉴얼 과정을 통해서, 빌드 환경 조성 및 사용이 직관적이고 큰 주의가 필요 없이 자동으로 동작하도록 만들었다.
비록 모든 환경에서 동작하는 개발 환경을 만들지는 못했지만, 큰 문제 없이 동작하는 개발 환경은 학생들과 조교들의 부담을 많이 줄일 수 있었다.

[^1]: musl libc는 Linux를 위해 제작된 프로젝트이기 때문에 Linux ABI를 준수하여 컴파일된다. C 표준에 명시되지 않은 구현은 ABI 차이에 따라서 조금씩 달라지는데, Windows와 Linux에서 비트 필드를 사용하면 컨테이너 구조체에 따라서 메모리 배치가 달라지는 문제가 있었다. [이 링크](https://github.com/ANLAB-KAIST/KENSv3/commit/31f4b9b3a50bce20eb06ec435956882e0e1933d8#diff-aede8ea360c2a31486c4b4a413a99cd0633282d27eecc9fb4be1285087204210)와 같이 구조체 내부에서 `unsigned int XXX:4;`와 `uint8_t XXX:4;`가 컴파일되었을 때 메모리 배치가 OS에 따라 달라진다.
[^2]: lib 파일. 당시에는 정적 라이브러리를 이용하여 솔루션을 배포하였으며, 동적 라이브러리(dll)로 전환한 후에는 문제가 생기지 않을 수 있다.
[^3]: 이는 Windows 네이티브 환경의 매력이 떨어지는 것도 있지만, Windows 호환 레이어의 개발이 성숙하지 못해서 Windows 네이티브 환경을 불안정 상태로 공지한 이유도 있다.
