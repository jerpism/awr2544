import dpkt
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fname", help="name of .pcap file to parse")
parser.add_argument("frame_num", help="index of frame to evaluate with Doppler FFT")
parser.add_argument("rangebin",help="index of range bin to evaluate with Doppler FFT")
args = parser.parse_args()

filename=args.fname

range_res = 1 #0.39
eval_frame_num = int(args.frame_num)
eval_rangebin_num = int(args.rangebin)

header = b"\x01\x02\x03\x04"
footer = b"\x04\x03\x02\x01"

chirpcounter=0
framecounter=0
pktbuf = []

#cfar variables
guard_len = 1
train_len = 12
p_fa = 0.1 # Probability of False Alarm

rx1_cmplx = np.zeros(128, dtype=np.complex128)
rx2_cmplx = np.zeros(128, dtype=np.complex128)
rx3_cmplx = np.zeros(128, dtype=np.complex128)
rx4_cmplx = np.zeros(128, dtype=np.complex128)

#create kernel
cfar_kernel = np.ones((1 + 2*guard_len + 2*train_len), dtype=float) / (2*train_len)
cfar_kernel[train_len: train_len + (2*guard_len) + 1] = 0.

thresh_scale = train_len*(p_fa**(-1/train_len) - 1)
print(f"Threshold scale factor: {thresh_scale}")

#compute x axis range values
ranges = np.arange(rx1_cmplx.shape[0]) * range_res

#plotting stuff
plt.ion()
fig, axs = plt.subplots(2,2)
lines = []
scatters = [None] * 4 



for ax in axs.flat:
    ax.set(xlabel='range', ylabel='signal component amp')
    ax.label_outer()
    line1, = ax.plot(np.zeros(128))
    line2, = ax.plot(np.zeros(128))
    lines.append([line1,line2])

def unpackPktBuf(buf):
    rx12_b = buf[::2] #rx12_b len: 128, type: <class 'list'>, [0] type: <class 'bytes'>
    rx34_b = buf[1::2]

    #print(f"rx12_b len: {len(rx12_b)}, type: {type(rx12_b)}, [0] type: {type(rx12_b[0])}")

    rx1_b = []
    rx2_b = []
    rx3_b = []
    rx4_b = []

    #hard coded values warning :(
    for i in range(128):
        rx1_b.append(rx12_b[i][:512])
        rx2_b.append(rx12_b[i][512:])
        rx3_b.append(rx34_b[i][:512])
        rx4_b.append(rx34_b[i][512:])
  
    ret = np.zeros((4,128,128),dtype=np.complex128)

    for i in range(128):
        for k in range(128):
            idx = 4*k
            ret[0][i][k] = int.from_bytes(rx1_b[i][idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx1_b[i][idx+2:idx+4],"little",signed=True))
            ret[1][i][k] = int.from_bytes(rx2_b[i][idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx2_b[i][idx+2:idx+4],"little",signed=True))
            ret[2][i][k] = int.from_bytes(rx3_b[i][idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx3_b[i][idx+2:idx+4],"little",signed=True))
            ret[3][i][k] = int.from_bytes(rx4_b[i][idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx4_b[i][idx+2:idx+4],"little",signed=True))

    return ret

def getChirpData(buf,rx1,rx2,rx3,rx4):
    rx1_b = buf[-2][:512]
    rx2_b = buf[-2][512:]
    rx3_b = buf[-1][:512]
    rx4_b = buf[-1][512:]

    for i in range(len(rx1)):
        idx = 4*i
        rx1[i] = int.from_bytes(rx1_b[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx1_b[idx+2:idx+4],"little",signed=True))
        rx2[i] = int.from_bytes(rx2_b[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx2_b[idx+2:idx+4],"little",signed=True))
        rx3[i] = int.from_bytes(rx3_b[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx3_b[idx+2:idx+4],"little",signed=True))
        rx4[i] = int.from_bytes(rx4_b[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx4_b[idx+2:idx+4],"little",signed=True))

    return



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



