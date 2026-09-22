/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 ATEK MIDAS
 */

#ifndef HW_H
#define HW_H

#include "stm32f0xx_hal.h"
#include <stdint.h>
#include <stdbool.h>

#define PORT_CTRL1 GPIOA
#define PIN_CTRL1  GPIO_PIN_0

#define PORT_CTRL2 GPIOA
#define PIN_CTRL2  GPIO_PIN_1

#define PORT_CTRL3 GPIOA
#define PIN_CTRL3  GPIO_PIN_2

#define PORT_CTRL4 GPIOA
#define PIN_CTRL4  GPIO_PIN_3

#define PORT_CTRL5 GPIOA
#define PIN_CTRL5  GPIO_PIN_4

#define PORT_BTN_LEFT  GPIOC
#define PIN_BTN_LEFT   GPIO_PIN_13

#define PORT_BTN_RIGHT GPIOA
#define PIN_BTN_RIGHT  GPIO_PIN_9

typedef struct {
    GPIO_TypeDef* port;
    uint16_t pin;
} IOPin_t;


void HW_Init(void);
void HW_PlayBootAnimation(void);
void HW_SetCtrlPins(const IOPin_t* pins, uint8_t val, uint8_t num_pins);
void HW_SetDac(uint8_t val);
bool HW_GetButtonLeft(void);
bool HW_GetButtonRight(void);
void HW_UpdateDisplay(const char* top_text, const char* main_text, bool is_degree);
uint32_t HW_GetTicks(void);

#endif // HW_H
