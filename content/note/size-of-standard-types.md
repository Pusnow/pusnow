---
title: Size of Standard Types
date: 2021-06-06
tags:
    - system
---

## Table

| Types         | x86_64 (Linux) | x86_64 (Windows) | x86_64 (macOS) | i386 (Linux) | i386 (Windows) | aarch64 (Linux) | aarch64 (macOS) | riscv64 (Linux) |
|---------------|:--------------:|:----------------:|:--------------:|:------------:|:--------------:|:---------------:|:---------------:|:---------------:|
| `short`       |       2        |        2         |       2        |      2       |       2        |        2        |                 |        2        |
| `int`         |       4        |        4         |       4        |      4       |       4        |        4        |                 |        4        |
| `long`        |       8        |        4         |       8        |      4       |       4        |        8        |                 |        8        |
| `long long`   |       8        |        8         |       8        |      8       |       8        |        8        |                 |        8        |
| `float`       |       4        |        4         |       4        |      4       |       4        |        4        |                 |        4        |
| `double`      |       8        |        8         |       8        |      8       |       8        |        8        |                 |        8        |
| `long double` |       16       |        8         |       16       |      12      |       8        |       16        |                 |       16        |
| `void*`       |       8        |        8         |       8        |      4       |       4        |        8        |                 |        8        |

## Compilers

- Windows: Visual Studio 2019
- macOS: Apple Clang 1
- Linux: GCC 8

## Source Code

```c
#include <stdio.h>

int main(){
    printf("short: %lu\n", sizeof(short));
    printf("int: %lu\n", sizeof(int));
    printf("long: %lu\n", sizeof(long));
    printf("long long: %lu\n", sizeof(long long));
    printf("float: %lu\n", sizeof(float));
    printf("double: %lu\n", sizeof(double));
    printf("long double: %lu\n", sizeof(long double));
    printf("void*: %lu\n", sizeof(void*));
    return 0;
}
```

