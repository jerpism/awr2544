#include <stdint.h>
#include <stdlib.h>
#include <math.h>

#include <cfg.h>
#define SQUARE_I16(x) (((int32_t)x) * ((int32_t)x))

// N is the number of samples
// as they are complex numbers, each one consists of 2 16 bit signed integers I and Q
void calc_abs_vals(int16_t *in, int16_t *out, uint32_t n){
    for(int32_t i = 0; i < n; i++){
        out[i] = (int16_t)sqrt(SQUARE_I16(in[i * 2]) + SQUARE_I16(in[i * 2 + 1]));

    }
}


void arrange_matrix(uint32_t *in, size_t n, size_t m, uint32_t *out){
    // Assume we're using 16 bit complex data
    // so we can just move 4 bytes at once to copy an entire sample
    // Number of elements per one rx in a chirp if we're using them as 4 byte values
    size_t rx_elements = CHIRP_DATASIZE / NUM_RX_ANTENNAS /  sizeof(uint32_t);
    // How many we have in a chirp
    size_t chirp_elements = CHIRP_DATASIZE / sizeof(uint32_t);

    // Arrange chirps for one receiver into a [n][m] matrix
    for(size_t i = 0; i < CHIRPS_PER_FRAME; ++i){
        for(size_t j = 0; j < rx_elements; ++j){
            out[i * rx_elements + j] = in[i * chirp_elements + j];
        }
    }

}
