#include <stdio.h>
#include <stdlib.h>

#include <drivers/edma.h>
#include <drivers/hwa.h>
#include <drivers/uart.h>

#include <kernel/dpl/DebugP.h>
#include <kernel/dpl/SemaphoreP.h>

#include "ti_drivers_config.h"
#include "ti_board_config.h"
#include "ti_drivers_open_close.h"
#include "ti_board_open_close.h"

#include <edma.h>
#include <hwa.h>


static Edma_IntrObject gIntrObj[CONFIG_EDMA_NUM_INSTANCES];


static uint8_t gTestBuff[2048] __attribute__((aligned(CacheP_CACHELINE_ALIGNMENT)));


void edma_write(){
    // Write 1 to EDMA_TPCC_ESR to trigger a transfer
    // TODO: probably replace this with the proper function?
    volatile uint32_t * const addr = (uint32_t*)(EDMA_getBaseAddr(gEdmaHandle[0])+0x1010);
    *addr = 0b1;
}


// TODO: use a struct here for configuring things
// the parameter list might grow even larger so it will be a lot simpler to pass in a `struct edmaCfg`
void edma_configure(EDMA_Handle handle, void *cb, void *dst, void *src, uint16_t acnt, uint16_t bcnt, uint16_t ccnt){
    uint32_t base = 0;
    uint32_t region = 0;
    uint32_t ch = 0;
    uint32_t tcc = 0;
    uint32_t param = 0;
    int32_t ret = 0;
    uint8_t *srcp = (uint8_t*)src;
    uint8_t *dstp = (uint8_t*)dst;

    EDMACCPaRAMEntry edmaparam;

    base = EDMA_getBaseAddr(handle);
    DebugP_assert(base != 0);

    region = EDMA_getRegionId(handle);
    DebugP_assert(region < SOC_EDMA_NUM_REGIONS);

    ch = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocDmaChannel(handle, &ch);
    DebugP_assert(ret == 0);

    tcc = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocTcc(handle, &tcc);
    DebugP_assert(ret == 0);

    param = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocParam(handle, &param);

    // First PaRAM entry, this is to handle ADCBUF -> HWA input
    EDMA_configureChannelRegion(base, region, EDMA_CHANNEL_TYPE_DMA, ch, tcc , param, 0);
    EDMA_ccPaRAMEntry_init(&edmaparam);
    edmaparam.srcAddr       = (uint32_t) SOC_virtToPhy(srcp);
    edmaparam.destAddr      = (uint32_t) SOC_virtToPhy(dstp);
    edmaparam.aCnt          = (uint16_t) acnt;     
    edmaparam.bCnt          = (uint16_t) bcnt;    
    edmaparam.cCnt          = (uint16_t) ccnt;
    edmaparam.bCntReload    = 0U;
    edmaparam.srcBIdx       = 0U;
    edmaparam.destBIdx      = 0U;
    edmaparam.srcCIdx       = 0U;
    edmaparam.destBIdx      = 0U;
    edmaparam.linkAddr      = 0x4000;           // PaRAM set 1 to trigger HWA
    edmaparam.srcBIdxExt    = 0U;
    edmaparam.destBIdxExt   = 0U;
    edmaparam.opt |= (EDMA_OPT_TCINTEN_MASK | EDMA_OPT_ITCINTEN_MASK | ((((uint32_t)tcc)<< EDMA_OPT_TCC_SHIFT)& EDMA_OPT_TCC_MASK));
    EDMA_setPaRAM(base, param, &edmaparam);





    gIntrObj[region].tccNum = tcc;
    gIntrObj[region].cbFxn = cb;
    gIntrObj[region].appData = (void*)0;
    ret = EDMA_registerIntr(handle, &gIntrObj[region]);
    DebugP_assert(ret == 0);
    EDMA_enableEvtIntrRegion(base, region, ch);
    EDMA_enableTransferRegion(base, region, ch, EDMA_TRIG_MODE_EVENT);
    DebugP_log("Edma initialized\r\n");
}

