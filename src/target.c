#include <stdio.h>
#include <stdint.h>

#define STACK_TOP   0x20008000
#define INPUT_ADDR  0x20000100

void reset_handler(void);
void hardfault_handler(void);
static void semihosting_exit(int status);

// 中断向量表
__attribute__((section(".vectors"))) void (*const vectors[])(void) = {
    (void (*)(void))STACK_TOP,
    reset_handler,
    0, 0, 0, 0,
    hardfault_handler
};

// 死循环的 HardFault
void hardfault_handler(void) {
    while (1) {}
}

// semihosting exit for normal termination
static void semihosting_exit(int status) {
    register int r0 __asm__("r0") = 0x18;
    register int r1 __asm__("r1") = status;
    __asm__ volatile ("bkpt #0xAB" : : "r"(r0), "r"(r1));
}

/* semihosting getchar implementation (works when semihosting is supported) */
static int host_getchar(void) {
    int ch;
    /* semihosting SYS_READC is operation 0x07, using bkpt 0xAB convention */
    asm volatile (
        "mov r0, #7\n"      /* SYS_READC */
        "bkpt 0xAB\n"       /* semihosting */
        "mov %0, r0\n"
        : "=r"(ch)          /* output */
        :                   /* no inputs */
        : "r0"              /* clobbered registers */
    );
    return ch;
}

/* reset_handler: supports two modes:
 *  - USE_STDIN: read up to 7 bytes from stdin (suitable for AFL / pipe)
 *  - default: read from memory at INPUT_ADDR (your original approach)
 */

void reset_handler(void) {
    char buf[8] = {0};

#ifdef USE_STDIN
    /* stdin-based harness: read up to 7 bytes from stdin via host_getchar() */
    for (int i = 0; i < 7; ++i) {
        int c = host_getchar();   /* use semihosting getchar */
        if (c == EOF || c == '\0' || c == '\n') break;
        buf[i] = (char)c;
    }
#else
    /* memory-mapped input harness: read from designated RAM region */
    volatile char *input = (volatile char *)INPUT_ADDR;
    for (int i = 0; i < 7; ++i) {
        char c = input[i];
        if (c == '\0' || c == '\n') break;
        buf[i] = c;
    }
#endif

    /* example check: CRASHME triggers explicit fault */
    if (buf[0]=='C' && buf[1]=='R' && buf[2]=='A' &&
        buf[3]=='S' && buf[4]=='H' && buf[5]=='M' && buf[6]=='E') {
        volatile int *crash = (int *)0xFFFFFFFF; /* force fault */
        *crash = 0xDEAD;
    }

    /* normal termination */
    semihosting_exit(0);
}

