#ifndef RF_MODULES_H
#define RF_MODULES_H

#include <stdint.h>
#include <stdbool.h>

// Modül Listesi
typedef enum {
  ATEK357P4,  // 5-Bit Attenuator
  ATEK888P5,  // Tunable LPF
  ATEK950P6,  // Filterbank 8
  ATEK656N5,  // Filterbank 6
  ATEK256N3,  // SPDT Switch
  ATEK366P5   // Phase Shifter (DAC)
} ModuleType_t;

// Projedeki Tüm Fonksiyon Prototipleri
void RF_Init(ModuleType_t module);
void RF_HandleButtons(void);
void RF_Update(void);
void RF_ProcessSerialCommand(void);
void RF_FeedCDCData(uint8_t* Buf, uint32_t Len);

#endif // RF_MODULES_H
