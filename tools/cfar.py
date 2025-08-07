import numpy as np
import matplotlib.pyplot as plt

def convolve_1d(a, b, mode='reflect'):
    
    a = np.asarray(a)
    b = np.asarray(b)
    radius = len(b) // 2 
    out = np.zeros_like(a, dtype=float)
    
    # Pad array based on mode
    # np.pad() expands the given array by (n,k) elements. n dictates how many elements are put in the beginning
    # while k is the same for the end of the given array.
    # more on padding modes at the end of: https://numpy.org/devdocs/reference/generated/numpy.pad.html
    if mode == 'reflect':
        #the default basically mirrors the data in the array across the end of the array. e.g.:
        #>>> a = [1, 2, 3, 4, 5]
        #>>> np.pad(a, (2, 3), 'reflect')
        #array([3, 2, 1, 2, 3, 4, 5, 4, 3, 2])
        a_padded = np.pad(a, (radius, radius), mode='reflect') 
    elif mode == 'constant':
        a_padded = np.pad(a, (radius, radius), mode='constant', constant_values=0)
    elif mode == 'nearest':
        a_padded = np.pad(a, (radius, radius), mode='edge')
    elif mode == 'wrap':
        a_padded = np.pad(a, (radius, radius), mode='wrap')
    else:
        raise ValueError(f"Unsupported mode: {mode}")
    
    # Correlation (NOT flipping the kernel)
    for i in range(len(a)):
        for j in range(len(b)):
            out[i] += a_padded[i + j] * b[j]
    
    return out

# get noisy signal
x = np.zeros((400))
x +=  np.random.normal(0, 1, 400)

# add sources to the noise
sources = np.random.choice(np.arange(0, 400), 10, replace=False)
x[sources] += 5

# spread the sources to simulate range spread
x[sources - 1] += 3
x[sources + 1] += 3
x[sources - 2] += 2
x[sources + 2] += 2
x[sources - 3] += 1
x[sources + 3] += 1

x -= x.min()

thresh = 6
detected = x > thresh

# generate sine wave to impose on the generated noise
n2 = np.random.normal(0, 1, 400) + 2*np.sin(np.arange(0, 400)/50)
x2 = x + n2

detected_2 = x2 > thresh

# get moving average
win_sz = 25
win = np.ones(win_sz)/win_sz
ma = convolve_1d(x2, win)

# get new threshold from moving average
threshold_ma = 3 + ma

# get new detections
detected_3 = x2 > threshold_ma

guard_len = 0
train_len = 10

cfar_kernel = np.ones((1 + 2*guard_len + 2*train_len), dtype=float) / (2*train_len)
cfar_kernel[train_len: train_len + (2*guard_len) + 1] = 0.

p_fa = 0.1 # Probability of False Alarm

a = train_len*(p_fa**(-1/train_len) - 1)
print(f"Threshold scale factor: {a}")

noise_level = convolve_1d(x2, cfar_kernel)
threshold = (noise_level + 1) * (a - 1)

# get new detections
detected_4 = x2 > threshold

plt.figure(figsize=(15,5))
'''
plt.plot(x)
plt.plot([0, 400], [thresh, thresh])
plt.scatter(np.where(detected == 1), x[detected], c='m')
plt.scatter(sources, x[sources], c='g')
plt.title("Signals Detected in White Gaussian Noise")

plt.plot(x2)
plt.plot([0, 400], [thresh, thresh])
plt.scatter(np.where(detected_2 == 1), x2[detected_2], c='m')
plt.scatter(sources, x2[sources], c='g')
plt.title("Signals Detected in Non-Stationary Gaussian Noise")

plt.plot(x2)
plt.plot(ma)
plt.plot(threshold_ma)
plt.scatter(np.where(detected_3 == 1), x2[detected_3], c='m')
plt.scatter(sources, x2[sources], c='g')
plt.title("Signals Detected in Non-Stationary Gaussian Noise")
'''
plt.plot(x2)
plt.plot(noise_level)
plt.plot(threshold)
plt.scatter(np.where(detected_4 == 1), x2[detected_4], c='m')
plt.scatter(sources, x2[sources], c='g')

plt.show()