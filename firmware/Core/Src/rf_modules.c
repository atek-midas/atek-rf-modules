/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 ATEK MIDAS
 */


#include "rf_modules.h"
#include "hw.h"
#include "main.h"
#include "usbd_cdc_if.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static ModuleType_t current_module;
static int current_state = 0;
static int max_states = 0;
static bool state_changed = true;

static uint32_t last_button_time = 0;
static uint32_t button_press_start_time = 0;
#define BUTTON_REPEAT_DELAY 200
#define FAST_SCROLL_DELAY 2000

/*
 *#define LEFT_BTN_Pin GPIO_PIN_13
#define LEFT_BTN_GPIO_Port GPIOC
#define IO8_Pin GPIO_PIN_4
#define IO8_GPIO_Port GPIOA
#define IO7_Pin GPIO_PIN_5
#define IO7_GPIO_Port GPIOA
#define IO6_Pin GPIO_PIN_6
#define IO6_GPIO_Port GPIOA
#define IO5_Pin GPIO_PIN_7
#define IO5_GPIO_Port GPIOA
#define IO10_Pin GPIO_PIN_1
#define IO10_GPIO_Port GPIOB
#define IO9_Pin GPIO_PIN_2
#define IO9_GPIO_Port GPIOB
#define IO4_Pin GPIO_PIN_12
#define IO4_GPIO_Port GPIOB
#define IO3_Pin GPIO_PIN_13
#define IO3_GPIO_Port GPIOB
#define IO2_Pin GPIO_PIN_14
#define IO2_GPIO_Port GPIOB
#define IO1_Pin GPIO_PIN_15
#define IO1_GPIO_Port GPIOB
#define RIGHT_BTN_Pin GPIO_PIN_9
#define RIGHT_BTN_GPIO_Port GPIOA
#define IO11_Pin GPIO_PIN_3
#define IO11_GPIO_Port GPIOB
#define IO12_Pin GPIO_PIN_4
#define IO12_GPIO_Port GPIOB
#define IO13_Pin GPIO_PIN_5
#define IO13_GPIO_Port GPIOB
#define IO14_Pin GPIO_PIN_6
#define IO14_GPIO_Port GPIOB
#define IO15_Pin GPIO_PIN_7
#define IO15_GPIO_Port GPIOB

 */

const IOPin_t Q1 = {GPIOB, GPIO_PIN_15};
const IOPin_t Q2 = {GPIOB, GPIO_PIN_14};
const IOPin_t Q3 = {GPIOB, GPIO_PIN_13};
const IOPin_t Q4 = {GPIOB, GPIO_PIN_12};
const IOPin_t Q5 = {GPIOA, GPIO_PIN_7};

const IOPin_t Q6 = {GPIOA, GPIO_PIN_6};
const IOPin_t Q7 = {GPIOA, GPIO_PIN_5};
const IOPin_t Q8 = {GPIOA, GPIO_PIN_4};
const IOPin_t Q9 = {GPIOB, GPIO_PIN_2};
const IOPin_t Q10 = {GPIOB, GPIO_PIN_1};

const IOPin_t Q11 = {GPIOB, GPIO_PIN_3};
const IOPin_t Q12 = {GPIOB, GPIO_PIN_4};
const IOPin_t Q13 = {GPIOB, GPIO_PIN_5};
const IOPin_t Q14 = {GPIOB, GPIO_PIN_6};
const IOPin_t Q15 = {GPIOB, GPIO_PIN_7};


// MSB to LSB ordering

// LSB to MSB ordering
const IOPin_t PINS_ATEK656N5[] = { Q5, Q4, Q3 };
const IOPin_t PINS_ATEK888P5[] = { Q8, Q7, Q6, Q9, Q11 };

