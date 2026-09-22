#ifndef RF_MODULES_H
#define RF_MODULES_H

#include <stdint.h>
#include <stdbool.h>

// RF Modules List
typedef enum {
  ATEK357P4,  	// 5-Bit Attenuator 	, Chip MFG#:
  ATEK1801,  	// Tunable LPF 			, Chip MFG#: ATEK888P5
  ATEK950P6,  	// Filterbank 8 		, Chip MFG#:
  ATEK1601,  	// Filterbank 6 		,  Chip MFG#: ATEK656N5
  ATEK256N3,  	// SPDT Switch 			, Chip MFG#:
  ATEK366P5   	// Phase Shifter (DAC) 	, Chip MFG#:
} ModuleType_t;


void RF_Init(ModuleType_t module);
void RF_HandleButtons(void);
void RF_Update(void);
void RF_ProcessSerialCommand(void);
void RF_FeedCDCData(uint8_t* Buf, uint32_t Len);

#endif // RF_MODULES_H
