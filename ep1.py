import os, sys, argparse, subprocess, re

def 

def main():
    PING = ["ping", "localhost", "-c", "1"]
    COUNT = 500

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

    print(PING)

    sampleRTT = []

    for i in range(COUNT):
        response = subprocess.run(PING, stdout = subprocess.PIPE)
        print(response.stdout.decode("UTF-8"))
        sampleRTT = re.findall('(?<=time=)\d{1,3}\.\d{1,3}', response.stdout.decode("UTF-8"))
        sampleRTT.append(rtt[0])
    
    print (rttList)

if __name__ == "__main__":
    main()


