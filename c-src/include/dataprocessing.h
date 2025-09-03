#ifndef DATAPROCESSING_H
#define DATAPROCESSING_H
#include <stdint.h>
#include <drivers/hwa.h>

void calc_abs_vals(int16_t *in, uint16_t *out, uint32_t n);
void process_data(void *data, uint8_t rx_cnt, uint8_t chirps, uint8_t rbins);

#endif /* DATAPROCESSING_H */
