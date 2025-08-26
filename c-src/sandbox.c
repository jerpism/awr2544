/*  This file should be used to test things separately from the full project.
    Simply #include <sandbox.h> and start sandbox_main as the task  */
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <drivers/hwa.h>
#include "drivers/edma/v0/edma.h"
#include "drivers/hwa/v1/hwa.h"
#include "ti_drivers_config.h"
#include <cfg.h>
#include "FreeRTOS.h"
#include "task.h"
#include <drivers/edma.h>
#include <drivers/hwa.h>
#include <drivers/uart.h>

#include <kernel/dpl/DebugP.h>
#include <kernel/dpl/SemaphoreP.h>

#include "ti_drivers_config.h"
#include "ti_board_config.h"
#include "ti_drivers_open_close.h"
#include "ti_board_open_close.h"

void reflect_pad(int16_t *input, size_t n, int radius, int16_t *padded){
    DebugP_assert(radius < n);
    // Pad the beginning of the array
    // e.g. in={1,2,3,4} radius=2 -> padded={3,2}
    for(int i = 0; i < radius; ++i){
        padded[i] = input[radius - i];
    }

    // Fill in the already existing values
    // same as before -> padded={3,2,1,2,3,4}
    for(int i = 0; i < n; ++i){
        padded[radius + i] = input[i];
    }

    // And then pad the end of the array
    // same as before -> padded={3,2,1,2,3,4,3,2}
    for(int i = 0; i < radius; ++i){
        padded[radius + n + i] = input[n - 2 - i];
    }

}

void convolve_1d(int16_t *a, int n, int16_t *b, int m, int16_t *out){
    int radius = m / 2;
    int padded_len = 2 * radius + n;
    int16_t *padded;
    padded = malloc(padded_len * sizeof(int16_t));
    reflect_pad(a, n, radius, padded);
    
    for(int i = 0; i < n; ++i){
        // Maybe just calloc or memset? probably faster
        out[i] = 0;
        for(int j = 0; j < m; ++j){
            out[i] += padded[i+j] * b[j];
        }
    }

    free(padded);
}

void sandbox_main(void *args){
    int win_sz = 2;
    float ma[40];
    float win[win_sz];
    memset(win, 1.0f / win_sz, win_sz * sizeof(float));

    for(int i = 0; i < win_sz; ++i) printf("%lf\r\n", win[i]);

    while(1) __asm__("wfi");
}