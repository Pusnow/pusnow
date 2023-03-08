---
title: QCNFA765을 이용한 Wi-Fi 6 AP
date: 2023-03-08
tags:
    - system
lang: ko-kr
---

## QCNFA765

최근에 알리익스프레스에서 WCN6855를 사용한 QCNFA765이 $20 내외로 판매되고 있다는 것을 발견했다.
WCN6855은 Wi-Fi 6(802.11ax)는 물론, 6GHz를 사용하는 Wi-Fi 6E도 지원하여, 사용하고 있던 QCA6174보다 더 좋은 성능을 기대할 수 있다.
또, 두 개 이상의 주파수 대역을 사용하여 성능을 높이는 DBS(dual band simultaneous)도 사용할 수 있어, 6GHz를 지원하는 장비는 성능을 거의 두 배 가까이 올릴 수도 있을 것으로 판단했다.

이 글에서는 QCNFA765를 구매하여 Wi-Fi 6 AP로 사용할 때 발생한 시행착오를 소개한다.

## 하드웨어 셋업

기존에 사용하던 QCA6174기반의 WLAN 카드는 M.2 A+E 키 인터페이스를 사용하지만, 새로 구매한 WLAN 카드는 M.2 E 키로 인터페이스가 조금 다르다.
지금 사용하는 하드웨어는 NVMe SSD용 M 키 슬롯에 A+E 키 어댑터를 사용하고 있어서, 호환이 되지 않을 수도 있다.
다만, 판매자의 설명과 달리 어댑터는 E 키 슬롯의 형태로 되어 있어 E 키 카드가 장착되고, 실제로 장착해보니 적어도 Wi-Fi는 문제없이 인식되는 것을 확인했다.
아마도 판매자가 설명을 잘못 적었거나, WLAN 카드의 일부 기능(블루투스 등, 확인하지 않음)이 비활성화되었을 것이다.
본 목적인 Wi-Fi 6 AP를 만드는 것에는 큰 문제가 없으므로, 이 셋업으로 진행하기로 하였다.

## 펌웨어 셋업

