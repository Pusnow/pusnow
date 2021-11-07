---
title: 비트 스캔 연산자의 Undefined Behavior
date: 2021-11-07
tags:
    - system
lang: ko-kr
---

비트 스캔 연산자에는 프로그래머가 주의를 기울이지 않으면 실수 할 수 있는 undefined behavior가 존재한다.
이 문서에서는 이런 undefined behavior와 이에 따른 버그 및 해결 방안을 알아본다.

## 비트 스캔 연산자

최신 프로세서에는 비트 스캔 연산자가 존재한다.
Intel 프로세서의 경우 `bsf` (Bit Scan First), `bsr` (Bit Scan Reverse) 연산자와 BMI1 확장을 지원한다면 `lzcnt` (Leading Zero Count), `tzcnt` (Trailing Zero Count) 연산자가 추가로 존재한다.
이 연산자들은 기본적으로 피연산자를 스캔하여 가장 첫 번째 혹은 마지막 비트의 위치를 추출하는 역할을 한다.

`bsf`/`tzcnt`/ 는 0부터 시작하여 가장 첫 번째 비트의 위치, `bsr`은 가장 마지막 비트의 위치, `lzcnt`는 마지막 비트의 위치 (가장 최고 비트부터)를 추출한다. 예를 들어 `0x1002`에 각 연산자를 적용하면 다음과 같다 (32bit 버전 연산자 사용).

- `bsf`: 1
- `bsr`: 12
- `tzcnt`: 1
- `lzcnt`: 19

GCC에서는 비트 스캔 연산자를 쉽게 사용할 수 있게 [builtin 함수들](https://gcc.gnu.org/onlinedocs/gcc/Other-Builtins.html)을 제공하여 비트 스캔 연산자를 쉽게 사용할 수 있게 해준다.

- `__builtin_ffs`: Returns one plus the index of the least significant 1-bit of x, or if x is zero, returns zero.
- `__builtin_clz`: Returns the number of leading 0-bits in x, starting at the most significant bit position. **If x is 0, the result is undefined.**
- `__builtin_ctz`: Returns the number of trailing 0-bits in x, starting at the least significant bit position. **If x is 0, the result is undefined.**

위와 같은 비트 스캔 연산자를 활용하면 비트맵 등 비트 하나로 데이터를 표기하는 데이터 구조를 쉽고 빠르게 만들 수 있어서 많은 구현체에서 이를 활용한다.

## 비트 스캔 연산자의 Undefined Behavior

Intel 시스템 매뉴얼과 GCC 매뉴얼을 살펴보면 몇 비트 연산자(`bsf`, `bsr`, `clz`, `ctz`)에 0을 인자로 활용하는 것은 undefined behavior라는 것을 알 수 있다.
본 문서에서는 `ctz`를 활용하여 비트 스캔 연산자를 잘못 활용했을 경우 어떤 문제가 발생하는지를 알아보겠다.

GCC(적어도 11.2 버전)에서는 `__builtin_ctzll`(`ctz`의 `long long` 버전)에 0을 제공하면 64를 결과로 내보낸다 [[참고](https://godbolt.org/z/7ncjrKPqK)].

그렇다면, 이 결과를 활용하는 함수를 제작해도 문제가 없을까?
이 결과를 활용하는 함수 `is_empty`를 제작해 보았다. 이 함수는 `field`를 인자로 받고 모든 비트가 0이면 1 아니면 0을 리턴하는 함수이다. (이 기능을 더 쉽게 구현하는 방법은 많지만 여기서는 의도적으로 실수를 저지르기 위해 `ctz`를 사용하였다.)

```c
int is_empty(uint64_t field){
    uint64_t ret = 0;
    ret = __builtin_ctzll(field);

    if (ret == 64)
        return 1;
    else
        return 0;
}
```

이 함수에 0을 사용하여 호출한다면 1이 리턴하여 얼핏 보면 문제가 없는 것으로 보인다 [[참고](https://godbolt.org/z/vzPv3x661)].

## Undefined Behavior에 의한 버그

다시 한번 강조하자면, `__builtin_ctzll`에 0을 인자로 넘기는 것은 undifined behavior이고 해서는 안 되는 행동이다.
즉, 경우에 따라 위처럼 64를 리턴할 수 있지만, 이것을 컴파일러 혹은 라이브러리가 보장하지는 않는다.

위와 완벽히 동일한 코드를 최적화 수준을 변경하여 다시 컴파일해보자. 놀랍게도 다음과 같은 결과가 나타난다.

결과: [https://godbolt.org/z/hG86WWE3P](https://godbolt.org/z/hG86WWE3P)

최적화를 하나도 진행한 결과 달리 최적화 수준을 2로 상향할 경우 전혀 다른 결과인 0을 리턴하게 된다.
왜 이런 결과가 발생할 것일까? 답은 컴파일러 최적화에 있다 [[참고](https://godbolt.org/z/ej4sx1rjP)].
최적화 수준이 2인 경우 다음과 같은 어셈블리 코드가 생성된다.

```asm
is_empty(unsigned long):
        xor     eax, eax
        ret
```

위 어셈블리 코드에서는 `eax`에 단지 0을 대입하고 리턴한다. (단지 0을 리턴함)
이와 같은 어셈블리 코드가 생성된 이유는 컴파일러가 최적화 도중에 `__builtin_ctzll` 함수가 단지 0부터 63까지의 결과만 리턴한다는 것을 알고 (나머지는 undefined behavior) `ret == 64`가 항상 `false` 라고 판단했기 때문이다.
따라서, 이 조건문 분기는 절대 방문하지 않는 것으로 간주하고 다음과 같은 코드로 최적화를 한 것이다.

```c
int is_empty(uint64_t field){
    
    // 최적화에 따라 ret는 사용하지 않기 때문에 삭제
    // uint64_t ret = 0;
    // ret = __builtin_ctzll(field);

    // 항상 false이기 때문에 else 구문만 사용
    // if (ret == 64)
    //    return 1;
    // else
        return 0;
}
```

이와 같은 결과는 비트 스캔 연산자에 0을 인자로 주는 것은 해서는 안 되는 행동이고, 이의 결과를 활용하는 것은 더더욱 절대로 해서는 안 되는 행동임을 보여준다.

## 버그 방지 방안

그렇다면 이와 같은 결과를 방지하려면 어떻게 해야 할까?
가장 쉽게 생각할 수 있는 방법은 `__builtin_ctzll`을 사용하기 전에 조건문을 활용하는 것이다.

```c
int new_ctzll(uint64_t field){
    if (field == 0)
        return 64;
    else
        return __builtin_ctzll(field);
```

많은 경우 조건문은 프로세서의 speculative 실행을 방해하여 성능을 저하하기 때문에, 때로는 사용하기 어려울 수가 있다.
이 경우 다른 비트 스캔 연산자 중 undefined behavior가 없는 것을 사용하면 된다.
`__builtin_ffs`을 사용하면 0을 인자로 주는 행동도 undefined behavior가 아니고, 이 점을 활용하면 보다 효과적인 코드를 만들 수 있을 것이다.
