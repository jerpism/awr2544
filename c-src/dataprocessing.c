#include <stdint.h>
#include <stdlib.h>
#include <math.h>
#include <hwa.h>
#include <cfg.h>
#include "ti_drivers_config.h"
#define SQUARE_I16(x) (((int32_t)x) * ((int32_t)x))

#define RANGEBINS (CFG_PROFILE_NUMADCSAMPLES / 2) 
// For how many rangebins can we calculate the doppler at once
// the HWA can fit 32k of input at once 
#define ITERATION_MAX (RANGEBINS / 2)   

// Store cfar result as a bit map to save on space
// don't change the name of this, it will break the macros
static uint32_t cfar[NUM_RX_ANTENNAS * CHIRPS_PER_FRAME * RANGEBINS];

//TODO: don't use magic numbers here but this should work for now
// Check if a specific data point was a detected object
#define CHECK_POINT(rx, chirp, point) ( cfar[(rx * chirp * 4) + (point / 32)] & (1U << (point % 32)) )
// Set a specific data point as a detected object
#define SET_POINT(rx, chirp, point) ( cfar[(rx * chirp * 4) + (point / 32 )] |= (1U << (point % 32)) )

// Input/output MUST be 4 byte aligned
void calc_doppler_fft(HWA_Handle hwahandle, void *in, void *out){
    //TODO: change these to macros even though it's unlikely they'll change.
    //Also implement it for all receivers and make it transfer the other half

    uint32_t *inp = (uint32_t*)in;
    uint32_t *outp = (uint32_t*)out;

    for(size_t i = 0; i < ITERATION_MAX; ++i){
        for(size_t j = 0; j < RANGEBINS; ++j){
            outp[i * RANGEBINS + j] = *(inp + j * RANGEBINS + i);
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