---
title: "비동기 프로그래밍 개념들"
date: 2024-09-07
lang: ko-kr
tags:
    - System
---

비동기 프로그래밍을 편하게 하기 위해 다양한 프로그래밍 언어적 기능과 라이브러리들이 존재한다.
많은 경우 각 개념들이 엄밀하지 않게 사용되는 경우가 많은데, 이 글에서는 되도록 원전을 찾아보고 각 개념을 엄밀히 정의해본다.
또한, 각 개념들이 처음 제안되었을 때의 의미와 다르게 현대에 사용될 수도 있다.
이 또한 반영하려 노력해본다.

이 글에서는 다음과 같은 개념들을 조사한다.

* Event-driven programming
* Coroutine
* Event Loop and Handlers
* Callback
* Promise and Future
* Async/await
* CSP Model
* Actor Model

## Event-Driven Programming

이 글에서 설명하는 event-driven은 thread-driven vs. event-driven 문맥에서 event-driven을 지칭한다.
과거에는 thread 기반 프로그래밍과 event-driven 프로그래밍 모델 사이의 여러 논쟁이 있었으며[^conf/hotos/CunninghamK05], 이는 더 오래전부터 논의되어 온 procedure-oriented 시스템과 message-oriented 시스템의 이름 정도만 다른 것으로 보인다[^journals/sigops/LauerN79]. 이에 따라 각 용어를 정의하면 다음과 같다. 괄호 안에는 논문이 작성될 당시에는 없거나 이 문맥에서 사용되지 않았던 개념으로 설명을 위해 추가하였다.

* Procedure-oriented (or thread-driven): a large, rapidly changing number of small processes (or threads, coroutines) and a process synchronization mechanism based on shared data.
* Message-oriented (or event-driven): a relatively small, static number of processes (or threads) with an explicit message (or event) system for communicating among them.

앞서 인용한 논문에서 밝혔다시피, 두 프로그래밍 모델은 듀얼이다. 즉, 한 모델에서 정의된 기본 요소는 다른 모델에 맞는 프로그램이나 요소에 매핑될 수 있다.
그럼에도, 초창기 Apache HTTP server (fork-based, process-driven) vs. NGINX (event-driven)에서의 논쟁 처럼, 학계에서도 웹 서버 (혹은 highly concurrent한 요청을 처리하는 서버)에서 thread-driven 모델이 우월하다는 주장[^conf/hotos/BehrenCB03]과 event-driven이 우월하는 주장[^whythreadsbad]이 이어졌고 다양한 라이브러리와 서버들이 연구되었다[^conf/hotos/CunninghamK05][^conf/sosp/BehrenCZNB03][^conf/sosp/WelshCB01].

## Coroutine

