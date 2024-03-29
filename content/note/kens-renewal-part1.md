---
title: "KENS 리뉴얼 Part 1: 메모리 안전성"
date: 2022-11-10
lang: ko-kr
tags:
    - System
---

* [Source code available](https://github.com/ANLAB-KAIST/KENSv3)

## KENS

KAIST 전산망 개론 수업에서는 KENS(KAIST Educational Network System)라는 네트워크 교육용 시스템을 활용한다.
학생들은 KENS를 이용하여 기초적인 TCP 스택을 구현하는 과제를 수행하며, 이 과제는 전체 수업 과정 중에 상당한 부분을 차지한다.
하지만, 내가 조교 활동을 준비하고 있을 때(2020년 여름)는 KENS 과제에 여러 문제가 누적되어 있었으며, 이 글과 후속 글에서는 조교 활동 및 준비 기간(2020년 여름 ~ 2022년 여름) 동안, KENS가 개선된 내용을 일부 소개한다.

## 메모리 안전성

학생들이 과제를 진행하면 가장 많이 겪는 문제는 메모리 관련 버그이다.
전산망 개론은 주로 3학년 학생들이 주로 수강하기 때문에, 학생들은 아직 운영체제 등의 수업을 수강하지 않은 상태로 과제를 수행하게 된다.
더욱이, KAIST의 프로그래밍 기초 및 데이터 구조 과목은 대부분 Python 혹은 Java로 진행되고, C 혹은 C++는 시스템프로그래밍 과목에서 잠깐만 사용하기 때문에, 학생들은 수동으로 메모리를 관리하는 데 익숙하지 못한 상태다.

KENS는 C++ 기반의 프로젝트로 기존 버전에서는 모든 객체를 raw 포인터로 관리하여, 학생들이 모든 리소스를 수동으로 할당 및 해제해 주어야 했다.
또한, 각 객체의 소유권 또한 명시적으로 표시되어 있지 않아서, 숙련된 프로그래머도 소유권 이전에 대한 정보가 부족하여 소유권이 넘어간 객체를 해제하는 등의 메모리 오류를 발생시킬 수 있었다.

따라서, KENS를 리뉴얼의 가장 중요한 내용은 메모리 안전성을 보장하기 위한 프레임워크를 디자인하여, 학생들이 범할 수 있는 메모리 관련 코딩 실수를 구조적으로 차단하는 것이었다.

## 기존 코드 분석

[KENS의 기존 버전](https://github.com/ANLAB-KAIST/KENSv3/tree/v3.0.0)은 모든 객체가 raw 포인터로 관리되고, 이들의 소유권 및 라이프타임은 모두 암시적으로 관리되고 있었다.
또한, 여러 객체가 하나의 객체를 공유하는 패턴이 빈번히 사용되어 소유권이 분명치 않은 경우가 많아 소스 코드 분석을 더욱 어렵게 하였다.

특히, 가장 어려웠던 부분은 메시지의 소유권 문제였다.
KENS의 기본적인 구조는 `System`의 여러 `Module`이 서로 메시지를 전송하면, `System`이 도착 시간 등을 시뮬레이션하여 메시지가 도착하는 시간 순서대로 핸들러를 호출하는 구조로 되어 있다(이를 파악하는 데도 오래 걸렸다).
여기서 모든 메시지는 raw 포인터로 전달되며, 간혹 여러 메시지 큐에 들어가는 경우도 있었다.
때문에, 메시지 큐를 관리하는 객체는 드러나지 않은 룰을 가지고, 특정 메시지가 큐에 더 이상 존재하지 않다는 것을 확인하고, 그 메시지를 해제하는 등의 작업을 수행해야 했다.
따라서, 리빌딩 과정에서 이와 같은 암시적인 소유권을 파악하는데 많은 시간을 쏟았다.

사용자 인터페이스는 실수를 빈번하게 발생할 수 있는 디자인으로 설계되어 있었다.
기존 인터페이스의 [`sendPacket` 메서드](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/Networking/E_Host.hpp#L93)를 확인해 보면, `Packet` raw 포인터로 패킷이 전달되는 것을 확인할 수 있다.
메서드의 시그니처만 가지고는 메서드 호출 전후로 `Packet`을 어떻게 다루어야 하는지 알기가 어렵다.
따라서, 학생들은 메서드의 주석(DO NOT HAVE TO FREE THAT PACKET)을 확인하고 추론하여 메서드를 사용해야 했다.
또한, 주석에는 단지 `free()` 여부만 나타날 뿐이고, 소유권 이전을 명시하지 않고 있다.
즉, `sendPacket()`으로 소유권이 이전되었는데, 많은 학생은 단지 `free()`만 하지 않을 뿐 그 패킷을 계속 사용하여, use-after-free 등의 메모리 오류를 많이 범하였다.

## 명시적 소유권 지정

소스 코드의 의존성 관계를 파악하면, C++의 스마트 포인터를 이용하여 의존성 정보를 코드상의 명시적으로 표현을 할 수 있다.
스마트 포인터를 이용하여 의존성을 명시적으로 표현하면, 기존에 암시적으로 관리되던 메모리를 자동으로 관리할 수 있게 되어, `free()` 관련 메모리 버그(memory leak, use-after-free, double-free)를 방지할 수 있게 된다.
따라서, 메모리 안전한 KENS를 만들기 위해서는 기존 코드에서 파악된 의존성을 스마트 포인터로 표현해야 한다.

대부분의 의존성은 `unique_ptr` 혹은 `shared_ptr`을 이용하면 되지만, 문제는 표현이 애매한 의존성이 있다는 것이다.
`Wire`(구 `Port`) 모듈은 두 개의 `NetworkModule`(구 `Module`) 연결해 주는 역할을 한다. 이 모듈은 [연결하는 두 모듈의 raw 포인터를 멤버 변수로 가지고 있고](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/Networking/E_Port.hpp#L33), 두 모듈 또한 `Wire`의 포인터를 가지고 있을 뿐 아니라, [raw 포인터를 인덱스로 하는 다양한 컬렉션](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/Networking/E_Link.hpp#L39-L41)을 가지고 있다.
또한, 모든 모듈은 `System`이 소유하고 있어서, [`System`이 `Wire`와 `NetworkModule`의 raw 포인터를 가지고 있으면서](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/E_System.hpp#L63), 각 모듈 또한 [`System`에 접근하기 위한 raw 포인터를 가지고 있다](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/E_Module.hpp#L26).

이를 단순히 `shared_ptr`을 이용하여 표현한다면, 순환 참조가 되고, `weak_ptr`을 사용하면 `System`만 `shared_ptr`을 사용하게 되어 모두 `weak_ptr`을 이용하게 되는 구조가 된다.

매번 `weak_ptr`을 이용하는 것이 번거러우므로 대안을 찾다가, 모듈의 raw 포인터가 대부분은 단지 인덱스로만 사용한다는 것을 발견했다. (`System` 객체를 제외하고) 모듈의 raw 포인터는 다음과 같은 방법으로 사용한다.

1. `sendMessage()`을 사용하여 모듈로 메시지를 전달할 때, 특정 모듈을 지정하기 위해 사용.
2. 자료구조의 인덱스로 사용
3. 객체의 매서드를 직접 호출할 때 사용.

대부분은 첫 번째와 두 번째 용도로 사용하고, 세 번째는 거의 사용되지 않는다. 따라서, 얼마 없는 세 번째 용례를 모두 다른 방법으로 대체하면, 꼭 raw 포인터를 사용하지 않더라도 UUID를 이용하여 구현할 수 있다.

최종적인 디자인은 다음과 같다.

* [모든 모듈은 UUID를 가지고 있다.](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/E_Module.hpp#L26)
* [모든 모듈의 소유권은 `System` 객체가 가지고 있다.](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/E_System.hpp#L63) 간혹 System도 Module도 아닌 객체(테스트 코드 등)가 공유된 소유권을 가지고 있을 수도 있다.
* [메시지를 전송할 때는 UUID를 이용한다.](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/E_System.hpp#L75-L76)

위 디자인으로 KENS의 모든 소유권 정보를 스마트 포인터로 표현하여 자동으로 메모리 관리할 수 있게 되었다.

## 메모리 안전한 사용자 인터페이스

KENS 코드가 메모리 안전하더라도 학생들이 코드를 작성할 때 위험하게 작성한다면 메모리 오류가 발생할 것이다.
학생들이 작성한 코드에서 메모리 오류가 발생하는 것은 어쩔 수 없지만, 인터페이스를 잘 설계한다면 적어도 프레임워크를 사용하다 발생하는 메모리 오류는 방지할 수 있다.
따라서, 학생들이 사용하는 인터페이스를 실수 없이 사용할 수 있도록 설계하였다.

안전한 인터페이스를 설계하기 위해서는 메서드의 인자와 반환 값을 전달할 때 소유권을 명확하게 하고, 레퍼런스 수명 관리가 중요하다.
기존 인터페이스에서는 [소유권을 명시하지 않고 객체를 전달하고](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/Networking/E_Host.hpp#L93), [C 형식의 raw 포인터를 이용한 반환](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/Networking/E_RoutingInfo.hpp#L93)을 사용하여 사용자가 메모리 관리를 수동으로 해야 했으며, 다음과 같이 [수명이 모호한 raw 포인터로 참조 값을 반환하는 API](https://github.com/ANLAB-KAIST/KENSv3/blob/7343a28bd5bde9479ab3f2cd3747bc2dabff4fb4/include/E/Networking/E_Host.hpp#L60)도 존재했다.

우선 소유권을 명확히 했다. KENS 프레임워크에서 학생 코드로 혹은 그 반대로 패킷을 전달할 때 패킷에 대한 소유권이 넘어가도록 하였다.
C++에서는 r-value 참조 혹은 `unique_ptr`을 이용한 move 시멘틱을 활용하면, 소유권 이전을 구현할 수 있다.
현재로서는 학생이 KENS 시스템에 패킷 등의 이벤트를 전달할 때 다형성 등을 이용하지 않기 때문에, `unique_ptr`을 이용할 필요는 없었고, 따라서 [r-value 참조를 이용하여 패킷을 전달할 수 있게](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/Networking/E_Host.hpp#L94) 하였다.
다만, 학생들이 C++의 move 시멘틱에 익숙하지 않기 때문에, 사용이 쉬운 [l-value 참조를 이용한 인터페이스](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/Networking/E_Host.hpp#L95)도 제공하며, 이 메서드에서는 Packet의 내용을 복사하여 사용한다.

다음으로 중요한 것은 레퍼런스의 수명관리였다. C++에서는 레퍼런스 타입을 잘못 사용하면 허상(dangling) 레퍼런스가 발생할 수 있고, 이는 메모리 오류로 이어질 수 있다.
과거 KENS에서는 레퍼런스(raw 포인터의 형식으로 사용, 전달과 달리 소유권이 이전되지는 않음, 암시적)를 사용하는 패턴 두 가지가 있었는데(인자로 전달한 raw 포인터, raw 포인터를 반환 값으로 사용), 이를 학생들이 안전하게 사용할 수 있는 방법을 찾아야 했다.
이를 위해서는 단순히 raw 포인터를 레퍼런스 타입으로 바꾸는 것이 아닌(dangling 레퍼런스의 위험이 있음), 학생들에게 시스템 내부에서 사용하는 레퍼런스 타입을 노출하지 않은 것이 좋다고 판단하였다.
따라서, 학생들이 직접 시스템 레퍼런스에 접근하는 것이 아닌, 프레임워크에 정의된 인터페이스를 통하여 간접적으로 시스템 내부 레퍼런스에 간접 접근하도록 하였다.

`RoutingInfoInterface`는 대표적인 인터페이스를 이용한 내부 레퍼런스 간접 접근 방법이다. 기존에는 학생이 라우팅 테이블에 접근하기 위해서는 `getHost()` 메서드를 활용하여 `Host`의 레퍼런스를 가져온 뒤, `Host`의 `RoutingInfo` 인터페이스를 이용해야 했다.
이 과정에서 `Host`의 레퍼런스가 프레임워크에 의도와는 달리, 사용자에게 유출이 되며, 이를 잘못 사용하면 드물게 허상 레퍼런스 문제가 발생할 수 있다.
이 문제는 `Host` 레퍼런스를 [private 멤버로 가지는 `RoutingInfoInterface`](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/Networking/E_RoutingInfo.hpp#L20-L23)를 사용하여 해결할 수 있다.
`Host`는 `RoutingInfo` 클래스를 상속하고, 학생 제출용 클래스는 `RoutingInfoInterface`를 상속한다.
`RoutingInfoInterface`의 구현체만 `Host`의 레퍼런스에 접근할 수 있어서, 학생들은 `RoutingInfoInterface`와 같이 인터페이스 메서드를 이용해서만 `Host`에 접근할 수 있다.
이와 같은 방식으로 학생들이 의도치 않게 시스템 내부 레퍼런스에 접근하는 것을 차단할 수 있어서 허상 레퍼런스 오류를 발생시키지 않게 할 수 있었다.

그 밖에 다음 [예제](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/include/E/Networking/E_RoutingInfo.hpp#L76)처럼, 학생들의 참조 값을 시스템에 전달할 때는 raw 포인터 대신 const 레퍼런스 타입을 사용하여 NULL 포인터를 전달하는 것을 방지하였고, 레퍼런스 인자를 통한 리턴값 대신 객체 자체를 반환하는 방식으로 변경하였다.
또, NULL을 반환하여 부존재를 알리는 대신 `std::optional`을 활용하여 NULL 포인터를 사용하는 것을 방지하였다.

결과적으로, 학생들이 시스템 의도와 달리 레퍼런스를 오용하는 것을 방지할 수 있어서, 허상 레퍼런스 문제를 완화할 수 있도록 하였다.

## Sanitizer 사용

지금까지는 프레임워크 자체와 학생 코드-프레임워크 인터페이스에서 발생할 수 있는 메모리 오류를 방지할 수 있도록 했지만, 학생 코드에서 발생하는 메모리 관련 버그를 방지하지는 못한다.
이와 같은 오류를 조금이라도 방지하고 발생했을 때 원인을 파악할 방법이 필요하다.
이를 위해서는 sanitizer(address sanitizer, thread sanitizer, 등)를 쉽게 활용할 수 있게 [빌드 스크립트를 수정](https://github.com/ANLAB-KAIST/KENSv3/blob/af43e908b2977e06db5466367c9ef91bb8656525/CMakeLists.txt#L19-L31)하였다.
Sanitizer를 사용해도 메모리 관련 버그를 원천 차단하지는 못하지만, 적어도 학생들이 어디서 잘못했는지 쉽게 확인할 수 있게 되어 관련 문제해결을 매우 간단하게 할 수 있었다.

KENS 리뉴얼 과정에서 나 또한 의도치 않게 메모리 관련 오류를 발생시켰는데, 관련 버그들을 sanitizer를 이용하여 찾을 수 있었다.
Sanitizer를 이용하여 찾을 수 있었던 버그는 대표적으로, 부모 클래스의 소멸자에 `virtual` 키워드를 빠뜨려 자식 클래스 소멸자가 호출되지 않아 발생한 메모리 누수, 스레드 초기화 시 발생하는 데이터 레이스 등이 있었다.

## 결론

메모리 관련 버그는 과거 KENS 수업에서 가장 많이 받은 질문이었다.
단지 그 수가 많은 것이 아닌, 랜덤하게 발생하기도 하고 원인을 파악하기 어려워 답변들 주기가 어려운 경우도 많았다.
이번 KENS 리뉴얼을 통하여, 메모리 안전성을 대폭 강화할 수 있었고, 학생들이 의도치 않게 메모리 오류를 발생시키는 것을 모두는 아니지만, 많은 오류를 방지할 수 있게 되었다.
결과적으로 수업 진행 시 메모리 관련 질문을 받는 건수는 많이 감소하였고 학생들 또한 디버깅에 시간을 덜 사용하게 되어서 본 수업에 주된 내용인 네트워크와 TCP 스택 공부에 집중할 수 있는 환경을 만들 수 있었다.
