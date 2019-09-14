import os, sys, argparse, re, subprocess, time
import statistics as st
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm

def EstimatedRTT(prevEstRTT, sampleRTT, alpha):
	return (1-alpha)*prevEstRTT + alpha*sampleRTT

def DevRTT(prevDevRTT, sampleRTT, estimatedRTT, beta):
    return (1-beta)*prevDevRTT + beta*abs(sampleRTT-estimatedRTT)

def TimeoutInterval(estimatedRTT, devRTT):
    return estimatedRTT + 4*devRTT

def main():
    alpha = 0.125 # EstimatedRTT coefficient
    beta = 0.25 # DevRTT coefficient
    count = 500	# number of SampleRTT values
    endpoint = "www.msu.ru"
    rePattern = '(?<=time=)\d{1,3}\.?\d{1,3}'

    # Command line arguments parsing
    parser = argparse.ArgumentParser(description = "Simple RTT analysis.")

    parser.add_argument("-e", "--endpoint", metavar = "addr", help = "The target address for the pings.\nDefault is \"www.msu.ru\".")
    parser.add_argument("-c", "--count", metavar = "count", type = int, help = "Number of pings.\nDefault is 500.")
    ipvx = parser.add_mutually_exclusive_group()
    ipvx.add_argument("-4", "--ipv4", action = "store_true", help = "Force use IPv4.")
    ipvx.add_argument("-6", "--ipv6", action = "store_true", help = "Force use IPv4.")

    args = parser.parse_args()

    if args.endpoint is not None:
        endpoint = args.endpoint
    
    if args.count is not None and args.count >= 1:
        count = args.count
    
    cmd = ["ping", endpoint, "-c", "1", "-W", "1"]

    if args.ipv4:
        cmd.append("-4")
    elif args.ipv6:
        cmd.append("-6")

    # Acquire SampleRTT data.
    print("Acquiring data for " + str(count) + " pings. This may take a while.")
    
    sampleRTT = []
    for i in tqdm(range(count)):
        # Execute cmd process to get raw ping data
        proc = subprocess.run(cmd, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        rawRTT = proc.stdout

        # Parse raw SampleRTT data to float list (ms)
        rtt = re.findall(rePattern, rawRTT)

        # Check if ping succeeded
        if len(rtt) == 1:
            sampleRTT.append(float(rtt[0]))
            if float(rtt[0] == 0):
                print (rawRTT)

        #time.sleep(0.5) # Pings without delay seem to cause timeouts


    # Calculate EstimatedRTT and DevRTT lists
    estimatedRTT = [0]*len(sampleRTT)
    devRTT = [0]*len(sampleRTT)
    timeoutInterval = [0]*len(sampleRTT)
    
    # Initial conditions
    estimatedRTT[0] = sampleRTT[0]
    devRTT[0] = 0.0
    timeoutInterval[0] = TimeoutInterval(estimatedRTT[0], devRTT[0])

    for i in range(1, len(sampleRTT)):
        estimatedRTT[i] = EstimatedRTT(estimatedRTT[i-1], sampleRTT[i], alpha)
        devRTT[i] = DevRTT(devRTT[i-1], sampleRTT[i], estimatedRTT[i], beta)
        timeoutInterval[i] = TimeoutInterval(estimatedRTT[i], devRTT[i])

    # Basic statistics. [0]-SampleRTT, [1]-EstimatedRTT, [2]-DevRTT, [3]-TimeoutInterval
    mean = [st.mean(sampleRTT), st.mean(estimatedRTT), st.mean(devRTT), st.mean(timeoutInterval)]
    stDeviation = [st.stdev(sampleRTT), st.stdev(estimatedRTT), st.stdev(devRTT), st.stdev(timeoutInterval)]

    print("")
    print(f"SampleRTT      : mean = {round(mean[0], 5)}ms / stdev =  {round(stDeviation[0], 5)}ms")
    print(f"EstimatedRTT   : mean = {round(mean[1], 5)}ms / stdev =  {round(stDeviation[1], 5)}ms")
    print(f"DevRTT         : mean = {round(mean[2], 5)}ms / stdev =  {round(stDeviation[2], 5)}ms")
    print(f"TimeoutInterval: mean = {round(mean[3], 5)}ms / stdev =  {round(stDeviation[3], 5)}ms")
    print(f"Packet loss: {(count-len(sampleRTT))*100/count}%")

    # Plotting
    x = np.arange(len(sampleRTT))

    plt.figure(1)
    plt.plot(x, sampleRTT, "red", label="SampleRTT")
    plt.plot(x, estimatedRTT, "green", label="EstimatedRTT")
    plt.plot(x, devRTT, "blue", label="DevRTT")
    plt.plot(x, timeoutInterval, "fuchsia", label="TimeoutInterval")
    plt.legend(loc="best")
    plt.title("RTT Analysis \"" + endpoint + "\"")
    plt.ylabel("Time [ms]")
    plt.xlabel("Ping iteration")
    plt.show()

    label = ["Success", "Timeout"]
    index = [0, 1]
    y = [len(sampleRTT), count - len(sampleRTT)]
    plt.figure(2)
    plt.bar(index, y)
    plt.ylabel("No. pings")
    plt.xticks(index, label)
    plt.title("Ping \"" + endpoint + "\" timeout comparison")
    for i, v in enumerate(y):
        plt.text(index[i] - 0.02, v + 0.1, str(v))
    plt.show()

if __name__ == "__main__":
    main()