기존 하드웨어와 같이 새로운 하드웨어도 펌웨어 로딩이 필요하다.
WCN6855의 펌웨어는 [ath11k-firmware](https://github.com/kvalo/ath11k-firmware)에서 제공하고 있고, 이 펌웨어는 Linux 커널에 탑재된 ath11k 드라이버라 로드하게 된다.
본 시스템에서는 가장 최신 버전의 펌웨어[^1]를 사용한다.

## 드라이버 설정

WCN6855 하드웨어를 지원하는 리눅스 커널의 ath11k 드라이버는 현재도 계속 개발되고 있다.
따라서, WCN6855를 제대로 사용하기 위해서는 비교적 최신 버전의 리눅스 커널을 사용해야 하는데, 이 시스템에서는 Debian 12에 탑재될 리눅스 커널(v6.1)을 사용한다.
Debian 12는 아직 testing stage이지만, 곧 릴리스 될 예정이고, 기존 시스템에서 쉽게 업그레이드할 수 있어서 이를 선택했다.

하지만, 하드웨어, 펌웨어, 드라이버 설정만으로는 충분하지 않았다.
Hostapd의 설정을 변경해도 WCN6855을 5GHz 대역에서 AP 모드로 변경이 되지 않았다.

### 문제 분석

`iw list`로 살펴보면 WCN6855 대역에서 `no IR`이 표시되는 문제다.
이 문제는 WLAN 카드에 regulatory domain 설정이 잘못되었을 때 발생하게 된다.
기존 하드웨어와 달리 WCN6855는 regulatory domain이  self-managed 되기 때문에[^2], `iw reg set` 등의 명령으로 regulatory domain 설정이 불가능하다.

이 문제는 (특히 Debian 환경에서) 크게 다뤄지지 않았기 때문에, 아무리 검색해도 적당한 해결책이 없었다.
중국어로 되어 있는 [CSDN 글](https://blog.csdn.net/wgl307293845/article/details/125760417)까지 결제[^3]하여 열람하였지만, 뾰족한 해결책이 없었다.

결국 커널 모듈 디버깅을 직접 진행하기로 하고, `ATH_DEBUG` 설정을 활성화한 뒤 커널 모듈을 컴파일 및 디버깅 로그를 살펴보았다.
Country 혹은 regdb 중심으로 커널 로그를 확인해 보니, 다음과 같은 로그가 눈에 띄었다.

```
Country 00, CFG Regdomain UNSET FW Regdomain 0, num_reg_rules 6
ath11k_pci 0000:01:00.0:   1. (2402 - 2472 @ 40) (0, 20) (0 ms) (FLAGS 0)
ath11k_pci 0000:01:00.0:   2. (2457 - 2482 @ 20) (0, 20) (0 ms) (FLAGS 128)
ath11k_pci 0000:01:00.0:   3. (5170 - 5330 @ 160) (0, 20) (0 ms) (FLAGS 2176)
ath11k_pci 0000:01:00.0:   4. (5490 - 5730 @ 160) (0, 20) (0 ms) (FLAGS 2176)
ath11k_pci 0000:01:00.0:   5. (5735 - 5895 @ 160) (0, 20) (0 ms) (FLAGS 2176)
ath11k_pci 0000:01:00.0:   6. (5945 - 7125 @ 160) (0, 20) (0 ms) (FLAGS 2176)
ath11k_pci 0000:01:00.0: rx ce pipe 2 len 172

...

ath11k_pci 0000:01:00.0: Country Setting is not allowed
ath11k_pci 0000:01:00.0: txpower from firmware NaN, reported -2147483648 dBm

```

어떤 이유에선가 드라이버가 country 설정을 거부하고 있었고, 따라서 기본 country 코드(00)로 설정되기 때문에 5GHz에서 AP 모드를 사용할 수 없었다.

이 현상이 발생하는 이유는 Debian 커널(혹은 리눅스 커널 기본값)이 `ATH_REG_DYNAMIC_USER_REG_HINTS`를 비활성화하기 때문에 발생한다.
ath11k 드라이버에서는 위 설정이 비활성화되었다면, [지역 코드를 업데이트하지 않는다.](https://github.com/torvalds/linux/blob/63355b9884b3d1677de6bd1517cd2b8a9bf53978/drivers/net/wireless/ath/ath11k/reg.c#L69-L73)
따라서, 커널 컴파일할 때 이 설정을 활성화하면 해결할 수 있다.

### 커널 빌드

드라이버 설정 하나를 바꾸기 위해서 모든 커널을 컴파일해야 할까?
커널의 버전 넘버가 크게 바뀌지 않는 이상 큰 문제는 없을 것이다.
하지만, 관리상의 이점(매 커널 업데이트 시 드라이버를 직접 업데이트해 줘야 하는 등) 때문에, Debian에서 제공하는 precompiled 커널을 사용하는 것이 아닌, 직접 전체 Debian kernel을 빌드하고, 커널 업데이트는 수동으로 진행하도록 결정하였다.
커널 빌드 자체는 Debian에서 새로운 kernel 소스코드가 릴리스 될 때마다 자동으로 컴파일하도록 하였다.
[빌드된 커널은 GitHub에서 관리](https://github.com/Pusnow/personal-kernel)하도록 하였다.

### 지역 코드 업데이트

ath11k에서 위 설정을 활성화하면 다음과 같은 디버그 출력을 볼 수 있다(`ATH_DEBUG` 필요).

```
ath11k_pci 0000:01:00.0: set current country pdev id 0 alpha2 KR                                                             

...

0000:01:00.0: processing regulatory channel list                                                                                                                     
ath11k_pci 0000:01:00.0: ath11k_pull_reg_chan_list_update_ev:cc KR dsf 5 BW: min_2g 0 max_2g 40 min_5g 2 max_5g 160                     

...

Country KR, CFG Regdomain ETSI FW Regdomain 5, num_reg_rules 5
ath11k_pci 0000:01:00.0:   1. (2402 - 2482 @ 40) (0, 23) (0 ms) (FLAGS 0)
ath11k_pci 0000:01:00.0:   2. (5170 - 5250 @ 80) (6, 23) (0 ms) (FLAGS 2048)
ath11k_pci 0000:01:00.0:   3. (5250 - 5330 @ 80) (6, 23) (0 ms) (FLAGS 2064)
ath11k_pci 0000:01:00.0:   4. (5490 - 5730 @ 160) (6, 23) (0 ms) (FLAGS 2064)
ath11k_pci 0000:01:00.0:   5. (5735 - 5835 @ 80) (6, 23) (0 ms) (FLAGS 2048)
```

정상적으로 지역 코드가 업데이트되는 것을 확인할 수 있으며, hostpad에서도 정상적으로 AP 모드를 활성화할 수 있었다.

### 규제 관련

`ATH_REG_DYNAMIC_USER_REG_HINTS`와 이 설정을 활성화 하기 위해 필요한 설정 `CFG80211_CERTIFICATION_ONUS`의 설명에는 다음과 같은 문구가 있다.

`ATH_REG_DYNAMIC_USER_REG_HINTS`:

> Say N. This should only be enabled in countries where
> this feature is explicitly allowed and only on cards that
> specifically have been tested for this.

`CFG80211_CERTIFICATION_ONUS`:

> You should disable this option unless you are both capable
> and willing to ensure your system will remain regulatory
> compliant with the features available under this option.
> Some options may still be under heavy development and
> for whatever reason regulatory compliance has not or
> cannot yet be verified. Regulatory verification may at
> times only be possible until you have the final system
> in place.

> This option should only be enabled by system integrators
> or distributions that have done work necessary to ensure
> regulatory certification on the system with the enabled
> features. Alternatively you can enable this option if
> you are a wireless researcher and are working in a controlled
> and approved environment by your local regulatory agency.

요약하면, 이 설정은 시스템이 현지 규제를 잘 준수하는 경우에만 활성화하라는 것이다.
ath11k에서 보고하는 사용 주파수 대역은 linux-wireless에서 국내 규제를 참고하여[^4] 정리한 [regdb](https://git.kernel.org/pub/scm/linux/kernel/git/sforshee/wireless-regdb.git/tree/db.txt?id=HEAD)와 어느 정도 일치하는 것으로 보이고, 펌웨어에 내장된 한국 규제 정보를 활용하기 때문에 큰 문제는 없다고 판단했다.


## Hostapd 설정

기존에 사용하고 있던 hostapd에서는 ax 모드가 활성화되지 않았다.
이는 Debian에서 제공하는 hostapd가 기본적으로 ax 모드를 지원하지 않게끔 설정되어 있어서 발생했던 문제로,
며칠 전에 [패치](https://salsa.debian.org/debian/wpa/-/commit/0119367854fc4ff2254c82b83dcb6886ab21c2a5)되었다.
패치가 Debian testing에 올라올 때까지 기다린 후, 업데이트하여 이 문제는 해결할 수 있었다.

기타 설정으로는 beamforming과 operating channel information 정도의 설정만 활성화하고 사용하고 있다.
최고 성능을 위한 설정은 조금 더 사용해 보면서 찾아봐야 할 것 같다.

## Wi-Fi 6E (6GHz) 설정

위와 같이 지역 정보를 정상적으로 업데이트했어도 Wi-Fi 6E (6GHz)를 활성화하지는 못했다.
어떤 이유인지는 몰라도, 펌웨어가 보고하는 한국의 규제 정보에 6GHz 대역이 빠져있다.

```
Country KR, CFG Regdomain ETSI FW Regdomain 5, num_reg_rules 5
ath11k_pci 0000:01:00.0:   1. (2402 - 2482 @ 40) (0, 23) (0 ms) (FLAGS 0)
ath11k_pci 0000:01:00.0:   2. (5170 - 5250 @ 80) (6, 23) (0 ms) (FLAGS 2048)
ath11k_pci 0000:01:00.0:   3. (5250 - 5330 @ 80) (6, 23) (0 ms) (FLAGS 2064)
ath11k_pci 0000:01:00.0:   4. (5490 - 5730 @ 160) (6, 23) (0 ms) (FLAGS 2064)
ath11k_pci 0000:01:00.0:   5. (5735 - 5835 @ 80) (6, 23) (0 ms) (FLAGS 2048)
```

이 문제를 해결하기 위해서는 하드웨어의 [OTP 데이터를 수정하거나, 펌웨어를 해킹](https://www.reddit.com/r/homelab/comments/ymecyp/comment/j64g1ms/)해야 하는 것으로 보이는데, 둘 다 쉬운 방법은 아니다.
어차피 나는 Wi-Fi 6E 장비를 가지고 있지도 않아서, 더는 시도하지 않았다.
이 때문에 DBS도 쉽게 활성화 하지 못할 것이라 판단하고 포기하였다.

## 결론

QCNFA765는 저렴하게 이용할 수 있는 Wi-Fi 6 AP 모드 WLAN 카드이다. 아직 소프트웨어와 펌웨어가 완벽한 것은 아니지만, Wi-Fi 6 AP로 활용할 수 있을 정도는 된 것으로 보인다.
장기 사용 시 어떤 문제가 발생할지는 모르지만, 현재로서는 큰 문제 없이 사용할 수 있을 것 같다.


[^1]: `WLAN.HSP.1.1-03125-QCAHSPSWPL_V1_V2_SILICONZ_LITE-3.6510.23`
[^2]: `iw reg get`으로 확인
[^3]: 99위안 + 결제대행료 (15,000원). 이 문서에서 제시하는 해결책은 리눅스의 오픈소스 ath11k드라이버를 사용하는 것이 아닌, 퀄컴에서 제공하는 비공개 드라이버를 사용하고, 이 드라이버에 country code 옵션을 사용하는 것이다. 퀄컴 비공개 드라이버를 사용하기 위해서는 매우 복잡한 절차(NDA 등)가 필요하기 때문에 이 방법은 사용할 수 없었다.
[^4]: [소스1](https://www.law.go.kr/LSW//admRulLsInfoP.do?chrClsCd=&admRulSeq=2100000205195), [소스2](https://www.law.go.kr/LSW//admRulLsInfoP.do?chrClsCd=&admRulSeq=2100000205187), [소스3](https://www.law.go.kr/LSW//admRulLsInfoP.do?chrClsCd=&admRulSeq=2100000206568)
