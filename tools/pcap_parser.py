#file to be parsed is named frame.pcapng

import dpkt
import numpy as np
import matplotlib.pyplot as plt
import copy

counter=0
ipcounter=0
udpcounter=0

filename='frame.pcap'

pktbuf=0

for ts, pkt in dpkt.pcap.Reader(open(filename,'rb')):

    counter+=1
    eth=dpkt.ethernet.Ethernet(pkt) 
    if eth.type!=dpkt.ethernet.ETH_TYPE_IP:
       continue

    ip=eth.data
    ipcounter+=1

    if ip.p==dpkt.ip.IP_PROTO_UDP:
        udpcounter+=1
        if udpcounter==2:
            pktbuf = ip.data.data

#get one chirp data:
print(type(pktbuf),type(pktbuf[0]),len(pktbuf))
testvar = int.from_bytes(pktbuf[:1])
print(pktbuf[:1],print(type(pktbuf[:1])),testvar)

rx1_comp = np.zeros(128,dtype=np.complex128)
real_arr = np.zeros(128)
img_arr = np.zeros(128)

for i in range(len(rx1_comp)):
    idx = 4*i
    rx1_comp[i] = int.from_bytes(pktbuf[idx:idx+2],"little",signed=True) + (1j*int.from_bytes(pktbuf[idx+2:idx+4],"little",signed=True))
    real_arr[i] = int.from_bytes(pktbuf[idx:idx+2],"little",signed=True)
    img_arr[i] = int.from_bytes(pktbuf[idx+2:idx+4],"little",signed=True)

print(real_arr)
print(img_arr)
print(rx1_comp[0])
print(type(rx1_comp),type(rx1_comp[0]))

plt.figure()
plt.plot(np.abs(rx1_comp))
plt.title("Range profile")
plt.xlabel("Range (m)")
plt.ylabel("Corresponding frequency component intensity")
plt.grid(True)
plt.show()

'''
rx1_re = pktbuf[:512:4] + pktbuf[1:512:4]
rx1_im = pktbuf[2:512:4] + pktbuf[3:512:4]

for i in range(len(rx1_comp)):
    if i == 0:
        arr_re = (rx1_re[i],rx1_re[i+1])
        arr_im = (rx1_im[i],rx1_im[i+1])
    else:
        arr_re = (rx1_re[(i*2)-1],rx1_re[i*2])
        arr_im = (rx1_im[(i*2)-1],rx1_im[i*2])
        rx1_comp[i] = int.from_bytes(arr_re,signed=True) + (1j*int.from_bytes(arr_im,signed=True))




print("Total number of packets in the pcap file: ", counter)
print("Total number of ip packets: ", ipcounter)
print("Total number of udp packets: ", udpcounter)


with open((filename), 'rb') as f:
    pcap = dpkt.pcap.Reader(f)
    pktBuf = pcap.readpkts()
    print(type(pktBuf))
    print(len(pktBuf))

    print(type(pktBuf[2][1]))
    print(pktBuf[2][1])

'''