const IOPin_t PINS_ATEK357P4[] = { {GPIOA, GPIO_PIN_1}, {GPIOA, GPIO_PIN_2}, {GPIOA, GPIO_PIN_3}, {GPIOA, GPIO_PIN_4}, {GPIOA, GPIO_PIN_5} }; // HW not ready
const IOPin_t PINS_ATEK950P6[] = { {GPIOC, GPIO_PIN_0}, {GPIOC, GPIO_PIN_1}, {GPIOC, GPIO_PIN_2} };// HW not ready
const IOPin_t PINS_ATEK256N3[] = { {GPIOA, GPIO_PIN_8} };// HW not ready
// DAC Module (ATEK366P5) No physical discrete connection

typedef struct {
    const char* name;          // Module name shown on the display
    uint8_t num_pins;          // Number of control pins
    uint8_t max_states;        // Number of states
    bool is_dac;               // Uses DAC?
    const IOPin_t* ctrl_pins;  // Pointer to this module's control pin array
} RF_Module_t;

const RF_Module_t modules[] = {
    {"ATEK357P4", 5, 32, false, PINS_ATEK357P4},
    {"ATEK888P5", 5, 32, false, PINS_ATEK888P5},
    {"ATEK950P6", 3, 8,  false, PINS_ATEK950P6},
    {"ATEK656N5", 3, 6,  false, PINS_ATEK656N5},
    {"ATEK256N3", 1, 2,  false, PINS_ATEK256N3},
    {"ATEK366P5", 0, 0,  true,  NULL} // No pin array (NULL)
};

// --- Lookup tables ---
const uint8_t atek950p6_codes[] = {0x00, 0x06, 0x04, 0x05, 0x02, 0x01, 0x03, 0x07};

const char* atek950p6_freqs[] = {"485 - 810", "670 - 1125", "960 - 1670", "1440-2560", "2140-3850", "3300-5880", "4820-8500", "2 - 9000"}; // :TODO 4820-8500 or 4820-8000

const uint8_t ATEK1601_codes[] = {0x00, 0x05, 0x02, 0x03, 0x01, 0x04};
const char* atek656n5_freqs[] = {"1.9 - 3.5", "2.8 - 5.4", "4.5 - 9.1", "7.1 - 12.3", "9.9 - 15.3", "12.5 - 18"};

const uint16_t atek888p5_freqs[] = {27, 28, 29, 30, 31, 32, 33, 34, 48, 51, 55, 58, 68, 75, 95, 112, 150, 155, 160, 164, 168, 172, 176, 180, 230, 245, 265, 285, 310, 350, 425, 550};

const uint8_t atek256n3_codes[] = {0x00, 0x01};

const uint8_t atek357p4_codes[] = {
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
  0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F
};

const uint8_t ATEK1801_codes[] = {
  0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F,
  0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F
};

void RF_Init(ModuleType_t module) {
  current_module = module;
  current_state = 0;
  state_changed = true;

  switch (current_module) {
    case ATEK357P4: max_states = 32; break;
    case ATEK1801: max_states = 32; break;
    case ATEK950P6: max_states = 8;  break;
    case ATEK1601: max_states = 6;  break;
    case ATEK256N3: max_states = 2;  break;
    case ATEK366P5: max_states = 101; break;
  }
}

void RF_HandleButtons(void) {
  uint32_t current_time = HW_GetTicks();

  bool left_pressed = HW_GetButtonLeft();
  bool right_pressed = HW_GetButtonRight();

  if (left_pressed || right_pressed) {
    if (button_press_start_time == 0) {
      button_press_start_time = current_time;
    }

    if (current_time - last_button_time > BUTTON_REPEAT_DELAY) {
      uint32_t hold_duration = current_time - button_press_start_time;

      int step = 1;
      if (hold_duration > FAST_SCROLL_DELAY && current_module == ATEK366P5) {
        step = 10;
      }

      	 // Button direction fixed (left/right were swapped)
      if (right_pressed) {
        if (current_state > 0) {
          current_state -= step;
          if (current_state < 0) current_state = 0;
          state_changed = true;
        }
        last_button_time = current_time;
      }
      else if (left_pressed ) {
        if (current_state < (max_states - 1)) {
          current_state += step;
          if (current_state >= max_states) current_state = max_states - 1;
          state_changed = true;
        }
        last_button_time = current_time;
      }
    }
  }
  else {
    button_press_start_time = 0;
  }
}


