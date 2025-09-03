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

void sandbox_main(void *args){
    int win_sz = 2;
    float ma[40];
    float win[win_sz];
    memset(win, 1.0f / win_sz, win_sz * sizeof(float));

    for(int i = 0; i < win_sz; ++i) printf("%lf\r\n", win[i]);

    while(1) __asm__("wfi");
}