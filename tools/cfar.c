#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define N 400
#define PI 3.14159265358979323846

// Generate random float in [0, 1)
float randf() {
    return (float)rand() / (float)(RAND_MAX);
}

// Generate standard normal using Box-Muller
float randn() {
    float u1 = randf();
    float u2 = randf();
    return sqrt(-2.0 * log(u1)) * cos(2.0 * PI * u2);
}

// Fill array with Gaussian noise
void fill_normal(float* arr, int len, float mean, float std) {
    for (int i = 0; i < len; ++i) {
        arr[i] = randn() * std + mean;
    }
}

// Reflect padding
void reflect_pad(const float* input, float* padded, int n, int pad) {
    for (int i = 0; i < pad; ++i)
        padded[i] = input[pad - i];
    for (int i = 0; i < n; ++i)
        padded[pad + i] = input[i];
    for (int i = 0; i < pad; ++i)
        padded[pad + n + i] = input[n - 2 - i];
}

// 1D Convolution (correlation) with reflect mode
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

// Generate unique random indices
void random_indices(int* out, int count, int max) {
    int chosen[max];
    for (int i = 0; i < max; ++i) chosen[i] = 0;

    int picked = 0;
    while (picked < count) {
        int r = rand() % max;
        if (!chosen[r]) {
            chosen[r] = 1;
            out[picked++] = r;
        }
    }
}

// Clip values to range [0, N-1]
int clamp(int val) {
    if (val < 0) return 0;
    if (val >= N) return N - 1;
    return val;
}

int main() {
    srand(time(NULL));

    float x[N] = {0}, n2[N], x2[N], ma[N], noise_level[N], threshold[N];
    int sources[10];
    int detected[N] = {0}, detected_2[N] = {0}, detected_3[N] = {0}, detected_4[N] = {0};

    // Step 1: Generate noise
    fill_normal(x, N, 0, 1);

    // Step 2: Add sources
    random_indices(sources, 10, N);
    for (int i = 0; i < 10; ++i) {
        int idx = sources[i];
        x[clamp(idx)] += 5;
        x[clamp(idx-1)] += 3;
        x[clamp(idx+1)] += 3;
        x[clamp(idx-2)] += 2;
        x[clamp(idx+2)] += 2;
        x[clamp(idx-3)] += 1;
        x[clamp(idx+3)] += 1;
    }

    // Step 3: Normalize x
    float min_x = x[0];
    for (int i = 1; i < N; ++i)
        if (x[i] < min_x) min_x = x[i];
    for (int i = 0; i < N; ++i)
        x[i] -= min_x;

    // Step 4: Add sine wave + noise to x
    for (int i = 0; i < N; ++i) {
        n2[i] = randn() + 2 * sin(i / 50.0);
        x2[i] = x[i] + n2[i];
    }

    // Step 5: Detection threshold
    float thresh = 6.0;
    for (int i = 0; i < N; ++i) {
        if (x2[i] > thresh) detected_2[i] = 1;
    }

    // Step 6: Moving average
    int win_sz = 25;
    float win[win_sz];
    for (int i = 0; i < win_sz; ++i) win[i] = 1.0 / win_sz;
    convolve_1d(x2, N, win, win_sz, ma);

    for (int i = 0; i < N; ++i) {
        float threshold_ma = 3 + ma[i];
        if (x2[i] > threshold_ma)
            detected_3[i] = 1;
    }

    // Step 7: CFAR detection
    int guard_len = 0;
    int train_len = 10;
    int k_len = 1 + 2*guard_len + 2*train_len;
    float cfar_kernel[k_len];
    for (int i = 0; i < k_len; ++i)
        cfar_kernel[i] = 1.0 / (2 * train_len);
    for (int i = train_len; i < train_len + 2*guard_len + 1; ++i)
        cfar_kernel[i] = 0;

    float p_fa = 0.1;
    float a = train_len * (pow(p_fa, -1.0 / train_len) - 1.0);
    printf("Threshold scale factor: %f\n", a);

    convolve_1d(x2, N, cfar_kernel, k_len, noise_level);
    for (int i = 0; i < N; ++i) {
        threshold[i] = (noise_level[i] + 1) * (a - 1);
        if (x2[i] > threshold[i])
            detected_4[i] = 1;
    }

    // Step 8: Write output to file
    FILE* f = fopen("output.csv", "w");
    fprintf(f, "x2,noise_level,threshold,detected,sources\n");
    for (int i = 0; i < N; ++i) {
        int is_source = 0;
        for (int j = 0; j < 10; ++j)
            if (sources[j] == i) is_source = 1;
        fprintf(f, "%f,%f,%f,%d,%d\n", x2[i], noise_level[i], threshold[i], detected_4[i], is_source);
    }
    fclose(f);

    printf("Done. Output written to output.csv\n");
    return 0;
}
