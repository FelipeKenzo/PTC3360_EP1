import os, sys, argparse, re, subprocess
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

def EstimatedRTT(prevEstRTT, sampleRTT, alpha):
	return (1-alpha)*prevEstRTT + alpha*sampleRTT

def DevRTT(prevDevRTT, sampleRTT, estimatedRTT, beta):
    return (1-beta)*prevDevRTT + beta*abs(sampleRTT-estimatedRTT)

def toFloat(n):
    return float(n)

def main():
    alpha = 0.125 # EstimatedRTT coefficient
    beta = 0.25 # DevRTT coefficient
    count = 500	# number of SampleRTT values
    endpoint = "google.com"
    rePattern = '(?<=time=)\d{1,3}\.\d{1,3}'

    # Command line arguments parsing
    parser = argparse.ArgumentParser(description = "Simple RTT analysis.")

    parser.add_argument("-e", "--endpoint", metavar = "addr", help = "The target address for the pings.\nDefault is \"localhost\".")
    parser.add_argument("-c", "--count", metavar = "count", type = int, help = "Number of pings.\nDefault is 500.")
    ipvx = parser.add_mutually_exclusive_group()
    ipvx.add_argument("-4", "--ipv4", action = "store_true", help = "Force use IPv4.")
    ipvx.add_argument("-6", "--ipv6", action = "store_true", help = "Force use IPv4.")

    args = parser.parse_args()

    if args.endpoint is not None:
        endpoint = args.endpoint
    
    if args.count is not None and args.count >= 1:
        count = args.count
    
    cmd = ["ping", endpoint, "-c", str(count)]


    if args.ipv4:
        cmd.append("-4")
    elif args.ipv6:
        cmd.append("-6")

    # Acquire SampleRTT raw data.
    print("Acquiring data for " + str(count) + " pings. This may take a while.")
    
    sampleRTT = []
    while True:
        proc = subprocess.run(cmd, encoding="utf-8", stdout=subprocess.PIPE)
        rawRTT = proc.stdout

        # Parse raw SampleRTT data to float list (ms)
        temp = re.findall(rePattern, rawRTT)
        sampleRTT += list(map(toFloat, temp))

        remaining = count - len(sampleRTT)
        
        print("Run completed, " + str(remaining) + " timeouts.")
        
        if remaining <= 0:
            break

        cmd[3] = str(remaining)

    # Calculate EstimatedRTT and DevRTT lists
    print("Calculating EstimatedRTT and DevRTT.")
    estimatedRTT = [0]*count
    devRTT = [0]*count
    
    estimatedRTT[0] = sampleRTT[0]
    devRTT[0] = 0.0

    for i in range(1, count):
        print(i)
        estimatedRTT[i] = EstimatedRTT(estimatedRTT[i-1], sampleRTT[i], alpha)
        devRTT[i] = DevRTT(devRTT[i-1], sampleRTT[i], estimatedRTT[i], beta)

    print(estimatedRTT)
    print(devRTT)

    # Plotting

    x = [0]*count
    for i in range(count):
        x[i] = i

    plt.plot(x, sampleRTT, "r-", label="SampleRTT")
    plt.plot(x, estimatedRTT, "g-", label="EstimatedRTT")
    plt.plot(x, devRTT, "b-", label="DevRTT")
    plt.legend(loc="best")
    plt.show()


if __name__ == "__main__":
    main()


