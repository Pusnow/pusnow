---
title: Size of Standard Types
date: 2021-06-06
tags:
    - system
draft: true
---

Note: architectures without parentheses mean Linux

| Types         | x86_64 | x86_64 (Windows) | x86_64 (macOS) | i386 | i386 (Windows) | aarch64 | aarch64 (macOS) | armv7 |
|---------------|--------|------------------|----------------|------|----------------|---------|-----------------|-------|
| `short`       |        |                  | 2              |      |                |         |                 |       |
| `int`         |        |                  | 4              |      |                |         |                 |       |
| `long`        |        |                  | 8              |      |                |         |                 |       |
| `long long`   |        |                  | 8              |      |                |         |                 |       |
| `float`       |        |                  | 4              |      |                |         |                 |       |
| `double`      |        |                  | 8              |      |                |         |                 |       |
| `long double` |        |                  | 16             |      |                |         |                 |       |
| `void*`       |        |                  | 8              |      |                |         |                 |       |

## Compilers

- Windows: MSVC
- macOS: Clang 12.0.5
- Linux: GCC

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

