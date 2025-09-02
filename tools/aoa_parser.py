import dpkt
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fname", help="name of .pcap file to parse")
parser.add_argument("frame_num", help="index of frame to evaluate with Doppler FFT")
parser.add_argument("rangebin",help="index of range bin to evaluate with Doppler FFT")
parser.add_argument("velocitybin",help="index of velocity bin to evaluate for AoA FFT")
args = parser.parse_args()

filename=args.fname
eval_frame_num = int(args.frame_num)
eval_range_bin_num = int(args.rangebin)
eval_vel_bin_num = int(args.velocitybin)

header = b"\x01\x02\x03\x04"
footer = b"\x04\x03\x02\x01"

chirpcounter=0
framecounter=0
pktbuf = []

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



def doppler_fft(frame,rangebin):

    doppler_data = np.zeros((4,len(frame[0])),dtype=np.complex128)
    for i in range(len(doppler_data[0])):
        doppler_data[0][i] = frame[0][i][rangebin]
        doppler_data[1][i] = frame[1][i][rangebin]
        doppler_data[2][i] = frame[2][i][rangebin]
        doppler_data[3][i] = frame[3][i][rangebin]

    doppler_res = np.zeros((4,len(frame[0])),dtype=np.complex128)
    for i in range(len(doppler_res)):
        doppler_res[i] = np.fft.fftshift(np.fft.fft(doppler_data[i]))

    return doppler_res


def aoa_fft(frame,vel_bin):
    doppler = doppler_fft(frame,eval_range_bin_num)
    aoa_data = np.zeros((len(doppler)),dtype=np.complex128)

    for i in range(len(doppler)):
        aoa_data[i] = doppler[i][vel_bin]
    
    aoa_res = np.fft.fft(aoa_data)
    print(aoa_res)
    return aoa_res



def music_single_snapshot(x, antenna_positions, wavelength, scan_angles_deg):
    M = len(x)  # Number of antennas
    theta_scan = np.deg2rad(scan_angles_deg)

    # Covariance matrix from single snapshot
    R = np.outer(x, x.conj())  # x * x^H

    # Eigendecomposition
    eigvals, eigvecs = np.linalg.eigh(R)
    idx = np.argsort(eigvals)[::-1]  # descending order
    eigvecs = eigvecs[:, idx]
    eigvals = eigvals[idx]

    # Assume 1 signal source, so the rest is noise
    En = eigvecs[:, 1:]  # Noise subspace (all except largest eigenvalue)

    # MUSIC spectrum
    P_music = []

    for theta in theta_scan:
        # Steering vector for angle theta
        a_theta = np.exp(-1j * 2 * np.pi / wavelength * antenna_positions * np.sin(theta))
        a_theta = a_theta[:, np.newaxis]

        # MUSIC pseudo-spectrum
        denom = np.conj(a_theta.T) @ En @ En.conj().T @ a_theta
        spectrum = 1 / np.abs(denom)[0, 0]
        P_music.append(spectrum)

    # Normalize and convert to dB
    P_music = np.abs(P_music)
    P_music_dB = 10 * np.log10(P_music / np.max(P_music))

    return scan_angles_deg, P_music_dB



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
                frame = unpackPktBuf(pktbuf)

                #print(f"pktbuf len: {len(pktbuf)}, pktbuf type: {type(pktbuf)}, pktbuf[0] type: {type(pktbuf[0])}")
                #print(f"frame shape: {np.shape(frame)}, cell type: {type(frame[0][0][0])}, val: {frame[0][0][10]}")           

                if framecounter == eval_frame_num:

                    dopp_spec = doppler_fft(frame,eval_range_bin_num)
                    aoa_spec = aoa_fft(frame,eval_vel_bin_num)

                    # Constants
                    wavelength = 3e8 / 77e9  # ~0.003896 m

                    # Antenna positions (in order: rx4, rx1, rx2, rx3)
                    antenna_positions = np.array([0, 1, 3.5, 4.5]) * wavelength  # meters

                    # Example snapshot from rx4, rx1, rx2, rx3 (same order as positions)
                    x = aoa_spec

                    # Angle scan range
                    angles_deg = np.linspace(-90, 90, 361)

                    # Run MUSIC
                    angles, spectrum_dB = music_single_snapshot(x, antenna_positions, wavelength, angles_deg)

                    plt.figure(figsize=(10, 5))
                    plt.plot(angles, spectrum_dB)
                    plt.title("MUSIC Spectrum")
                    plt.xlabel("Angle (degrees)")
                    plt.ylabel("Spectrum (dB)")
                    plt.grid(True)
                    plt.show()

                pktbuf = []
                chirpcounter = 0