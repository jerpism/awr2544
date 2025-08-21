import dpkt
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fname", help="name of .pcap file to parse")
args = parser.parse_args()

filename=args.fname
range_res = 0.39

udpcounter=0
chirpcounter=0
pktbuf = []

rx1_cmplx = np.zeros(128, dtype=np.complex128)
rx2_cmplx = np.zeros(128, dtype=np.complex128)
rx3_cmplx = np.zeros(128, dtype=np.complex128)
rx4_cmplx = np.zeros(128, dtype=np.complex128)

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


#compute x axis range values
ranges = np.arange(rx1_cmplx.shape[0]) * range_res

plt.ion()
fig, axs = plt.subplots(2,2)
lines = []
for ax in axs.flat:
    ax.set(xlabel='range', ylabel='signal component amp')
    ax.label_outer()
    line, = ax.plot(np.zeros(128))
    lines.append(line)

for ts, pkt in dpkt.pcapng.Reader(open(filename,'rb')):

    eth=dpkt.ethernet.Ethernet(pkt) 
    if eth.type!=dpkt.ethernet.ETH_TYPE_IP:
       continue

    ip=eth.data

    if ip.p==dpkt.ip.IP_PROTO_UDP:
        header = b"\x01\x02\x03\x04"
        footer = b"\x04\x03\x02\x01"
        payload = ip.data.data
        if (payload != header and payload != footer and payload != 0):
            pktbuf.append(ip.data.data)
            chirpcounter += 1
            if chirpcounter == 256:
                #after receiving whole frame, plot data.
                #print(f"pktbuf len: {len(pktbuf)}, pktbuf type: {type(pktbuf)}, pktbuf[0] type: {type(pktbuf[0])}")
                string = f"Each rx for pkt: {udpcounter}"
                fig.suptitle(string)

                #Currently getChirpData fetches only last chirp for debugging purposes
                getChirpData(pktbuf,rx1_cmplx,rx2_cmplx,rx3_cmplx,rx4_cmplx)

                for i in range(4):
                    cmplx_sets = [rx1_cmplx,rx2_cmplx,rx3_cmplx,rx4_cmplx]
                    lines[i].set_ydata(np.abs(cmplx_sets[i]))
                    lines[i].set_xdata(ranges)
                for ax in axs.flat:
                    ax.relim()
                    ax.autoscale_view()
                fig.canvas.draw()
                fig.canvas.flush_events()

                pktbuf = []
                chirpcounter = 0
            

        udpcounter+=1