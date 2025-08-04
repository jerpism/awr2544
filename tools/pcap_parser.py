import dpkt
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fname", help="name of .pcap file to parse")
args = parser.parse_args()

filename=args.fname
range_res = 0.39

counter=0
udpcounter=0
chirpcounter=0
pktbuf=0

rx1_comp = np.zeros(128, dtype=np.complex128)
rx2_comp = np.zeros(128, dtype=np.complex128)
rx3_comp = np.zeros(128, dtype=np.complex128)
rx4_comp = np.zeros(128, dtype=np.complex128)

#compute x axis range values
ranges = np.arange(rx1_comp.shape[0]) * range_res

plt.ion()
fig, axs = plt.subplots(2,2)
lines = []
fig.suptitle("Each rx for chrip: ")
for ax in axs.flat:
    ax.set(xlabel='range', ylabel='signal component amp')
    ax.label_outer()
    line, = ax.plot(np.zeros(128))
    lines.append(line)


def getChripData(buf,rx1,rx2):
    for i in range(len(rx1)):
        idx = 4*i
        rx1[i] = int.from_bytes(buf[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(buf[idx+2:idx+4],"little",signed=True))
        idx = 512 + 4*i
        rx2[i] = int.from_bytes(buf[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(buf[idx+2:idx+4],"little",signed=True))
    return


for ts, pkt in dpkt.pcap.Reader(open(filename,'rb')):

    counter+=1
    eth=dpkt.ethernet.Ethernet(pkt) 
    if eth.type!=dpkt.ethernet.ETH_TYPE_IP:
       continue

    ip=eth.data

    if ip.p==dpkt.ip.IP_PROTO_UDP:
        #drop first packet
        if (udpcounter>=1):
            pktbuf = ip.data.data
            if (udpcounter%2 == 1):
                getChripData(pktbuf,rx1_comp,rx2_comp)
            if (udpcounter%2 == 0):
                getChripData(pktbuf,rx3_comp,rx4_comp)
                chirpcounter+=1
                #when data from each rx is done, plot new data
                string = "Each rx for chirp: " + str(chirpcounter)
                fig.suptitle(string)
                for i in range(4):
                    cmplx_sets = [rx1_comp,rx2_comp,rx3_comp,rx4_comp]
                    lines[i].set_ydata(np.abs(cmplx_sets[i]))
                    lines[i].set_xdata(ranges)
                for ax in axs.flat:
                    ax.relim()
                    ax.autoscale_view()
                fig.canvas.draw()
                fig.canvas.flush_events()

        udpcounter+=1

'''
print("all pkts counter: ", counter," udpcounter: ", udpcounter)
print("pktbuf, size:", len(pktbuf)," type:",type(pktbuf)," type of element:",type(pktbuf[0:1]))
print("rx1_comp, size:", len(rx1_comp)," type:",type(rx1_comp)," type of element:",type(rx1_comp[0]))
'''