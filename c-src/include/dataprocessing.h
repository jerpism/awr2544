#ifndef DATAPROCESSING_H
#define DATAPROCESSING_H
#include <stdint.h>
#include <drivers/hwa.h>

void calc_abs_vals(int16_t *in, uint16_t *out, uint32_t n);
void calc_doppler_fft(HWA_Handle hwahandle, void *in, void *out);
void dp_cfar(uint8_t rx, uint8_t chirp, void *data, size_t n);


#endif /* DATAPROCESSING_H */
