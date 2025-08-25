#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <hwa.h>
#include <cfg.h>
#include "ti_drivers_config.h"
#define SQUARE_I16(x) (((int32_t)x) * ((int32_t)x))

// Input/output MUST be 4 byte aligned
void calc_doppler_fft(HWA_Handle hwahandle, void *in, void *out){
    //TODO: change these to macros even though it's unlikely they'll change.
    //Also implement it for all receivers and make it transfer the other half

    uint32_t *inp = (uint32_t*)in;
    uint32_t *outp = (uint32_t*)out;

    for(size_t i = 0; i < 64; ++i){
        for(size_t j = 0; j < 128; ++j){
            outp[i * 128 + j] = *(inp + j * 128 * NUM_RX_ANTENNAS + i);
        }
    }


   hwa_process_dfft(hwahandle, NULL);
}

// N is the number of samples
// as they are complex numbers, each one consists of 2 16 bit signed integers I and Q
void calc_abs_vals(int16_t *in, int16_t *out, uint32_t n){
    for(int32_t i = 0; i < n; i++){
        out[i] = (int16_t)sqrt(SQUARE_I16(in[i * 2]) + SQUARE_I16(in[i * 2 + 1]));

    }
}