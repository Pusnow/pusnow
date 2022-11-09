---
title: DinV (Docker-in-VM)
date: 2022-01-31
tags:
    - system
lang: ko-kr
---

* [Source code available](https://github.com/Pusnow/dinv)

간혹 Docker를 Docker 컨테이너 안에서 실행시켜야 하는 경우가 있다.
특히, CI 서비스([Jenkins Docker](https://plugins.jenkins.io/docker-plugin/), [GitHub Docker Container Action](https://docs.github.com/en/actions/creating-actions/creating-a-docker-container-action), [GitLab Docker executor](https://docs.gitlab.com/runner/executors/docker.html))를 Docker를 통하여 배포할 때, Docker 이미지를 빌드할 수 없는 문제가 생긴다.
이는 Docker 이미지를 빌드하기 위해 필요한 `dockerd` 데몬이 많은 시스템 권한을 요구하기 때문이다.

## 기존 솔루션

지금까지 `dockerd`를 컨테이너 안에서 실행시키기 위해서는 DooD (Docker-out-of-Docker) 혹은 [DinD (Docker-in-Docker)](https://jpetazzo.github.io/2015/09/03/do-not-use-docker-in-docker-for-ci/) 기법을 사용한다.
DooD 기법은 컨테이너 내부에서 호스트 `dockerd`에 연결하여 사용하는 기법으로, 이를 위해 도커 컨트롤 소켓(`/var/run/docker.sock`)을 bind mount 하여 사용한다.
이 기법은 컨테이너가 호스트 `dockerd`에 대한 거의 모든 접근 권한을 가지기 때문에, 컨테이너 isolation을 회피하여 다른 컨테이너에 영향을 줄 수 있다.
DinD 기법은 `dockerd`를 컨테이너 안에서 실행시키기 위해 privileged 컨테이너를 사용한다. Privileged 컨테이너는 일반 Docker 컨테이너와 달리, [모든 권한](https://docs.docker.com/engine/reference/commandline/run/#full-container-capabilities---privileged)을 가져간다. 따라서, 호스트가 수행할 수 있는 모든 작업을 시행할 수 있다는 것을 의미한다.
따라서, DooD와 DinD 모두 실제 사용하기에는 보안 고려사항 때문에 쉽게 적용하기가 어렵다.

[Sysbox](https://github.com/nestybox/sysbox)는 이 문제를 해결하기 위해 등장했다. 이는 Docker 런타임과 호환되는 `runc` 구현체로, Linux user-namespace와 시스템 파티션(`/sys`, `/proc` 등)을 흉내 내는 OS shim으로 구성되어 있다. 이를 통해 `dockerd`를 privileged 권한 없이 실행할 수 있게 된다.
하지만, 이와 같은 솔루션은 호스트 측에 추가적인 런타임을 설치해야 하며, 따로 관리해주어야 하는 단점이 존재한다.

## Virtualization 기법

기존 솔루션을 검토해본 결과 다음과 같은 조건을 모두 만족하는 솔루션은 없었다.

* 최소한의 권한 사용 (unprivileged, `dockerd` isolation)
* Docker 혹은 podman 런타임에서 실행 가능 (추가적인 host-side 런타임 설치 불필요)
* CI 용으로 사용하므로 높은 성능은 불필요

이 경우 VM 기술을 사용하면 모든 조건을 만족할 수 있다.
VM을 이용하여 host 측과 격리된 Linux를 실행하게 되면, host에 영향 없이 Linux의 모든 기능을 사용할 수 있어서, `dockerd`를 실행 할 수 있게 된다.
또한, VM을 사용하기 위해서는 `kvm` 디바이스 드라이버 권한만 필요하므로, 권한 부여를 최소화 할 수 있다.
비록 가상화 오버헤드 때문에 성능(특히 I/O)은 저하될 수 있는데, 이는 CI 환경이므로 큰 문제가 되지 않는다.

## DinV (Docker-in-VM)

따라서, Docker를 이용해 쉽게 사용할 수 있는 DinV를 만들었다 (엄밀히는 Docker-in-VM-in-Docker).
DinV 컨테이너는 가벼운 [QEMU microVM](https://qemu.readthedocs.io/en/latest/system/i386/microvm.html)을 실행하여, 가벼운 리눅스 가상 머신 ([Alpine Linux](https://www.alpinelinux.org/) 기반)과 `dockerd`를 실행한다.
또한 [SLIRP](https://wiki.qemu.org/Documentation/Networking#User_Networking_.28SLIRP.29)와 [virtio-9p](https://wiki.qemu.org/Documentation/9psetup)를 이용하여 port binding과 bind mount를 제공한다.

### microVM

QEMU microVM은 가벼운 가상 머신으로 작은 이미지 사이즈 및 빠른 부팅 속도와 같은 장점을 가지고 있다.
DinV에서는 microVM을 이용하여 VM 인스턴스를 제공한다[^1].

### SLIRP

SLIRP(혹은 user networing)는 QEMU에서 제공하는 기본적인 네트워킹 방식이다.
TAP 네트워킹 방식과 비교하여 성능은 떨어지지만, port forwarding 기능을 쉽게 제공할 수 있고, `CAP_NET_ADMIN`과 같은 추가적인 권한을 요구하지 않기 때문에 DinV에서는 SLIRP를 사용한다.

단, 이 때문에, SLIRP가 가지는 몇 단점(낮은 성능 및 ICMP 미작동)을 가지게 된다.

### virtio-9p

Bind mount는 컨테이너와 호스트 간에 shared file system을 구성하는 기능이다.
하나의 커널을 사용하는 Docker 컨테이너와 달리, VM과 호스트 간 shared file system을 만드는 것은 조금 어려운 일이다.
이를 위해서 대부분의 기존 구현체([Docker for Desktop](https://www.docker.com/products/docker-desktop), [Podman Machine](https://docs.podman.io/en/latest/markdown/podman-machine.1.html))는 대부분 [SSHFS](https://github.com/libfuse/sshfs)를 사용하여 구성한다.
SSHFS는 추가적인 SSH 관리가 필요하고, 낮은 성능을 가지기 때문에 DinV에서는 사용하지 않고, 가상화를 이용한 기술을 검토하여 도입했다.

QEMU에서 지원하는 가상화 기반 shared file system은 두 가지가 존재한다: [virtio-9p](https://wiki.qemu.org/Documentation/9psetup), [virtio-fs](https://virtio-fs.gitlab.io).
대부분의 경우 virtio-fs 훨씬 높은 성능을 [보여주지만](https://vmsplice.net/~stefan/virtio-fs_%20A%20Shared%20File%20System%20for%20Virtual%20Machines.pdf), 아직 QEMU microVM에서는 이를 지원하지 못한다[^2].
따라서 DinV에서는 virtio-9p를 이용하여 bind mount를 지원한다.

## 사용법

자세한 사용법은 [GitHub repo](https://github.com/Pusnow/dinv)에서 확인 가능하다.

## 자세한 기술적 내용

### Graceful shutdown

CI 워크플로에서는 큰 필요가 없을 수도 있지만, DinV는 graceful shutdown을 지원한다.
QEMU에서 graceful shutdown을 지원하는 것은 hard shutdown (`SIGINT`로 호출됨)과 달리 조금 노력이 필요하다.

QEMU에서 graceful shutdown을 수행하기 위해서는, 가장 먼저 guest-side에 shutdown 시그널을 보내야 한다.
이를 위해서 QEMU는 [ACPI와 QEMU Guest Agent 두 가지 방법을 지원하는데](https://pve.proxmox.com/wiki/QEMU/KVM_ACPI_Guest_Shutdown), DinV에서 사용하는 microVM은 ACPI 지원이 빠져 있으므로, DinV는 QEMU Guest Agent를 사용한다.
이를 위하여, DinV가 사용하는 VM 이미지는 QEMU Guest Agent 및 관련 커널 모듈(`virtio_console`)을 추가로 활성화한다.

Docker에서는 컨테이너를 shutdown 할 때 (`docker stop`), 기본적으로 `SIGTERM` 시그널을 사용하고 특정 시간이 지나면 `SIGKILL`을 사용한다.
DinV의 Docker entrypoint는 이와 같은 시그널을 처리하기 위하여 `SIGTERM` 핸들러를 설치하고, 이 핸들러에서는 QEMU Guest Agent 콘솔로 종료 명령을 전달한다.
이와 같은 방식으로, `docker stop` -> `SIGTERM` -> `Handler` -> `Guest Agent` -> `Shutdown` 순으로 graceful shutdown이 진행된다.

마지막으로, 조금 더 안전한 graceful shutdown을 위하여 DinV의 [`shutdown-timeout`](https://docs.docker.com/engine/reference/commandline/dockerd/)을 호스보다 낮은 값으로 설정하여 DinV의 `dockerd`가 종료되기 전에 컨테이너 shutdown timeout이 발생하여 `SIGKILL`로 강제 종료되는 상황을 방지하였다.

### Port forwarding

VM안에서 `dockerd`를 아무런 설정 없이 실행하면, port forwarding이 정상적으로 동작하지 않을 수 있다.
이는 host docker 네트워크와 컨테이너 네트워크 간 IP 충돌이 발생하기 때문이다. 두 네트워크 모두 `172.17.0.0/16` 대역(`dockerd` 기본 값)을 사용하므로 VM 안에서 `172.17.0.0/16` 대역을 조회할 때, routing이 host와 container network를 구분하지 못하기 때문이다.

따라서, DinV는 `dockerd`에 `--bip` (bridge IP) 옵션을 사용하여 container network의 IP 대역을 `172.19.0.0/16`으로 변경하여 해결하였다.
이렇게 해야만, host network와 container network를 구분이 가능하다.

```goat
┌─ host network ─────────────────────┐
│                                    │
│  Network: 172.17.0.0/16            │
│                                    │
│┌─ VM container ───────────────────┐│
││                                  ││
││  IP: 172.17.0.3/16               ││
││                                  ││
││┌─ container network ────────────┐││
│││                                │││
│││  Network: 172.19.0.0/16        │││
│││                                │││
│││┌─ container ──────────────────┐│││
││││                              ││││
││││  IP: 172.19.0.3/16           ││││
││││                              ││││
│││└──────────────────────────────┘│││
││└────────────────────────────────┘││
│└──────────────────────────────────┘│
└────────────────────────────────────┘ 
```

[^1]: 사실 DinV를 위해 꼭 microVM을 사용해야 하는 것은 아니다.
[^2]: QEMU microVM에서는 PCI를 에뮬레이션하지 않고 virtio-mmio기반 디바이스만 지원한다. virtio-fs를 사용하기 위해서는
 vhost-user-fs 디바이스가 필요한데, 이 디바이스는 PCI만 지원하기 때문에 (`vhost-user-fs-pci`) microVM에서는 사용할 수 없다.
