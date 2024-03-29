---
title: 한글과 유니코드
date: 2016-07-04
tags:
    - Hangul
lang: ko-kr
---

유니코드에서 한글을 어떻게 다루는지를 정리하였다.

## 유니코드

* 유니코드(Unicode)는 전 세계의 모든 문자를 컴퓨터에서 일관되게 표현하고 다룰 수 있도록 설계된 산업 표준 [^1]
* 단순히 문자마다 번호를 붙임
* 계속 업데이트되며 현재는 Unicode Version 14.0.0 이 최신

### UTF

* 유니코드를 실제 파일 등에 어떻게 기록할 것인지를 표준화한 것이다.
* 유니코드는 문자를 각 숫자에 대응시킨 것에 불과하고 이를 실제 비트로 표현하는 방식은 다양하다
* UTF-8, UTF-16 등이 있다.

## 유니코드 속의 한글

[Unicode Consortium](http://www.unicode.org)의 Version 9.0.0 데이터베이스에 따르면 유니코드에서 한글이 지정된 블록은 다음과 같다.[^2]

* Hangul Jamo: 1100 ~ 11FF
* Currency Symbols 중 WON SIGN : 20A9
* CJK Symbols and Punctuation 중 HANGUL DOT TONE MARK: 302E ~ 302F
* Hangul Compatibility Jamo : 3130 ~ 318F
* Enclosed CJK Letters and Months 중 한글/한국어 부분 : 3200 ~ 321E, 3260 ~ 327F
* Hangul Jamo Extended-A : A960 ~ A97F
* Hangul Syllables : AC00 ~ D7AF
* Hangul Jamo Extended-B : D7B0 ~ D7FF
* Halfwidth and Fullwidth Forms 중 Halfwidth Hangul variants 부분 : FFA0 ~ FFDC
* Halfwidth and Fullwidth Forms 중 FULLWIDTH WON SIGN FFE6

편의상 한국어와 한글은 구분하지 않았다.

### 한글 자모

한글을 구성하는 가장 작은 단위인 자모에 부여된 유니코드이다.

#### Hangul Jamo

[차트](http://unicode.org/charts/PDF/U1100.pdf)

한글 자모를 기록한 영역이다. 초성, 중성, 종성으로 구성되어 있으며 각 자모 영역은 현대 한글과 옛 한글로 나뉘어 있다.

#### Hangul Jamo Extended-A

[차트](http://unicode.org/charts/PDF/UA960.pdf)

Hangul Jamo 영역에서 추가된 옛 한글 초성 블록이다.

#### Hangul Jamo Extended-B

[차트](http://unicode.org/charts/PDF/UD7B0.pdf)

Hangul Jamo 영역에서 추가된 옛 한글 중성, 종성 블록이다.

#### Hangul Compatibility Jamo

[차트](http://unicode.org/charts/PDF/U3130.pdf)

과거 한국에서 쓰였던 한글 문자 표준 (KS X 1001)과 호환되는 한글 자모 영역이다. 앞선 자모 영역과 달리 자음에 초성, 종성 구분이 없다.

### 한글 음절

#### Hangul Syllables

[차트](http://unicode.org/charts/PDF/UAC00.pdf)

자주 사용되는 한글 음절을 표현한 블록이다. 한국에서 사용되는 많은 시스템이 이 블록을 사용한다.

### 한글 기호

#### WON SIGN, FULLWIDTH WON SIGN

[차트](http://unicode.org/charts/PDF/U20A0.pdf), [차트](http://unicode.org/charts/PDF/UFF00.pdf)

원화 기호 (₩)를 지정한 유니코드 문자이다. 일반적으로 많이 사용하는 기호 \\ 는 표준적인 원화 문자가 아니다.

#### HANGUL DOT TONE MARK

[차트](http://unicode.org/charts/PDF/U3000.pdf)

중세 한국어에 존재했던 성조를 표시하기 위한 방점 기호이다. [위키백과](https://ko.wikipedia.org/wiki/방점)
방점 한개 혹은 두개가 존재한다.

#### Enclosed CJK Letters and Months 중 한글 부분

[차트](http://unicode.org/charts/PDF/U3200.pdf)

한글 원 기호와 괄호 기호를 표현한 영역이다.
다음 영역으로 구분되어 있다.

* Parenthesized Hangul letters : 한글 자음 괄호 기호
* Parenthesized Hangul syllables : 한글 음절 괄호 기호
* Parenthesized Korean words : 한국어 단어 괄호 기호 (오전, 오후)
* Circled Hangul letters : 한글 자음 원 기호
* Circled Hangul syllables : 한글 음절 원 기호
* Circled Korean words : 한글 단어 원 기호 (참고, 주의)
* Circled Hangul syllable : 추가 한글 음절 원 기호 (우)
* Symbol : 한국 추가 기호 Korean Standard 기호 (K 마크)

#### Halfwidth Hangul variants

[차트](http://unicode.org/charts/PDF/UFF00.pdf)

한글 반각 기호 영역이다. 현대 한글 자모만 존재한다.
일반적인 한글 자모 표기 방법은 전각이다.

## 정규화

앞서 살펴본 것처럼 유니코드에서 한글을 표시하는 방법은 다양하다. 같은 글을 표현하더라도 사용하는 코드 블록에 따라 다르게 저장된다. 예를 들어, `각` 이라는 문자는 한글 자모 영역을 이용해 `ㄱ` + `ㅏ` + `ㄱ` 으로 저장하거나 한글 음절 영역을 이용해 `각`이라는 하나의 문자로 저장할 수 있다. 만일 텍스트를 저장할 때 규칙 없이 저장한다면 후에 데이터 처리가 불편해질 것이다.

이 문제를 해결하기 위해 유니코드는 텍스트를 한 가지 규칙을 이용하여 정규화하여 저장하는 것을 권장한다. 정규화 규칙에는 NFD, NFC, NFKD, NFKC가 있다. ([UAX #15](http://unicode.org/reports/tr15/))

### NFD (Normalize Form D)

NFD는 모든 음절을 Canonical Decomposition(정준 분해)하여 한글 자모 코드를 이용하여 저장하는 방식이다. 즉, `각`을 `ㄱ` + `ㅏ` + `ㄱ`  로 저장하는 방식이다. 이 방식은 현대 한글과 옛 한글을 동일한 방식으로 저장한다는 장점이 있지만 NFC 방식과 비교하여 텍스트의 크기가 커진다는 문제가 있다.

NFD는 macOS 시스템에서 주로 사용한다.

### NFC (Normalize Form C)

NFC는 모든 음절을 Canonical Decomposition(정준 분해) 후 Canonical Composition(정준 결합) 하는 방식이다. 즉, `각`을 `각`이라는 하나의 문자로 저장하는 방식이다. 이 방식을 사용하면 NFD 방식보다 텍스트의 사이즈는 작아지게 된다. 하지만, 옛 한글 자모의 결합으로 이루어진 한글 음절 코드가 없으므로 이 음절은  Canonical Composition 하지 못하므로 자소가 분리된 체로 저장하게 된다. 이로 인해, 현대 한글과 옛 한글이 다른 방식으로 저장되므로 텍스트를 처리할 때 유의해야 한다.

NFC는 많은 GNU/Linux 시스템, Windows에서 주로 사용한다.

### NFKC, NFKD

NFKC와 NFKD는 또 다른 NFC, NFD 정규화 방식이다. 많은 사람들이 NFC와 NFD만 한글 유니코드를 처리하는데 쓰이고 NFKD/NFD, NFKC/NFC의 차이가 없다고 생각한다. 이는 한글 음절/자모 유니코드에서 호환분해 과정과 정준분해 과정이 동일하기 때문에 생기는 인식이다.

NFKC와 NFKD는 한글자모/한글음절 영역 이외의 한글 유니코드 영역을 처리할 때 유용하게 사용할 수 있다. 다음 표를 참고하면 각 유니코드 클자가 정규화 방식에 따라 어떻게 변하는 가를 확인할 수 있다.

|             | NFC         | NFD                     | NFKC                               | NFKD                                                    | 비고         |
|-------------|-------------|-------------------------|------------------------------------|---------------------------------------------------------|--------------|
| 각(AC01)    | 각 (AC01)   | 각 (1100 + 1161 + 11A8) | 각 (AC01)                          | 각 (1100 + 1161 + 11A8)                                 | 한글음절     |
| ㄱ (1100)   | ᄀ (1100)   | ᄀ (1100)               | ᄀ (1100)                          | ᄀ (1100)                                               | 한글자모     |
| ㄱ (3131)   | ㄱ (3131)   | ㄱ (3131)               | ᄀ (1100)                          | ᄀ (1100)                                               | 호환자모     |
| ㈀ (3200)   | ㈀ (3200)   | ㈀ (3200)               | (ㄱ) ( '(' + 1100 + ')' )          | (ㄱ) ( '(' + 1100 + ')' )                               | 자모괄호기호 |
| ㈎ (320E)   | ㈎ (320E)   | ㈎ (320E)               | (가) ( '(' + AC00 +  ')' )         | (가) ( '(' + 1100 + 1161 +,')' )                        | 음절괄호기호 |
| ㈝㈝ (321D) | ㈝㈝ (321D) | ㈝㈝ (321D)             | (오전) ( '(' + C624 + C804 + ')' ) | (오전) ( '(' + 110B + 1169 + 110C + 1165 + 11ab + ')' ) | 오전괄호기호 |
| ㉠ (3260)   | ㉠ (3260)   | ㉠ (3260)               | ᄀ (1100)                          | ᄀ (1100)                                               | 자모원기호   |
| ㉮ (326E)   | ㉮ (326E)   | ㉮ (326E)               | 가 (AC00)                          | 가 (1100 + 1161)                                        | 음절원기호   |
| ﾡ (FFA1)    | ﾡ (FFA1)    | ﾡ (FFA1)                | ᄀ(1100)                           | ᄀ (1100)                                               | 자모반각기호 |

이처럼 NFKC/NFKD의 호환분해는 단순히 자모를 분리/결합할 뿐만 아니라 각종 한글 특수 기호 또한 정규화를 진행한다. 모든 기호를 오직 한글음절/한글자모로 변환하므로 한글 특수기호를 다룰 일이 있다면 유용하게 쓰일 수 있을 것이다.

## 단위

지금까지는 한글을 어떻게 저장할 것인가에 대해 논의하였다. 이제는 저장된 한글을 어떻게 처리할 것인가를 논의해야 할 것이다. 이를 위해 가장 먼저 해야 할 것은 단위를 확실히 해야 하는 것이다.
한글 문자열은 한글 음절의 연속이다. 또한, 한글 음절은 한글 자모의 연속이다. 즉 첫 번째로 선택할 문제는 음절 단위 혹은 자모 단위를 선택해야 할 것이다.

### 자모 단위

일반적으로 한글을 처리할 때 자모 단위를 사용하는 경우는 많이 없다. 하지만 만일 자모 단위로 처리할 경우가 생기면 NFD 방식으로 정규화 한 뒤 처리하면 큰 문제가 없을 것이다.

### 문자 단위

음절을 처리하는 방식으로 문자 단위로 처리하는 방식이 있다. NFC 정규화된 유니코드 문자열의 문자 하나를 하나의 음절로 간주한다. 모든 현대 한글 음절은 유니코드 문자 하나로 표현 가능하므로 현대 한글을 처리할 때는 문제가 생기지 않는다. 하지만, 옛 한글의 경우 음절이 하나의 문자로 저장될 수 없으므로 문제가 생긴다. 즉, 음절 단위를 처리하기 위한 다른 방식이 필요하다.

### 자소 클러스터 단위

옛 한글 음절을 처리하기 위해서는 한글 문자열을 자소 클러스터(Grapheme Cluster) 단위로 분할해야 한다. 이에 대한 논의는 [UAX #29](http://unicode.org/reports/tr29/)에서 확인 가능하다.

자소 클러스터의 정의 방식은 언어에 따라 Extended grapheme clusters, Legacy grapheme clusters, Tailored grapheme clusters 등으로 나뉠 수 있는데 이 구분은 타밀 문자, 태국 문자, 데바나가리 문자 등의 문자를 위한 구분 되어 있으므로 한글을 처리할 때는 고려하지 않아도 된다.

본격적으로 옛 한글을 음절 단위로 처리하려고 한다면 UAX #29를 참고해야 할 것이다.

## 정렬

다음으로 논의할 문제는 한글 정렬 문제이다. 문자열을 정렬하는 방식은 다양하다. 같은 문자를 사용해도 국가 혹은 언어에 따라 정렬 방식이 달라질 수 있다. [UTS #10](http://www.unicode.org/reports/tr10/)를 참고하면 이에 대한 다양한 논의를 확인할 수 있다.

라틴 문자의 경우 국가, 언어에 따라 기호가 붙거나 대/소문자가 존재하므로 이를 정렬 알고리즘에 반영시켜야 한다. 하지만, 한글은 현재 한국에서만 사용하고 있고 현대 한글의 경우 기호를 사용하지 않으므로 문제가 비교적 간단하다.

현대 한글의 경우 문자열이 NFC로 정규화 되어 있다면 단순히 유니코드 코드 포인트로 정렬하더라도 괜찮은 결과가 나온다. 여기에 추가로 한글 자모 낱자와 기호 등을 고려하면 쉽게 정렬될 수 있다.

옛 한글의 경우는 현재까지 표준화된 자소 규칙이 존재하지 않는다. 예를 들면, `ㅅ`의 경우 현대 자소 말고도 치두음 시옷, 정치음 시옷이 존재한다. 이들을 구분하여 정렬할 것인지 구분한다면 어떤 순서로 정렬할 것인지 등의 논의가 필요하다.

### KS X 1026-1

유니코드 표준은 아니지만 [KS X 1026-1](http://www.unicode.org/L2/L2008/08225-n3422.pdf)에서는 한글 정렬 알고리즘이 소개되어 있다. 본격적으로 정렬을 하고자 한다면 이 규칙을 따르는 것도 나쁘지 않은 선택이다.

[^1]: 유니코드. 위키백과. [https://ko.wikipedia.org/wiki/유니코드](https://ko.wikipedia.org/wiki/유니코드)
[^2]: Unicode 9.0.0 Charts. <http://www.unicode.org/Public/9.0.0/charts/>
