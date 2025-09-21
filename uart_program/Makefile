BINARY := uart_test.elf

CMSIS := ../CMSIS_5
LINKER_SCRIPT = ./gcc_uart.ld


SRC_ASM := $(CMSIS)/Device/ARM/ARMCM3/Source/GCC/startup_ARMCM3.S
SRC_C := $(CMSIS)/Device/ARM/ARMCM3/Source/system_ARMCM3.c \
         main.c \
         uart.c

INCLUDE_FLAGS := \
  -I$(CMSIS)/Device/ARM/ARMCM3/Include \
  -I$(CMSIS)/CMSIS/Core/Include \
  -I.

CFLAGS := \
  -mcpu=cortex-m3 \
  -mthumb \
  -Wall \
  -g \
  -O0 \
  -nostartfiles \
  -ffunction-sections \
  -fdata-sections \
  -Wl,--gc-sections

CC := arm-none-eabi-gcc
OBJ := arm-none-eabi-objdump

all: $(BINARY)

$(BINARY): $(SRC_ASM) $(SRC_C)
	$(CC) $(CFLAGS) $(INCLUDE_FLAGS) -T $(LINKER_SCRIPT) $^ -o $@
	$(OBJ) -D $(BINARY) > $(BINARY:.elf=.objdump)

clean:
	rm -f $(BINARY) *.o *.objdump

