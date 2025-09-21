ENTRY(reset_handler)

MEMORY {
    ROM (rx)  : ORIGIN = 0x00000000, LENGTH = 64K
    RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 64K
}

SECTIONS {
    .vectors : { KEEP(*(.vectors)) } > ROM

    .text : { *(.text*) *(.rodata*) } > ROM

    .data : { *(.data*) *(.bss*) } > RAM
}

