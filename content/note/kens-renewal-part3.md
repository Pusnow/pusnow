---
title: "KENS 리뉴얼 Part 3: 지속이 가능한 에코시스템과 남은 과제"
date: 2022-11-22
lang: ko-kr
tags:
    - System
---

* [Source code available](https://github.com/ANLAB-KAIST/KENSv3)
* [Part 1](https://yoon.ws/note/kens-renewal-part1/)
* [Part 2](https://yoon.ws/note/kens-renewal-part2/)

## 지속가능성

언제까지고 내가 KENS 수업 조교를 할 수는 없다.
다음에 다른 조교가 쉽게 조교 활동을 할 수 있도록 개편하여 지속이 가능한 에코시스템을 개발하는 것이 이번 리뉴얼의 마지막 목표였다.
이를 위해서 KENS 과제 자료를 문서화, 조교 활동에 수반하는 반복적인 작업을 자동화, 그리고 지식 베이스 조성을 시도하였다.
모든 것이 완벽하다고 할 수는 없지만, 어느 정도 성과가 있어 이를 공유한다.
마지막으로, 현재까지 개발된 KENS의 한계점과 향후 개선 방향에 대하여 정리해 보았다.

## 문서화

기존 KENS 시스템은 간단한 소개 슬라이드와 [API 문서 홈페이지](http://anlab-kaist.github.io/KENSv3/doc/)가 전부였다.
학생들은 과제를 처음 시작하는 것부터 어려움을 겪어서 답답함을 호소하는 학생이 많이 있었다.
또, 학생들은 프레임워크에 특정 기능을 사용하기 위해서 어떤 메소드를 호출해야 하는지를 모르기 때문에 API 문서에 익숙하지 않은 학생들은 과제 진행이 매우 어려웠다.
그래도 과제를 수행하는데 필요한 프레임워크의 기능은 많지 않기 때문에, 한번 이 기능들을 익히면 프레임워크로 사용법으로 인해 어려움을 겪지는 않게 된다.
따라서, 학생이 프레임워크 사용법을 빨리 익히게 하는 것이 이번 리뉴얼에서 중요한 목표였다.

학생들이 프레임워크 사용법을 빨리 익히기 위해 GitHub의 Wiki 기능을 활용하여 [KENSv3 Wiki](https://github.com/ANLAB-KAIST/KENSv3/wiki)를 개설하고 여러 KENS 관련 문서들을 작성하였다.
과제를 수행하는 데 필요한 개발 환경 조성 방법, 과제 소개 및 여러 팁 등 완벽하지는 않지만, 과제 수행에 필요한 모든 정보를 한곳에 모아 두었다.
특히, API를 사용하는 여러 팁을 소개하여, 학생들이 마주치는 여러 시나리오에 따른 프레임워크 사용법을 예제 위주로 소개하여 따라 하기만 하더라도 쉽게 KENS의 기능을 익힐 수 있도록 했다.

## 자동화

조교 활동은 여러 반복되는 작업의 연속이다.
매 학기 같은 수업을 진행할 뿐만 아니라, 매 과제도 채점과 표절 검사 등 반복되는 작업의 연속이다.
또, KENS의 버전 상향이 지속됨에 따라 변경되는 문서 생성, 호환성 테스트, 솔루션 빌드, 컨테이너 이미지 빌드 등의 작업도 지속해서 이뤄져야 한다.
추후 조교가 변경되더라도 위 작업을 쉽게 진행할 수 있는 시스템을 구축하는 것이 목표였다.

학생들의 과제물을 관리하는 작업은 과제 파이프라인을 이용한다.
다음은 KENS 과제 파이프라인으로 학생들이 KLMS(KAIST Learning Management System)에 제출된 과제물들이 어떻게 처리되는가를 보여준다.

```mermaid
flowchart TB
    klms(1\. Submission archive) -- unzip --> klms_extracted
    klms_extracted(2\. Extracted KLMS archive) -- extract_klms.py --> submissions
    submissions(3\. Submissions) -- git commit/push --> github(4\. GitHub)
    submissions -- check_plag.py --> plagiarism_report(5\. Plagiarism report)
    submissions -- grade.py --> grading_result
    grading_result(6\. Grading result) -- report.py --> report(7\. Grading report)
```

1. 학생들이 제출한 과제물들은 KLMS에서 압축 파일로 한 번에 다운로드 받을 수 있다.
2. 압축을 해제하면 학번과 이름으로 구성된 각 제출물이 나타난다.
3. `extract_klms.py` 스크립트를 이용해서 KLMS 제출물을 정리하여 과제물 데이터베이스에 추가한다.
4. 추후 표절 검사에 활용하기 위해 비공개 GitHub 저장소에 저장한다.
5. `check_plag.py` 스크립트를 활용하여 지금까지 제출된 과제들을 모두 비교하여 표절 여부를 확인한다.
6. `grade.py` 스크립트를 이용하여 제출물을 채점한다. 채점은 컨테이너 이미지를 활용하여 동시에 독립된 환경에서 수행한다.
7. `report.py`를 이용하여 채점 결과를 정리 리포트를 생성한다.

학생들 제출물을 관리하는 작업을 제외하고는 많은 작업이 GitHub Actions를 이용하여 CI를 이용한 자동화를 진행하였다.
[API 문서 생성 및 배포](https://github.com/ANLAB-KAIST/KENSv3/actions/workflows/doxygen.yml), 호환성 테스트([리눅스](https://github.com/ANLAB-KAIST/KENSv3/actions/workflows/test-linux.yml), [리눅스2](https://github.com/ANLAB-KAIST/KENSv3/actions/workflows/test-linux-extra.yml), [WSL](https://github.com/ANLAB-KAIST/KENSv3/actions/workflows/test-wsl.yml), [macOS](https://github.com/ANLAB-KAIST/KENSv3/actions/workflows/test-macos.yml)), [컨테이너 이미지 빌드 및 배포](https://github.com/ANLAB-KAIST/KENSv3/actions/workflows/docker-publish.yml), 솔루션 빌드(비공개) 등이 GitHub Actions를 이용하여 진행된다.
특히 마지막 솔루션 빌드는 OS(Linux, macOS) 및 컴파일러 버전(GCC, AppleClang)별로 별도의 환경을 구축해야만 수행할 수 있는데, GitHub Actions를 이용하면 쉽게 개발 환경을 대여해 사용할 수 있어서 쉽게 솔루션을 빌드할 수 있었다.

## 지식 베이스

조교 활동의 많은 부분은 학생들의 질문에 답하는 것이다.
학생들은 매우 다양한 질문을 하고 어떤 경우에는 KENS, 네트워크 스택 및 POSIX에 대한 깊은 이해가 없으면 답변하기 어려운 것들도 많이 질문한다.
이런 질문을 답변하기 위해서는 몇 학기 정도 지속해서 KENS 조교로 활동하여 관련 노하우가 쌓여야 한다.
하지만, KAIST에서는 길어야 3년(석박사과정 총합) 정도를 조교로 활동하게 되는데, 노하우가 생길 때가 되면 더는 조교를 하지 않게 된다.
이 시스템에서는 매우 정교한 인수인계를 진행하지 않는 한, 세대를 거듭함에 따라 노하우의 유실이 발생하고 결과적으로 다음 조교가 처음부터 노하우를 쌓아 올려야 하는 비효율이 발생한다.

이 문제를 현실적으로 해결하기 위해서 지식 베이스를 구축하기로 했다.
학생들과의 질의응답 과정을 기록하고 다음에 비슷한 질문을 가진 학생이 검색을 통하여 스스로 문제를 해결하게 된다면, 전문성 있는 조교의 필요성이 줄어들게 되고 질의응답을 통해 발생한 노하우가 영속적으로 전승되게 된다.

지식 베이스를 구축하는 방법은 다양하지만, GitHub Discussion을 선택하기로 했다.
기존에 질의응답을 위해 사용하던 KLMS의 질의응답 게시판은 매 학기 새로 생성되기 때문에 전 학기의 질의응답 내용을 검색 및 열람할 수 없다.
지식 베이스의 구축 목적이 노하우의 영속이므로 이는 적합한 선택이 아니었다.
그 밖에 Stack Overflow, Confluence 등 기능이 많고 강력한 지식 베이스 소프트웨어를 검토했지만, 다음 이유로 GitHub Discussion을 선택하였다.

* GitHub Discusstion을 이용하기 위해서 대부분의 전산학부 학생은 GitHub 계정을 가지고 있어서 따로 가입할 필요가 없고, GitHub에 친숙하므로 사용에 큰 어려움이 없다.
* KENS와 관련된 자료(소스 코드, 문서, 위키)는 GitHub로 관리되어 접근이 편리하고, 검색 기능을 이용하면 소스 코드, 문서, 위키 자료가 한꺼번에 검색이 된다.
* GitHub Editor의 다양한 기능을 활용할 수 있다.

[KENSv3 GitHub Discussion](https://github.com/ANLAB-KAIST/KENSv3/discussions)을 도입하고 한 학기 수업을 진행했었다.
여전히 KLMS 질문 게시판 및 이메일 등 Discussion을 제외한 다른 채널로 질문을 하는 학생들이 있었지만, 영속하는 지식 베이스 구축을 위해서 모두 GitHub Discussion을 이용하라고 안내했다.
또, 기존에는 따로 오피스아워를 마련하여 프로젝트 관련 질의응답을 해야 했는데, 여기서 발행하는 질의응답 또한 지식 베이스에 남겨두기 위해 정말 필요한 경우가 아닌 한 Discussion을 이용하게 했다.
질의응답 방법의 개선으로 많은 중복되는 질문을 없앨 수 있었으며 다음 학기에도 다른 조교와 학생이 질의응답 내용을 검색 및 열람할 수 있게 되었다.

GitHub Discussion은 GitHub Editor를 사용하기 때문에 추가적인 장점을 가져왔다.
[이 질의응답 과정](https://github.com/ANLAB-KAIST/KENSv3/discussions/58)처럼 소스 코드를 참조할 때 자동으로 링크와 렌더링 되어 학생들의 편의를 도모할 수 있었고, 이 기능을 Linux 매뉴얼 파일 및 RFC를 참조할 때 유용하게 활용할 수 있었다.

## 남은 과제

KENS는 다른 네트워크 수업 과제와 달리 네트워킹 스택을 구현해 보는 독특한 장점을 가지고 있다.
하지만, 전산망 개론 수업 조교로 활동하면서 여러 한계점을 느꼈고, 앞으로의 개선 방향을 생각해 보았다.
여기서는 버그 수정과 같은 자잘한 개선 방향은 제외하고 큰 노력이 필요한 큰 방향만 공유해 본다.

### 프로그래밍 언어 접근성 개선

KENS는 C++ 기반의 프로젝트로 이번 리뉴얼을 거치면서 C++17의 최신 기능들을 여러 도입하였다.
C++는 다양한 기능을 지원하여 모든 기능을 능수능란하게 사용하기에는 매우 복잡한 언어이고, 많이 사용해도 여전히 헷갈리는 개념이 많이 존재한다.
전산망 개론을 수강하는 3학년 학생들은 C++는 물론 C언어에도 익숙하지 못한 경우가 많을 뿐 아니라 C++11 이상의 현대적인 C++ 기능은 많이 어려워하기도 한다.

그렇다면 학생들을 어떻게 하면 현대적인 C++에 익숙하게 할 수 있을까?
KENS에서 사용하는 C++ 기능을 소개하는 튜토리얼을 진행하는 것도 한 방법일 수 있다.
하지만, 여기서 조금 더 나아간 방법을 생각해 보았다.
KENS 과제 수행을 학생들이 익숙한 Python을 이용해서 진행할 수 있도록 개편해 보는 것은 어떨까?

Python에도 BSD 소켓과 유사한 [소켓 인터페이스](https://docs.python.org/3/library/socket.html)를 제공하고 있고 이의 내부 구현(TCP 구현 포함)을 개발해 보는 것도 네트워킹 스택과 POSIX 소켓의 핵심 개념을 익히는 데 문제가 없을 수 있다.
물론 C++와 Python 모두 익숙한 사람에게는 메모리 배치를 다루기 쉬운 C++이 더 편할 수 있겠지만, C++이 익숙하지 못한 학생이 C++를 익히느라 사용하는 시간을 많이 줄일 수 있게 될 것이다.

KENS의 Python 버전 개발은 생각보다 어렵지 않을 수 있다.
KENS의 모든 부분을 Python으로 대체하는 것이 아닌, 학생들이 접근할 수 있는 인터페이스만 Python wrapper를 작성하면 되는 문제이고 이를 자동화하는 몇 [프로젝트](https://github.com/pybind/pybind11)도 존재한다.

이 개선 방향은 많이 논쟁적일 수 있다.
이번 리뉴얼을 통해 메모리 관리 등 많은 C++의 어려운 부분을 많이 사라져 KENS의 난이도가 많이 쉬워졌고 문서화도 많이 진행되어 과제를 시작하는 것이 많이 쉬워졌다.
그래도, KENS의 접근성을 높이기 위해 많은 학생이 익숙한 Python을 도입해 보는 것은 고려해 볼 수 있다고 생각한다.

### 멀티플렉싱

현재 KENS에서 다루는 네트워크 관련 시스템 콜은 `socket`, `connect`, `bind`, `listen`, `accept`, `read`, `write`, `close`, `getsockname`, `getpeername`으로 멀티플렉싱을 위한 `select`, `poll` 등의 시스템 콜은 포함되어 있지 않다.
또한, KENS 시뮬레이터 구조상 멀티프로세싱은 지원하기 어렵고, 멀티스레딩 시뮬레이션 또한 아직 지원하지 못한다.
따라서, 현재 과제는 서버와 클라이언트가 1:1로 데이터를 주고받는 시나리오만 테스트하고 있다.
현대적인 네트워크 애플리케이션에서 `select`와 같은 I/O 멀티플레싱은 필수적인 기능이고, 이를 학생들이 구현해 보는 것은 값진 경험이 될 것이다.

### 다양한 과제

KENS의 주된 과제 내용은 TCP 네트워킹 스택을 구현하는 것이다.
이번 리뉴얼을 통해서 [BSD 소켓 사용법 학습을 위한 echo 서버](https://github.com/ANLAB-KAIST/KENSv3/tree/master/app/echo) 및 [라우팅 프로토콜 개발](https://github.com/ANLAB-KAIST/KENSv3/tree/master/app/routing)을 추가했지만, 아직은 과제가 아주 다양하지는 않다.
나는 과거에 전산망 개론 수업 말고도 분산시스템 및 알고리즘 수업 조교도 했었는데, 이 수업에서 사용할만한 RPC, 합의 알고리즘, P2P와 같은 과제를 개발해 KENS를 확장한다면 좋을 것이다[^1].

## 결론

지금까지의 KENS는 조교 활동을 위한 체계적인 방법이 없었다.
이번 리뉴얼을 통해 문서화, 자동화, 지식 베이스 구축을 통해 체계적인 KENS 관리가 가능해졌으며, 앞으로 다른 조교가 오더라도 이전보다는 쉽게 조교 활동을 할 수 있게 되었다.
다음 조교는 이번 리뉴얼을 통해 필요 없이 KENS를 공부하는 것에 시간을 쓰지 말고  KENS의 남은 과제를 해결하는 데 시간을 사용해 보기를 기대해 본다.

[^1]: 기존에는 [MIT에서 제공하는 Raft 합의 알고리즘 과제](http://nil.csail.mit.edu/6.824/2017/labs/lab-raft.html)를 사용했었다. 이 과제에서는 네트워크 시뮬레이터와 결정론적 랜덤 변수를 사용하지 않기 때문에, 결과가 비결정적이므로 나타나게 된다. 분산 알고리즘 구현이란 어려운 과제를 더욱 어렵게 하는 요소였다.
