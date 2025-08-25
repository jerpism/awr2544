#ifndef DATAPROCESSING_H
#define DATAPROCESSING_H
#include <stdint.h>
#include <drivers/hwa.h>

void calc_abs_vals(int16_t *in, int16_t *out, uint32_t n);
void calc_doppler_fft(HWA_Handle hwahandle, void *in, void *out);

#endif /* DATAPROCESSING_H */