void RF_Update(void) {
    if (!state_changed) return;
    state_changed = false;

    // Send data to PC to sync UI
    char state_msg[16];
    snprintf(state_msg, sizeof(state_msg), "STATE:%d\r\n", current_state);
    CDC_Transmit_FS((uint8_t*)state_msg, strlen(state_msg));
    //
    char main_val[16];
    char top_val[20] = "";

    // Generic pin handling:
    // each module's own control pins are passed via modules[current_module].ctrl_pins.

    switch (current_module) {
        case ATEK357P4:
            HW_SetCtrlPins(modules[current_module].ctrl_pins, atek357p4_codes[current_state], modules[current_module].num_pins);
            snprintf(top_val, sizeof(top_val), "ATT (dB)");
            snprintf(main_val, sizeof(main_val), "%d", current_state);
            HW_UpdateDisplay(top_val, main_val, false);
            break;

        case ATEK1801:
            HW_SetCtrlPins(modules[current_module].ctrl_pins, ATEK1801_codes[current_state], modules[current_module].num_pins);
            snprintf(top_val, sizeof(top_val), "B%d (MHz)", current_state + 1);
            snprintf(main_val, sizeof(main_val), "%d", atek888p5_freqs[current_state]);
            HW_UpdateDisplay(top_val, main_val, false);
            break;

        case ATEK950P6:
            HW_SetCtrlPins(modules[current_module].ctrl_pins, atek950p6_codes[current_state], modules[current_module].num_pins);
            if(current_state == 7) {
                snprintf(top_val, sizeof(top_val), "BYP (MHz)");
            } else {
                snprintf(top_val, sizeof(top_val), "B%d (MHz)", current_state + 1);
            }
            snprintf(main_val, sizeof(main_val), "%s", atek950p6_freqs[current_state]);
            HW_UpdateDisplay(top_val, main_val, false);
            break;

        case ATEK1601:
            HW_SetCtrlPins(modules[current_module].ctrl_pins, ATEK1601_codes[current_state], modules[current_module].num_pins);
            snprintf(top_val, sizeof(top_val), "B%d (GHz)", current_state + 1);
            snprintf(main_val, sizeof(main_val), "%s", atek656n5_freqs[current_state]);
            HW_UpdateDisplay(top_val, main_val, false);
            break;

        case ATEK256N3:
            HW_SetCtrlPins(modules[current_module].ctrl_pins, atek256n3_codes[current_state], modules[current_module].num_pins);
            snprintf(top_val, sizeof(top_val), "SPDT SW");
            snprintf(main_val, sizeof(main_val), "RF%d", current_state + 1);
            HW_UpdateDisplay(top_val, main_val, false);
            break;

        case ATEK366P5:
        {
            int volt_tam = current_state / 10;
            int volt_ondalik = current_state % 10;
            int angle = (current_state * 360) / 100;

            uint8_t dac_val = (uint8_t)((current_state * 255) / 100);
            HW_SetDac(dac_val);

            snprintf(top_val, sizeof(top_val), "PS %d.%dV", volt_tam, volt_ondalik);
            snprintf(main_val, sizeof(main_val), "%d", angle);
            HW_UpdateDisplay(top_val, main_val, true);
            break;
        }
    }
}

// --- USB CDC COMMUNICATION HANDLING ---
char rx_buffer[64];
uint8_t rx_index = 0;
bool cmd_ready = false;

// Parses incoming USB data byte by byte and assembles commands
void RF_FeedCDCData(uint8_t* Buf, uint32_t Len) {
    for (uint32_t i = 0; i < Len; i++) {
        uint8_t rx_byte = Buf[i];
        if (rx_byte == '\n' || rx_byte == '\r') {
            if (rx_index > 0) {
                rx_buffer[rx_index] = '\0';
                cmd_ready = true;
            }
        } else if (rx_index < 63) {
            rx_buffer[rx_index++] = rx_byte;
        }
    }
}