void edma_test(void *arg){
    Drivers_open();
    Board_driversOpen(); 

    hwa_init(gHwaHandle[0], NULL);

    EDMA_Handle handle = gEdmaHandle[0];
    static Edma_IntrObject intrObj;
    srand(1337);
    for(size_t i = 0; i < 2048; ++i){
        gTestBuff[i] = (uint8_t)rand() % 255;
    }
    CacheP_wbInv(gTestBuff, 1024*2, CacheP_TYPE_ALL);

    uint32_t base = 0;
    uint32_t region = 0;
    uint32_t ch0 = 0, ch1 = 0;
    uint32_t tcc0 = 0, tcc1 = 0;
    uint32_t param0 = 0, param1 = 0;
    int32_t ret = 0;
    uint8_t *srcp = (uint8_t*)&gTestBuff;
    uint8_t *dstp = (uint8_t*)0x82000000;

    EDMACCPaRAMEntry edmaparam, edmaparam2;
    uint32_t hwaaddr = (uint32_t)SOC_virtToPhy((void*)hwa_getaddr(gHwaHandle[0]));

    base = EDMA_getBaseAddr(handle);
    DebugP_assert(base != 0);
    DebugP_log("Base %#x\r\n",base);

    region = EDMA_getRegionId(handle);
    DebugP_assert(region < SOC_EDMA_NUM_REGIONS);
    DebugP_log("Region %u\r\n",region);

    ch0 = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocDmaChannel(handle, &ch0);
    DebugP_assert(ret == 0);
    DebugP_log("ch %u\r\n",ch0);

    tcc0 = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocTcc(handle, &tcc0);
    DebugP_assert(ret == 0);
    DebugP_log("tcc %u\r\n", tcc0);

    param0 = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocParam(handle, &param0);
    DebugP_assert(ret == 0);
    DebugP_log("first param %u\r\n",param0);


    ch1 = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocDmaChannel(handle, &ch1);
    DebugP_assert(ret == 0);
    DebugP_log("ch %u\r\n",ch1);

    tcc1 = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocTcc(handle, &tcc1);
    DebugP_assert(ret == 0);
    DebugP_log("tcc %u\r\n", tcc1);

    param1 = EDMA_RESOURCE_ALLOC_ANY;
    ret = EDMA_allocParam(handle, &param1);
    DebugP_assert(ret == 0);
    DebugP_log("second param %u\r\n",param1);

    // First PaRAM entry, this is to handle ADCBUF -> HWA input
    EDMA_configureChannelRegion(base, region, EDMA_CHANNEL_TYPE_DMA, ch0, tcc0, param0, 0);
    EDMA_ccPaRAMEntry_init(&edmaparam);
    edmaparam.srcAddr       = (uint32_t) SOC_virtToPhy(srcp);
    edmaparam.destAddr      = (uint32_t) hwaaddr;
    edmaparam.aCnt          = (uint16_t) 2048;     
    edmaparam.bCnt          = (uint16_t) 1U;    
    edmaparam.cCnt          = (uint16_t) 1U;
    edmaparam.bCntReload    = 0U;
    edmaparam.srcBIdx       = 0U;
    edmaparam.destBIdx      = 0U;
    edmaparam.srcCIdx       = 0U;
    edmaparam.destBIdx      = 0U;
    edmaparam.linkAddr      = 0xFFFFU;           // PaRAM set 1 to trigger HWA
    edmaparam.srcBIdxExt    = 0U;
    edmaparam.destBIdxExt   = 0U;
    edmaparam.opt |= (EDMA_OPT_TCINTEN_MASK | EDMA_OPT_ITCINTEN_MASK | ((((uint32_t)tcc0)<< EDMA_OPT_TCC_SHIFT)& EDMA_OPT_TCC_MASK));
    EDMA_setPaRAM(base, param0, &edmaparam);


 //   EDMA_chainChannel(base, param0, ch1, (EDMA_OPT_TCCHEN_MASK | EDMA_OPT_ITCCHEN_MASK));

    EDMA_enableTransferRegion(base, region, ch0, EDMA_TRIG_MODE_MANUAL);
 //   edma_write();

    
    while(1)__asm__("wfi");
    
}