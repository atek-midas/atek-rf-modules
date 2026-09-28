/*
 * SPDX-License-Identifier: MIT
 * Copyright (c) 2026 ATEK MIDAS
 */

#ifndef RF_MODULES_H
#define RF_MODULES_H

#include <stdint.h>
#include <stdbool.h>

// RF Modules List
// Module names follow https://atekmidas.com/products/modules/ (the name is also the *IDN? response).
// NOTE: only ATEK1801 and ATEK1601 have ready hardware. The other entries are
//       HW NOT READY: module assignment not yet confirmed, pin mapping not verified.
typedef enum {
  ATEK1231,     // 5-Bit Attenuator         (HW not ready)
  ATEK1801,     // Tunable LPF
  ATEK1001,     // Filterbank 8             (HW not ready)
  ATEK1601,     // Filterbank 6
  ATEK1202,     // SPDT Switch              (HW not ready, ATEK1201 or ATEK1202 to be confirmed)
  ATEK_PS_TBD   // Phase Shifter (DAC)      (HW not ready, module name TBD, DAC not implemented)
} ModuleType_t;


void RF_Init(ModuleType_t module);
void RF_HandleButtons(void);
void RF_Update(void);
void RF_ProcessSerialCommand(void);
void RF_FeedCDCData(uint8_t* Buf, uint32_t Len);

#endif // RF_MODULES_H
