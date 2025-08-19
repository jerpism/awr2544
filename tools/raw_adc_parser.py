import dpkt
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fname", help="name of .pcap file to parse")
args = parser.parse_args()

filename=args.fname

header = b"\x01\x02\x03\x04"
footer = b"\x04\x03\x02\x01"
pktbuf = []

pktcounter = 0
udpcounter = 0

range_res = 0.39

#compute x axis range values
ranges = np.arange(128) * range_res

#plotting stuff
plt.ion()
fig, axs = plt.subplots(2,2)
lines = []

for ax in axs.flat:
    ax.set(xlabel='range', ylabel='signal component amp')
    ax.label_outer()
    line1, = ax.plot(np.zeros(128))
    lines.append(line1)

def pkts_parse(buf, sig):
    rx1_b = buf[-2][:512]
    rx2_b = buf[-2][512:]
    rx3_b = buf[-1][:512]
    rx4_b = buf[-1][512:]

    for i in range(len(buf)):
        idx = i * 2
        sig[0].append(int.from_bytes(rx1_b[idx:idx+2],"little",signed=False))
        sig[1].append(int.from_bytes(rx2_b[idx:idx+2],"little",signed=False))
        sig[2].append(int.from_bytes(rx3_b[idx:idx+2],"little",signed=False))
        sig[3].append(int.from_bytes(rx4_b[idx:idx+2],"little",signed=False))
        

for ts, pkt in dpkt.pcapng.Reader(open(filename,'rb')):

    eth=dpkt.ethernet.Ethernet(pkt) 
    if eth.type!=dpkt.ethernet.ETH_TYPE_IP:
       continue

    ip=eth.data

    if ip.p==dpkt.ip.IP_PROTO_UDP:
        udpcounter += 1
        payload = ip.data.data
        if (payload != header and payload != footer and payload != 0):
            pktbuf.append(payload)
            pktcounter += 1
            if pktcounter == 256:

                signals = [[],[],[],[]]
                pkts_parse(pktbuf,signals)
                
                string = f"Each rx for pkt: {udpcounter}"
                fig.suptitle(string)

                for i in range(4):
                    fft_res = np.abs(np.fft.rfft(signals[i]))
                    fft_res = fft_res[:-1]
                    lines[i].set_ydata(fft_res)
                    lines[i].set_xdata(ranges)
                for ax in axs.flat:
                    ax.relim()
                    ax.autoscale_view()
                fig.canvas.draw()
                fig.canvas.flush_events()

                pktbuf = []
                pktcounter = 0
