---
title: DIY Wi-Fi 라우터
date: 2022-11-23
tags:
    - System
lang: ko-kr
---

## DIY Wi-Fi 라우터 제작

이 글에서는 개인적으로 사용하는 Wi-Fi 라우터를 소개한다.
일반적인 라우터와 달리 Intel 기반의 미니 PC에 Debian Linux 기반으로 직접 제작하여 커스터미이징이 쉽고 높은 성능을 제공한다.

## 목적

기성 Wi-Fi 라우터는 낮은 가격에 쓸만한 성능, 전력효율을 제공한다.
하지만, 대부분의 기성 라우터는 제조사가 제공하는 펌웨어만을 강제한다. [OpenWRT](https://openwrt.org)와 같은 커스텀 펌웨어를 사용하더라도 완전히 커스터마이즈하여 사용하기에는 한계가 있다.

그래서, 직접 Wi-Fi 라우터를 만들기로 결심했다.
또, 새로 만드는 김에 기존에 개인적으로 사용하던 홈서버와 통합하여, 홈서버가 Wi-Fi 라우터 기능을 제공하는 것을 목표로 했다.
그 밖에 다음과 같은 목표들을 정하고 Wi-Fi 라우터 제작을 시작했다.

* Fanless: 방 안에서 24시간 계속 사용할 예정이므로, 팬 소음은 없어야 한다.
* Compact: Wi-Fi 라우터는 책상 위에 두고 사용하기 때문에 너무 큰 공간을 차지하면 안 된다.
* Dual-LAN: WAN과 LAN 용 각 최소 하나씩 필요하므로, 이더넷 포트가 두 개 이상은 있어야 한다.
* Dual-WLAN: 2.4GHz와 5GHz Wi-Fi를 모두 지원하려면 두 개 이상의 WLAN 카드를 설치할 수 있어야 한다.
* Major Linux Distro: Debian, CentOS와 같이 사용법이 익숙한 리눅스 배포판이면 좋겠다.
* Container Support: Docker와 같은 컨테이너 이미지를 이용해서 서버를 관리할 수 있어야 한다.
* Cost?: 가격은 큰 고려 사항은 아니다. 가격대성능비는 기성품을 능가할 수 없다.

## 하드웨어

### 베이스 하드웨어

가장 먼저 결정해야 하는 것은 마더보드 혹은 베어본 PC와 같은 베이스 하드웨어였다.
Fanless 및 Compact 조건을 만족하기 위해서는 팬리스 Intel/AMD CPU 내장 mITX 메인보드 혹은 베어본 PC 중에서 선택해야 한다.
ARM 기반 하드웨어도 도전해 보고 싶었으나, 아직은 쓸만한 하드웨어가 많지 않아서 포기하였다.
또, 두 개의 WLAN 카드를 위한 PCIe/mPCIe/M.2 PCI 슬롯이 두 개 필요하고[^1], Dual-LAN을 탑재한 하드웨어가 아니면 이더넷 카드를 위한 PCIe/mPCIe/M.2 PCI 슬롯이 추가로 하나 더 필요하다.

이런 하드웨어는 국내에서 소매점을 통해서 구하기가 어렵다. 특히, 팬리스 하드웨어 PCIe/mPCIe/M.2 PCI 슬롯이 3개씩 달린 경우는 거의 없고, 팬이 있더라도 케이스 크기가 많이 커지게 된다.

결국 선택한 하드웨어는 Aliexpress에서 판매하는 TopTon N5105 Router였다.
이 하드웨어는 4개의 2.5G Intel i225-V 온보드 이더넷을 탑재하고 있고, Wi-Fi용 mPCI 슬롯 하나, NVMe 스토리지용 M.2 M-Key 슬롯이 하나가 있었다.
이 외에 SATA3 포트가 추가로 있어서 2.5인치 SSD 드라이브를 추가로 설치할 수 있었다.

이 하드웨어는 조건 대부분을 만족했다.
별도의 팬이 없고 매우 작은 산업용 컴퓨터, 4개의 이더넷 포트, 두 개의 PCIe/mPCIe/M.2 확장 슬롯, Intel CPU 탑재로 일반 Linux Distro 설치와 컨테이너 지원 등 모든 조건을 만족할 뿐만 아니라, 가격 또한 매우 저렴했다.
구매 시점에는 US $142.76으로 베어본 PC라는 점을 감안하면 저렴하고, 면세범위(US $150) 안이기 때문에 무관세로 수입할 수 있었다.

### 확장 카드

이 하드웨어를 사용하기 위해서는 메모리, 스토리지 및 WLAN 카드가 필요하다.

메모리는 평소에 쓰지 않고 남아있던 SO-DIMM DDR4 16GB 메모리 두 장을 사용했다.
흥미롭게도 Aliexpress 판매 페이지에는 베어본 PC의 최대 지원 메모리가 64GB로 안내되어 있었다. [Intel ARK](https://ark.intel.com/content/www/us/en/ark/products/212328/intel-celeron-processor-n5105-4m-cache-up-to-2-90-ghz.html)에 따르면 재스퍼레이크 N5105 CPU는 최대 지원 메모리가 16GB이기 때문에 판매자가 잘못 기술한 줄 알았으나, 실제로 테스트해 보니 32GB 메모리 모두 인식이 되고 사용할 수 있었다.

스토리지는 기존에 사용하던 2TB WD Blue SATA SSD 드라이브를 사용했다.
NVMe 스토리지도 테스트해 보았지만, 발열이 너무 심하여 사용할 수 없을 정도로 스토리지 성능이 저하되었으며, WLAN 카드를 위해 NVMe 슬롯을 사용해야 하므로 SATA SSD 하나만 사용하게 되었다.

WLAN 카드는 퀄컴 아데로스 QCA6174 카드를 [Protectli](https://protectli.com)에서 두 개 구매하여 장착하였다.
보통 자주 사용하는 Intel WLAN 카드는 [5GHz 대역에서 AP 모드로 동작하지 않은 제한](https://wireless.wiki.kernel.org/en/users/drivers/iwlwifi)이 있고, Broadcom 카드는 모델에 따라 비공개 드라이버를 사용해야 해서 관리가 번거롭게 된다.
최근 MediaTek의 WLAN 카드의 성능 및 지원이 많이 개선됐다고 하나, 아직은 퀄컴 아데로스가 더 검증되었다고 판단하여 이를 선택하였다.
이 외에 Realtek이 있지만 아직 퀄컴에 비하면 성능 및 지원이 빈약하다고 한다.

NVMe 슬롯(M.2 M Key)에 Wi-Fi 어댑터를 장착하려면 변환 어댑터가 필요하다. Aliexpress에서 M.2 M key 슬롯에 M.2 A+E Key 카드를 장착할 수 있게 하는 어댑터를 구매하여 장착하였다.
결과적으로 mPCI 슬롯에 mPCI 퀄컴 WLAN 카드 한 장과 NVMe 슬롯에 어댑터를 통하여 M.2 A+E Key 퀄컴 WLAN 카드 한 장, 총 두 장의 WLAN 카드를 설치하였다.

WLAN 카드를 이용하려면 케이스에 안테나 구멍이 필요하다.
이 하드웨어는 두 개의 안테나를 사용하는 WLAN 카드 한 장을 사용하는 것을 가정하고 설계된 하드웨어이기 때문에, 안테나 구멍이 두 개만 존재했다.
QCA6174는 두 개의 안테나 사용하고 총 두 장의 QCA6174를 사용하기 때문에, 안테나 구멍이 총 4개가 필요하다.
따라서, KAIST 아이디어팩토리에 방문하여 드릴링 머신을 이용해 케이스 측면에 두 개의 안테나 구멍을 추가로 뚫었다.
결국 총 네 개의 안테나를 모두 설치할 수 있었다.

### 최종 사양

최종 사항을 정리하면 다음과 같다.
아주 성능이 좋다고는 할 수 없지만, Wi-Fi 라우터 중에는 매우 좋은 편이다.

| Hardware     | Specification                          |
| ------------ | ---------------------------------------|
| CPU          | Intel Celeron N5105 (2.00GHz)          |
| Memory       | 32GiB DDR4 Synchronous (2667 MHz)      |
| SSD          | 2 TB WD Blue SSD                       |
| NIC          | 4x Intel Ethernet I225-V (2.5G)        |
| Wireless NIC | 2x Qualcomm Atheros QCA6174 (802.11ac) |

## 소프트웨어

### OS

OS는 최신 버전의 Debian Linux를 사용하였다.
모든 서비스를 컨테이너화하여 관리하기 때문에, Debian 제공 Docker를 설치해서 사용했다.

### Firmware

QCA6174 WLAN 카드를 사용하기 위해서는 이를 위한 펌웨어 설치가 필요하다.
Debian에서는 [`firmware-atheros` 패키지](https://packages.debian.org/bullseye/firmware-atheros)를 설치하면 되는데, 내가 가지고 있는 카드와 패키지의 펌웨어가 호환되지 않았다.
[업스트림 linux-firmware](https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git)도 테스트해 보았지만 역시 호환성 문제가 있었다.

결국, [`ath10k-firmware` GitHub 저장소](https://github.com/kvalo/ath10k-firmware)에서 제공하는 hw3.0 4.4.1.c3 버전 펌웨어가 호환되는 것을 확인하고 이를 수동으로 설치하여 사용하였다.
ath10k 메일링 리스트를 통해 각 펌웨어 버전별 (c1, c2, c3) 차이가 무엇인지 문의해 보았으나, 정확한 정보를 얻지는 못하였다.

### Hostapd

Wi-Fi 라우터를 기능을 추가하기 위해서는 Hostapd를 사용하였다.
특별한 설정 없이 `ht_capab`와 `vht_capab`를 이용하여 사용할 수 있는 Wi-Fi 기능을 활성화하면, 최대 성능을 사용할 수 있었다.

## 결론

기성 Wi-Fi 라우터는 좋은 가격에 괜찮은 성능을 제공하지만, 내가 만족할 만큼 커스터마이징이 불가능했다.
따라서, Intel 기반의 DIY Wi-Fi 라우터를 제작 및 설정하였다.
이 라우터는 기성 라우터 대비 가격은 높지만, 커스터마이징이 매우 쉬우며 높은 성능을 제공할 수 있었다.

## Update (2023. 2. 22.)

최근 커널[^2]에서는 아래와 같은 메시지가 나타나면서 [`ath10k-firmware` GitHub 저장소](https://github.com/kvalo/ath10k-firmware)에서 제공하는 펌웨어가 호환되지 않는다.

```log
[ 2060.576275] ath10k_pci 0000:01:00.0: No allocated memory for IRAM back up
[ 2060.576281] ath10k_pci 0000:01:00.0: failed to copy target iram contents: -12
[ 2060.652476] ath10k_pci 0000:01:00.0: could not init core (-12)
[ 2060.652486] ath10k_pci 0000:01:00.0: could not probe fw (-12)
```

이 현상은 최근 ath10 드라이버에 추가된 [iram recovery 기능](https://github.com/torvalds/linux/commit/9af7c32ceca85da27867dd863697d2aafc80a3f8) 때문이다.
`ath10k-firmware` 저장소에서 제공하는 QCA6174 펌웨어는 실제로는 iram recovery 기능을 제공하지 않으면서 iram recovery feature flag를 설정하는 것으로 추정된다.
예전 드라이버에서는 관련 flag를 확인하지 않고 관련 기능을 설정하지 않아서 문제가 되지 않았지만, 최신 버전의 드라이버에서는 펌웨어에 설정된 flag를 확인하고 iram recovery 기능을 활성화하다 오류가 발생한 것으로 보인다.

이를 해결하기 위해서는 드라이버를 수정하여 iram recovery 기능을 삭제하거나, firmware 파일을 수정하여 iram recovery flag를 비활성화해야 한다.
다행히 다음 [GitHub 저장소](https://github.com/tiiuae/wifi-firmware)에서 iram recovery flag를 비활성화한 버전의 QCA6174 수정 펌웨어를 배포하고 있다.
기존에 사용하는 펌웨어를 이 버전으로 교체하니, 다시 정상 작동하게 되었다.

[^1]: [QWA-AC2600](https://www.qnap.com/en-us/product/qwa-ac2600)와 같은 하나의 PCIe 슬롯에 장착하여 두 개의 WLAN 인터페이스를 제공하는 카드도 있지만, 팬이 달려있고 가격도 너무 비싸 고려하지 않았다.
[^2]: 나는 Debian Bookworm으로 업그레이드 하면서 현상이 발생하였다. 사용하는 커널 버전은 6.1.8이다.