def doppler_fft(buf, range_bin):
    #not very elegant but hey
    rx_buf = buf[::2][:512]
    res = np.zeros((len(rx_buf),len(rx_buf)),dtype=np.complex128)

    for i in range(len(res)):
        for k in range(len(res[0])):
            idx = 4*k
            res[i][k] = int.from_bytes(rx_buf[i][idx:idx+2],"little",signed=True) + (1j*int.from_bytes(rx_buf[i][idx+2:idx+4],"little",signed=True))

    '''
    with open("framedata.csv","w",newline="\n") as csvfile:
        string_to_write = ""
        print(np.shape(res))
        for i in range(len(res)):
            for k in range(len(res[0])):
                real = str(int(np.real(res[i][k])))
                imag = str(int(np.imag(res[i][k])))

                if (i == (len(res)-1) and k == (len(res[0])-1)):
                    print("last write loop")
                    string_to_write += f"{real},{imag}"
                else:
                    string_to_write += f"{real},{imag},"
                    
        csvfile.write(string_to_write)
    '''

    #doppler fft
    doppler_data = np.zeros(len(rx_buf), dtype=np.complex128)
    for i in range(len(doppler_data)):
        doppler_data[i] = res[i][range_bin]
    doppler_res = np.fft.fftshift(np.fft.fft(doppler_data))#np.fft.fft(doppler_data)

    return doppler_res



def calc_angle(z1,z2):
    phase_d = np.angle(z1) - np.angle(z2)
    angle = np.arcsin(phase_d/(2*np.pi)) #the actual formula is asin( (wavelength*phase_diff) / (2*pi*antenna_distance) ), however, antenna_distance equals wavelength when comparing adjacent rx (rx2,rx3 or rx1,rx4)
    return angle

#def aoa_calc(frame):


for ts, pkt in dpkt.pcapng.Reader(open(filename,'rb')):

    eth=dpkt.ethernet.Ethernet(pkt) 
    if eth.type!=dpkt.ethernet.ETH_TYPE_IP:
       continue

    ip=eth.data

    if ip.p==dpkt.ip.IP_PROTO_UDP:
        payload = ip.data.data
        if (payload != header and payload != footer and payload != 0):
            pktbuf.append(payload)
            chirpcounter += 1
            if chirpcounter == 256:
                framecounter += 1
                #after receiving whole frame, plot data.
                #print(f"pktbuf len: {len(pktbuf)}, pktbuf type: {type(pktbuf)}, pktbuf[0] type: {type(pktbuf[0])}")
                framecnt_string = f"Each rx for frame: {framecounter}"
                fig.suptitle(framecnt_string)

                frame = unpackPktBuf(pktbuf)

                #Currently getChirpData fetches only last chirp for debugging purposes
                getChirpData(pktbuf,rx1_cmplx,rx2_cmplx,rx3_cmplx,rx4_cmplx)

                noise_level = []
                threshold = []
                detected = []
                cmplx_sets = [rx1_cmplx,rx2_cmplx,rx3_cmplx,rx4_cmplx]

                for i, line_pair in enumerate(lines):

                    noise_level.append(convolve_1d(np.abs(cmplx_sets[i]),cfar_kernel))
                    threshold.append((noise_level[i] + 1) * (thresh_scale-1))
                    detected.append(np.abs(cmplx_sets[i]) > threshold[i])

                    if scatters[i] is not None:
                        scatters[i].remove()  # remove previous scatter

                    x_points = np.array(ranges)[detected[i]]
                    y_points = np.abs(np.array(cmplx_sets[i]))[detected[i]]
                    scatters[i] = axs.flat[i].scatter(x_points, y_points, color='m', s=10)

                    line_pair[0].set_ydata(np.abs(cmplx_sets[i]))
                    line_pair[0].set_xdata(ranges)
                    line_pair[1].set_ydata(threshold[i])
                    line_pair[1].set_xdata(ranges)

                    

                if framecounter == eval_frame_num:

                    print(x_points)
                    doppler = doppler_fft(pktbuf,eval_rangebin_num)
                    angle = calc_angle(rx1_cmplx[eval_rangebin_num],rx4_cmplx[eval_rangebin_num])
                    print(f"Angle: {angle*(180/np.pi)} degrees")

                    N = 128  # number of chirps
                    T_chirp = 35e-6  # 34,8 usec actual val
                    f_c = 77e9  # 77 GHz
                    fd_axis = np.fft.fftshift(np.fft.fftfreq(N, d=T_chirp))  # Doppler frequency axis
                    wavelength = 3e8 / f_c
                    velocity_axis = (fd_axis * wavelength) / 2  # in m/s

                    plt.figure()
                    plt.plot(velocity_axis,np.abs(doppler))
                    #plt.plot(np.abs(doppler))
                    plt.xlabel("Velocity (m/s)")
                    plt.ylabel("Magnitude")
                    plt.title("Doppler Spectrum")
                    plt.grid(True)
                    plt.show()
                    input("Press enter to continue plotting\n") #this pauses plotting so Doppler spectrum can be examined
                    
                for ax in axs.flat:
                    ax.relim()
                    ax.autoscale_view()
                fig.canvas.draw()
                fig.canvas.flush_events()

                pktbuf = []
                chirpcounter = 0