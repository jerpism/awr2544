#include <stdint.h>
#include <stdlib.h>
#include <math.h>

#include <cfg.h>
#define SQUARE_I16(x) (((int32_t)x) * ((int32_t)x))

void dfft_move_cols(uint32_t *in, uint32_t *out){
    for(size_t i = 0; i < 64; ++i){
        for(size_t j = 0; j < 128; ++j){
            out[i * 128 + j] = *(in + j * CHIRPS_PER_FRAME * NUM_RX_ANTENNAS + i );
        }
    }
}

// N is the number of samples
// as they are complex numbers, each one consists of 2 16 bit signed integers I and Q
void calc_abs_vals(int16_t *in, int16_t *out, uint32_t n){
    for(int32_t i = 0; i < n; i++){
        out[i] = (int16_t)sqrt(SQUARE_I16(in[i * 2]) + SQUARE_I16(in[i * 2 + 1]));

    }
}