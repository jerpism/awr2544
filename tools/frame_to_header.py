import dpkt
import numpy as np
import matplotlib.pyplot as plt
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("fname", help="name of .pcap file to parse")
parser.add_argument("frame_num", help="index of frame to parse into C header")
parser.add_argument("-o", "--output", default="framedata.h", type=str, help="name of output .h file")
args = parser.parse_args()

filename=args.fname
eval_frame_num = int(args.frame_num)

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


def export_frame_to_header(data, header_filename, var_name="frame_data"):
    """
    Exports complex data of shape (4, 128, 128) to a C header file,
    where each complex number (a + jb) is flattened as [a, b].

    Parameters:
        data: np.ndarray
            Complex input array of shape (4, 128, 128)
        header_filename: str
            Output .h filename
        var_name: str
            Name of the variable in the C file
    """
    assert data.shape == (4, 128, 128), "Expected input shape (4, 128, 128)"

    rx, chirps, rangebins = data.shape
    flat_rangebins = rangebins * 2  # real and imag per bin

    with open(header_filename, "w") as f:
        f.write("// Auto-generated radar data header\n")
        f.write(f"#ifndef {var_name.upper()}_H\n")
        f.write(f"#define {var_name.upper()}_H\n\n")

        f.write(f"#define NUM_RX {rx}\n")
        f.write(f"#define NUM_CHIRPS {chirps}\n")
        f.write(f"#define NUM_RANGEBINS_FLAT {flat_rangebins}\n\n")

        f.write(f"static float {var_name}[NUM_RX][NUM_CHIRPS][NUM_RANGEBINS_FLAT] = {{\n")

        for r in range(rx):
            f.write("  {\n")
            for c in range(chirps):
                line = "    {" + ", ".join(
                    f"{data[r, c, b].real:.6f}, {data[r, c, b].imag:.6f}"
                    for b in range(rangebins)
                ) + "},\n"
                f.write(line)
            f.write("  },\n")
        f.write("};\n\n")

        f.write(f"#endif // {var_name.upper()}_H\n")

    print(f"Header file '{header_filename}' written with shape [4][128][256] (real, imag pairs).")




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

                #print(f"pktbuf len: {len(pktbuf)}, pktbuf type: {type(pktbuf)}, pktbuf[0] type: {type(pktbuf[0])}")
                #print(f"frame shape: {np.shape(frame)}, cell type: {type(frame[0][0][0])}, val: {frame[0][0][10]}")           

                if framecounter == eval_frame_num:
                    
                    frame = unpackPktBuf(pktbuf)
                    export_frame_to_header(frame,args.output)

                    

                pktbuf = []
                chirpcounter = 0