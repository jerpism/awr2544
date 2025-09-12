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
eval_frame_num = int(args.frame_num)
eval_range_bin_num = int(args.rangebin)

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



def frame_to_mimo(frame):
    mimo_arr = np.zeros((8,128),dtype=np.complex128)

    for i in range(len(frame)):
        rx_pairs = []

        for j in range(len(frame[i])//2):
            idx = j*2
            rx_pairs.append([frame[i][idx],frame[i][idx+1]])
        
        for j in range(len(rx_pairs)):
            sum_rx = rx_pairs[j][0] + rx_pairs[j][1]
            sub_rx = rx_pairs[j][0] - rx_pairs[j][1]
        
        mimo_arr[i] = sum_rx
        mimo_arr[i+4] = sub_rx

    return mimo_arr



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
                    mimo = frame_to_mimo(frame)

                    aoa_vec = []
                    for i in range(len(mimo)):
                        aoa_vec.append(mimo[i][eval_range_bin_num])

                    plt.figure()
                    plt.plot(np.abs(np.fft.fft(aoa_vec)))
                    plt.show()

                pktbuf = []
                chirpcounter = 0