// --- JUMP TO SYSTEM MEMORY (ROM BOOTLOADER) ---
void JumpToBootloader(void) {
    // 1. Show bootloader info on the display
    HW_UpdateDisplay("SYSTEM", "BOOT MODE", false);

    // 2. Simulate a physical USB disconnect
    GPIO_InitTypeDef GPIO_InitStruct = {0};
    GPIO_InitStruct.Pin = GPIO_PIN_11 | GPIO_PIN_12;
    GPIO_InitStruct.Mode = GPIO_MODE_ANALOG; // Put USB pins in analog (high-Z) mode
    GPIO_InitStruct.Pull = GPIO_NOPULL;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    __HAL_RCC_USB_FORCE_RESET();
    for(volatile int i=0; i<1500000; i++); // Wait for the host to detect the disconnect
    __HAL_RCC_USB_RELEASE_RESET();
    __HAL_RCC_USB_CLK_DISABLE(); // Disable USB clock so the bootloader can re-initialize it

    // 3. Reset peripherals and SysTick without globally disabling IRQs
    HAL_DeInit();
    HAL_RCC_DeInit();
    SysTick->CTRL = 0;
    SysTick->LOAD = 0;
    SysTick->VAL = 0;

    // 4. Clear interrupts in the NVIC only (Cortex-M0)
    NVIC->ICER[0] = 0xFFFFFFFF; // Disable all interrupts
    NVIC->ICPR[0] = 0xFFFFFFFF; // Clear all pending interrupts

    // 5. Remap memory (vector table to system ROM)
    __HAL_RCC_SYSCFG_CLK_ENABLE();
    __HAL_SYSCFG_REMAPMEMORY_SYSTEMFLASH();

    // 6. STM32F070 ROM bootloader address
    volatile uint32_t addr = 0x1FFFC800;
    void (*SysMemBootJump)(void) = (void (*)(void)) (*((uint32_t *)(addr + 4)));

    // 7. Set stack pointer and jump
    __set_MSP(*(uint32_t *)addr);
    SysMemBootJump();

    while (1);
}

void RF_ProcessSerialCommand(void) {
    if (!cmd_ready) return;

    if (strncmp(rx_buffer, "*IDN?", 5) == 0) {
        char response[32];
        switch(current_module) {
            case ATEK357P4: strcpy(response, "ATEK357P4\r\n"); break;
            case ATEK1801: strcpy(response, "ATEK1801\r\n"); break;
            case ATEK950P6: strcpy(response, "ATEK950P6\r\n"); break;
            case ATEK1601: strcpy(response, "ATEK1601\r\n"); break;
            case ATEK256N3: strcpy(response, "ATEK256N3\r\n"); break;
            case ATEK366P5: strcpy(response, "ATEK366P5\r\n"); break;
            default: strcpy(response, "UNKNOWN\r\n"); break;
        }
        // Send response over USB (CDC)
        CDC_Transmit_FS((uint8_t*)response, strlen(response));
    }
    else if (strncmp(rx_buffer, "SET:", 4) == 0) {


		if (strncmp(&rx_buffer[4], "UPDATE", 6) == 0) {
			char response[] = "Entering DFU Mode...\r\n";
			CDC_Transmit_FS((uint8_t*)response, strlen(response));
			HAL_Delay(50); // Short delay to let the message go out over USB
			JumpToBootloader();
		}
		else {
			int new_state = atoi(&rx_buffer[4]);
			if (new_state >= 0 && new_state < max_states) {
				current_state = new_state;
				state_changed = true;
			}
		}


    }
    else if (strncmp(rx_buffer, "GET?", 4) == 0) {
            char response[16];
            snprintf(response, sizeof(response), "STATE:%d\r\n", current_state);
            CDC_Transmit_FS((uint8_t*)response, strlen(response));
     }


    memset(rx_buffer, 0, sizeof(rx_buffer));
    rx_index = 0;
    cmd_ready = false;
}
