TARGET = target.elf

# find C sources in src/
SRC := $(wildcard src/*.c)

# toolchain
CC = arm-none-eabi-gcc

# common flags
CFLAGS := -nostdlib -mcpu=cortex-m3 -mthumb -O0 -g -Wall -fno-builtin

# explicit linker script path (src/gcc_uart.ld)
LDSCRIPT := src/gcc_uart.ld

LDFLAGS := -T $(LDSCRIPT) -nostdlib -Wl,-e,reset_handler

.PHONY: all all-stdin clean

all: $(TARGET)

$(TARGET): $(SRC)
	@echo "[make] Using linker script: $(LDSCRIPT)"
	$(CC) $(CFLAGS) -o $@ $(SRC) $(LDFLAGS)

all-stdin:
	@echo "[make] Building stdin-enabled (USE_STDIN) using linker script: $(LDSCRIPT)"
	$(CC) $(CFLAGS) -DUSE_STDIN -o $(TARGET) $(SRC) $(LDFLAGS)

clean:
	rm -f *.o *.elf
