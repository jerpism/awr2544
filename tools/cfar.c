#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 50 // Length of data
#define PI 3.14159265358979323846

//Testing data
float signal[N] = {0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
// Scale factor for detection threshold
float p_fa = 0.3; 


void reflect_pad(const float* input, float* padded, int n, int pad) {
    for (int i = 0; i < pad; ++i)
        padded[i] = input[pad - i];
    for (int i = 0; i < n; ++i)
        padded[pad + i] = input[i];
    for (int i = 0; i < pad; ++i)
        padded[pad + n + i] = input[n - 2 - i];
}


void convolve_1d(const float* a, int n, const float* b, int m, float* output) {
    int radius = m / 2;
    int padded_len = n + 2 * radius;
    float* a_padded = (float*)malloc(sizeof(float) * padded_len);
    
    reflect_pad(a, a_padded, n, radius);

    for (int i = 0; i < n; ++i) {
        output[i] = 0;
        for (int j = 0; j < m; ++j) {
            output[i] += a_padded[i + j] * b[j];
        }
    }

    free(a_padded);
}


int cfar_main() {
    float noise_level[N] = {0},  threshold[N];
    int detected[N] = {0};

    int guard_len = 0;
    int train_len = 10;
    int k_len = 1 + 2*guard_len + 2*train_len;
    float cfar_kernel[k_len];

    for (int i = 0; i < k_len; ++i)
        cfar_kernel[i] = 1.0 / (2 * train_len);
    for (int i = train_len; i < train_len + 2*guard_len + 1; ++i)
        cfar_kernel[i] = 0;

    float a = train_len * (pow(p_fa, -1.0 / train_len) - 1.0);
    printf("Threshold scale factor: %f\n", a);

    convolve_1d(signal, N, cfar_kernel, k_len, noise_level);
    for (int i = 0; i < N; ++i) {
        threshold[i] = (noise_level[i] + 1) * (a - 1);
        if (signal[i] > threshold[i])
            printf("Detected at %d\r\n",i);
            detected[i] = 1;
    }

    printf("Done.\n");
    return 0;
}