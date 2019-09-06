import os, sys, argparse, subprocess, re, platform
import time
from tqdm import tqdm

def EstimatedRTT(prevEstRTT, sampleRTT, alpha):
	return alpha*prevEstRTT + (1-alpha)*sampleRTT

def main():
    PING = ["ping", "google.com", "-c", "1"] # List of shell commands for subprocess.run
    COUNT = 500	# number of SampleRTT values
    ALPHA = 0.9 # EstimatedRTT coefficient
    PATTERN = '(?<=time=)\d{1,3}\.\d{1,3}' # regex for parsing system response to ping command.

    # Command line arguments parsing
    parser = argparse.ArgumentParser(description = "Simple RTT analysis.")

    parser.add_argument("-e", "--endpoint", metavar = "addr", help = "The target address for the pings.\nDefault is \"localhost\".")
    parser.add_argument("-c", "--count", metavar = "count", type = int, help = "Number of pings.\nDefault is 500.")
    ipvx = parser.add_mutually_exclusive_group()
    ipvx.add_argument("-4", "--ipv4", action = "store_true", help = "Force use IPv4.")
    ipvx.add_argument("-6", "--ipv6", action = "store_true", help = "Force use IPv4.")

    args = parser.parse_args()

    if args.endpoint is not None:
        PING[1] = args.endpoint
    
    if args.count is not None and args.count >= 1:
        COUNT = args.count
    
    if args.ipv4:
        PING.append("-4")
    elif args.ipv6:
        PING.append("-6")

    # Data lists initialization
    sampleRTT = [0]*COUNT
    estimatedRTT = [0]*COUNT

    # Acquire SampleRTT series.
    for i in tqdm(range(COUNT)):
        response = subprocess.run(PING, stdout = subprocess.PIPE)
        currentRTT = re.findall(PATTERN, response.stdout.decode("utf-8"))
        print
        if currentRTT.count != 0:
        	sampleRTT[i] = currentRTT[0]
        else:
        	i -= 1
    
    print (sampleRTT)

    estimatedRTT[0] = sampleRTT[0]

    for i in range(1, estimatedRTT.count-1):
    	estimatedRTT[i] = EstimatedRTT(estimatedRTT[i-1], sampleRTT[i], ALPHA)

    print (estimatedRTT)


if __name__ == "__main__":
    main()


