/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.h
  * @brief          : Header for main.c file.
  *                   This file contains the common defines of the application.
  ******************************************************************************
  * @attention
  *
  * Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.
  *
  * This software is licensed under terms that can be found in the LICENSE file
  * in the root directory of this software component.
  * If no LICENSE file comes with this software, it is provided AS-IS.
  *
  ******************************************************************************
  */
/* USER CODE END Header */

/* Define to prevent recursive inclusion -------------------------------------*/
#ifndef __MAIN_H
#define __MAIN_H

#ifdef __cplusplus
extern "C" {
#endif

/* Includes ------------------------------------------------------------------*/
#include "stm32f0xx_hal.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */


/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 ATEK MIDAS
 */


/* USER CODE END Includes */

/* Exported types ------------------------------------------------------------*/
/* USER CODE BEGIN ET */

/* USER CODE END ET */

/* Exported constants --------------------------------------------------------*/
/* USER CODE BEGIN EC */

/* USER CODE END EC */

/* Exported macro ------------------------------------------------------------*/
/* USER CODE BEGIN EM */

/* USER CODE END EM */

/* Exported functions prototypes ---------------------------------------------*/
void Error_Handler(void);

/* USER CODE BEGIN EFP */

/* USER CODE END EFP */

/* Private defines -----------------------------------------------------------*/
#define LEFT_BTN_Pin GPIO_PIN_13
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

/* USER CODE BEGIN Private defines */

/* USER CODE END Private defines */

#ifdef __cplusplus
}
#endif

#endif /* __MAIN_H */
