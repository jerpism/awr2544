#include <stdint.h>
#include <stdlib.h>
#include <math.h>

#include <cfg.h>
#define SQUARE_I16(x) (((int32_t)x) * ((int32_t)x))

// N is the number of samples
// as they are complex numbers, each one consists of 2 16 bit signed integers I and Q
void calc_abs_vals(int16_t *dst, int16_t *src, uint32_t n){
    for(int32_t i = 0; i < n; i++){
        dst[i] = (int16_t)sqrt(SQUARE_I16(src[i * 2]) + SQUARE_I16(src[i * 2 + 1]));

    }
}