앞서 작성한 [글](https://www.pusnow.com/note/execution-units/)에서처럼 코루틴은 여러 문맥에서 다양한 개념을 지칭하고 있다. 현재 문맥에서는 procedure-oriented 시스템에서 사용하는 process의 일종으로 보면 간단하다.
코루틴은 다른 process 혹은 thread와 달리 생성과 문맥전환이 빠르기 때문에 작은 프로세스의 수가 빠르게 변화하는 procedure-oriented 시스템에서 성능을 개선하기 위해 많이 사용된다. Capriccio는 대표적인 코루틴을 사용한 procedure-oriented 시스템이다[^conf/sosp/BehrenCZNB03].

## Event Loop and Handlers

Event-driven programming을 어떻게 할 것인가는 사실상 표준적인 방식이 존재한다: 이는 event loop와 event handler들을 활용하는 방식이다.
이 방식에서는 하나의 프로세스가 하나의 루프(event loop)를 가지고 있고 그 루프에서 이벤트를 수신을 기다리고 수신시 그 이벤트를 처리하는 서비스 루틴(event handlers)을 호출한다[^journals/sigops/LauerN79].
아래 코드는 인용한 논문에서 사용한 코드 예시이다.

```
begin m: messageBody;
    i: messageld;
    p: portid;
    s: set of portid;
    ... --local data and state information for this process
    initialize;
    do forever; -- event loop
        [m, i, p] <- WaitForMessage[s];
        case p of
            port 1 =>... ; --algorithm (or handler) for port1
            port 2 =>...
                    if resourceExhausted then
                        s <- s - port2;
                        SendReply[i, reply];
                        ...; --algorithm (or handler) for port2
            ...
            port k => ...
                    s <- s + port2
                    ... ; --algorithm (or handler) for port k
        endcase;
    endloop;
end;
```

하나의 프로세스가 하나의 event loop를 지속적으로 실행한다. 이 loop 안에서는 (1) port의 집합 s로부터 이벤트를 수신하여 port에 따라 대응되는 handler를 실행한다. (2) 만일 특정 port(2)에 대한 리소스가 모두 소진되었을 경우, 더이상 이벤트를 수신하지 않기 위해 집합 s로부터 리소스가 소진된 port를 제거한다. (3) 다른 handler(k)에서 특정 port(2)에대한 리소스를 다시 확보했을 경우, 다시 집합 s에 그 port(2)를 추가한다.

## Callback

Event-driven programming에서 콜백은 어떤 프로그램이 특정 이벤트를 기다려야 하기 때문에 특정 작업을 완료하지 못할 경우 등록하는 함수로, 이 함수는 그 이벤트가 발생했을 경우 호출된다[^conf/sigopsE/DabekZKMM02].
콜백은 다음 예시와 같이 비동기 함수의 인자로 전달되며, 보통의 경우 event loop와 handler를 관리하는 라이브러리에서 호출하는 경우가 많다.

```c
void awrite (int fd, char *buf, size_t size, void (*callback) (void *), void *arg);
```

콜백은 event loop와 handler를 관리하는 라이브러리에서 자주 사용되는 인터페이스이다.
다양한 라이브러리에서 애플리케이션이 등록한 callback은 특정 이벤트가 발생했을 때 라이브러리의 event handler가 그 이벤트에 대응되는 콜백 함수를 호출한다.
이런 라이브러리에서는 라이브러리가 event loop와 handler를 관리하기 때문에, 개발자가 event handler에서 event에 따른 각 event handler를 직접 호출할 필요 없어져, event-driven 프로그래밍을 보다 쉽게 할 수 있게 한다.

Callback을 사용하는 라이브러리는 libasync[^conf/sigopsE/DabekZKMM02]과 같은 연구 시스템을 비롯, .NET의 APM와 EAP, Node.JS 등이 있다.

### 번외: Higher-Order Function과 Combinator

앞서 소개한 함수 `awrite`는 인자로 함수 `callback`을 받는다.
이와 같이 함수를 인자로 받는 함수를 higher-order function이라 한다[^conf/acm/Reynolds72].

Combinator는 많은 경우 higher-order function과 같은 의미로 사용되는데, 엄밀하게 따지면 combinator pattern의 combinator만 해당된다.
Combinator라는 용어는 combinatory logic과 combinator pattern 두 맥락에서 사용되는데, 이는 (적어도 내가 보기에는) 전혀 다른 의미를 가지고 있다[^haskell-combinator].

* Combinator in combinatory logic: a function or definition with no free variables.
  * 내부에서 사용되는 변수가 모두 인자로 제공되는 함수를 말한다. 여기서 변수에는 다른 함수도 포함함으로, 컴비네이터에서 다른 함수를 호출하기 위해서는 그 다른 함수를 인자로 받아야 한다. 즉, 이 경우 higher-order function이 되어야 한다.
* Combinator in combinator pattern: something combines values of type T in various ways to build up more complex values of type T.
  * 작은 값들을 합쳐 보다 복잡한 값들을 만들어 내는 것을 지칭한다. 보통은 함수를 인자로 받아 더 복잡한 함수를 만드는 것이 많기 때문에, higher-order function이 많다.

위 두 combinator의 용례가 밀접한 관계가 있는 것인지는 모르겠다.

## Promise and Future

Promise와 Future는 효율적인 비동기 호출을 지원하기 위해 만들어진 데이터타입으로, 미래에 존재할 값에 대한 placeholder이다[^journals/toplas/Halstead85][^conf/pldi/LiskovS88].
처음 이들이 생성되었을 때는 결과 값을 지니고 있지 않지만 비동기적이 완료되어 값이 생성되면 placeholder에 값이 채워져 결과 값을 caller가 조회할 수 있게 된다.

Callback 매커니즘과 비교한다면  특정 이벤트의 발생을 callback으로 수신하는 것이 아니라 caller에서 promise/future 데이터타입으로 조회하게 된다.
앞서 제시한 `awrite` 함수는 promise를 사용하면 다음과 같이 바꿀 수 있다.

```c++
promise_t<int> awrite (int fd, char *buf, size_t size);
```

이 함수는 호출 즉시 바로 비동기적인 I/O 요청을 발생시키고 promise를 리턴하게 된다.
후에 caller에서 promise를 조회하여 쓰기 이벤트의 성공 여부를 확인할 수 있다.

이들은 callback 방식의 여러 단점을 개선하지만, 그 중 가장 유명한 것은 callback hell일 것이다.
Callback hell은 callback 함수 내에서 새로운 callback 함수를 등록하는 경우에, indendation의 레벨이 계속 증가하여 가독성이 좋아지지 않는 문제를 말한다[^callbackhell].
Promise를 사용하면 callback을 함수의 인자로 넘겨주지 않기 때문에 이런 문제가 발생하지 않고, 만일 callback처럼 continuation 기능을 꼭 사용하고 싶다면 `then()`과 같은 promise가 제공하는 higher-order 함수를 사용하면 된다. 이 경우에도 caller에서 `then()`을 호출하기 때문에 추가적인 indentation level이 증가하지는 않는다. 아래는 `then()` 함수를 사용하는 예시이다. 여러 continuation을 사용했음에도 indentation이 일정하게 유지된다.

```c++
promise_t<int> p = awrite(fd, buf, size);
promise_t<bool> p2 = p.then(
  ||(int written){
    if(written > 0 ) { return true;  } 
    else { return false; }
});
promise_t<void> p3 = p2.then(
  ||(bool ok){
    if(ok) { printf("ok\n"); } 
    else { printf("error\n"); }
});
```

Promise와 future는 매우 유사한 개념이다. 이들은 많은 경우 같은 것을 지칭하지만 맥락에 따라 다른 것을 지칭하기도 한다.
예를 들면, promise를 강타입, 예외처리, call-stream기능을 추가적으로 지원하는 future를 지칭하거나[^conf/pldi/LiskovS88],
future를 evaluation이 지연될 수 있고 객체로 전달되어 꼭 evaluation 주체가 callee가 아닐 수 있는 promise를 지칭하는 경우도 있다[^conf/sc/Chatterjee89].
또, 현대의 프로그래밍 언어에 따라서는 이들을 구분해서 사용하기도한다.
C++에서는 promise를 future를 이용하여 비동기적으로 조회할 수 있는 객체를 지칭한다[^cpppromise].


## Async/Await

Promise 위주로 프로그래밍을 하다보면 모든 함수가 promise를 리턴하게 되는 상황이 자주 발생한다.
몇 프로그래밍 언어에서는 async 키워드를 통해 이를 통일성 있게 표현할 수 있게 한다[^journals/pacmpl/Syme20].
예를 들면, 아래 `awrite` 함수는 앞서 설명한 함수와 동치이다. (실제 C++에는 async 키워드가 없다. 여기서는 임의로 추가하였다.)

```c++
async int awrite (int fd, char *buf, size_t size);
```

Promise는 callback이 발생시키는 모든 문제를 해결하지는 못했다.
이 중 하나는 inversion of control-flow이다.
이 문제는 callback을 등록하는 주체와 이를 실행하는 주체가 달라지는 상황을 말한다.
위 예제 들에서 callback 함수는 누가 호출하게 되는가?
비동기 프레임워크에 따라서는 다른 스레드에서 실행될 수 있고[^conf/icse/OkurHDD14], 같은 스레드에서 실행된다 하더라도 스택프레임은 달라질 수 있다.
만일 다른 스레드에서 callback 호출된다면, caller 함수가 제어하는 변수에 접근할 때 락 등을 사용하여 신중하게 접근해야 한다.
Callback이 caller와 같은 스레드에서 실행한다 하더라도, 스택 프래임이 달라지기 때문에, 만일 callback 함수에서 실수로 caller 함수의 로컬 변수에 접근하다면 use-after-free 오류가 발생하게 된다.

Await 키워드는 이 문제를 pause를 통해 해결한다.
특정 promise에 await을 호출하게 되면 실행중인 컨택스트는 일시 중지되고, 후에 promise가 처리되면 중지된 컨택스트가 재개된다.
아래 예시에서 `await()` 함수를 통해 promise를 조회하는 예시이다.

```c++
int written = awrite(fd, buf, size).await();
if(written > 0 ) { return true;  } 
else { return false; }
...
```

Async/Await을 사용하게 된다면 이벤트 처리를 동기적 시멘틱을 사용할 수 있다.
위 코드를 일반적인 write 시스템콜을 사용하는 코드과 비교해보면, `await()` 함수가 있다는 점만 제외한다면 대부분 일치한 다는 것을 알 수 있다.

그렇다면, Async/Await의 프로그래밍 모델은 event-driven일까 아니면 thread-driven일까?
사람마다 의견이 다를 수 있지만, 나는 event loop위에서 구현된 thread-driven이라 생각한다.
이와 같은 구조는 Capriccio와 유사한 구조로[^conf/sosp/BehrenCZNB03], 이 구조 위에서 컴파일러/라이브러리가 Async/Await 키워드를 통해 락으로 보호된 값 (promise)를 쉽게 사용할 수 있게 한 것이다.


## CSP Model

[^journals/cacm/Hoare78]
(작성중)

## Actor Model

[^conf/ijcai/HewittBS73]
(작성중)


[^whythreadsbad]: John Ousterhout. *Why Threads Are A Bad Idea (for most purposes)* In ATC 1996.
[^haskell-combinator]: Haskell Wiki. *Combinator*. [https://wiki.haskell.org/Combinator](https://wiki.haskell.org/Combinator).
[^callbackhell]: *Callback Hell*. [http://callbackhell.com](http://callbackhell.com).
[^cpppromise]: *std:promise* [https://en.cppreference.com/w/cpp/thread/promise](https://en.cppreference.com/w/cpp/thread/promise)

<!-- pusnow reference start -->
[^conf/acm/Reynolds72]: John C. Reynolds. *Definitional interpreters for higher-order programming languages.* In ACM Annual Conference (2) 1972. [https://doi.org/10.1145/800194.805852](https://doi.org/10.1145/800194.805852)
[^conf/hotos/BehrenCB03]: J. Robert von Behren, Jeremy Condit, and Eric A. Brewer. *Why Events Are a Bad Idea (for High-Concurrency Servers).* In HotOS 2003. [https://www.usenix.org/conference/hotos-ix/why-events-are-bad-idea-high-concurrency-servers](https://www.usenix.org/conference/hotos-ix/why-events-are-bad-idea-high-concurrency-servers)
[^conf/hotos/CunninghamK05]: Ryan Cunningham and Eddie Kohler. *Making Events Less Slippery with eel.* In HotOS 2005. [http://www.usenix.org/events/hotos05/final_papers/full_papers/cunningham/cunningham.pdf](http://www.usenix.org/events/hotos05/final_papers/full_papers/cunningham/cunningham.pdf)
[^conf/icse/OkurHDD14]: Semih Okur, David L. Hartveld, Danny Dig, and Arie van Deursen. *A study and toolkit for asynchronous programming in c#.* In ICSE 2014. [https://doi.org/10.1145/2568225.2568309](https://doi.org/10.1145/2568225.2568309)
[^conf/ijcai/HewittBS73]: Carl Hewitt, Peter Boehler Bishop, and Richard Steiger. *A Universal Modular ACTOR Formalism for Artificial Intelligence.* In IJCAI 1973. [http://ijcai.org/Proceedings/73/Papers/027B.pdf](http://ijcai.org/Proceedings/73/Papers/027B.pdf)
[^conf/pldi/LiskovS88]: Barbara Liskov and Liuba Shrira. *Promises: Linguistic Support for Efficient Asynchronous Procedure Calls in Distributed Systems.* In PLDI 1988. [https://doi.org/10.1145/53990.54016](https://doi.org/10.1145/53990.54016)
[^conf/sc/Chatterjee89]: Arunodaya Chatterjee. *FUTURES: a mechanism for concurrency among objects.* In SC 1989. [https://doi.org/10.1145/76263.76326](https://doi.org/10.1145/76263.76326)
[^conf/sigopsE/DabekZKMM02]: Frank Dabek, Nickolai Zeldovich, M. Frans Kaashoek, David Mazières, and Robert Tappan Morris. *Event-driven programming for robust software.* In ACM SIGOPS European Workshop 2002. [https://doi.org/10.1145/1133373.1133410](https://doi.org/10.1145/1133373.1133410)
[^conf/sosp/BehrenCZNB03]: J. Robert von Behren, Jeremy Condit, Feng Zhou, George C. Necula, and Eric A. Brewer. *Capriccio: scalable threads for internet services.* In SOSP 2003. [https://doi.org/10.1145/945445.945471](https://doi.org/10.1145/945445.945471)
[^conf/sosp/WelshCB01]: Matt Welsh, David E. Culler, and Eric A. Brewer. *SEDA: An Architecture for Well-Conditioned, Scalable Internet Services.* In SOSP 2001. [https://doi.org/10.1145/502034.502057](https://doi.org/10.1145/502034.502057)
[^journals/cacm/Hoare78]: C. A. R. Hoare. *Communicating Sequential Processes.* Commun. ACM 21(8). [https://doi.org/10.1145/359576.359585](https://doi.org/10.1145/359576.359585)
[^journals/pacmpl/Syme20]: Don Syme. *The early history of F#.* Proc. ACM Program. Lang. 4(HOPL). [https://doi.org/10.1145/3386325](https://doi.org/10.1145/3386325)
[^journals/sigops/LauerN79]: Hugh C. Lauer and Roger M. Needham. *On the Duality of Operating System Structures.* ACM SIGOPS Oper. Syst. Rev. 13(2). [https://doi.org/10.1145/850657.850658](https://doi.org/10.1145/850657.850658)
[^journals/toplas/Halstead85]: Robert H. Halstead Jr.. *Multilisp: A Language for Concurrent Symbolic Computation.* ACM Trans. Program. Lang. Syst. 7(4). [https://doi.org/10.1145/4472.4478](https://doi.org/10.1145/4472.4478)
<!-- pusnow reference end -->