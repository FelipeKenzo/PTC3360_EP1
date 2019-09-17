import os, sys, argparse, re, subprocess, time, json
import statistics as st
import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
from urllib import request

def EstimatedRTT(prevEstRTT, sampleRTT, alpha):
	return (1-alpha)*prevEstRTT + alpha*sampleRTT

def DevRTT(prevDevRTT, sampleRTT, estimatedRTT, beta):
    return (1-beta)*prevDevRTT + beta*abs(sampleRTT-estimatedRTT)

def TimeoutInterval(estimatedRTT, devRTT):
    return estimatedRTT + 4*devRTT

def main():
    count = 500	# number of SampleRTT values.
    endpoint = "www.google.com" # host to be ping.
    ping = ["ping", endpoint, "-c", "1", "-W", "1"] # subprocess ping command.

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
    

    if args.ipv4:
        ping.append("-4")
    elif args.ipv6:
        ping.append("-6")

    # Acquire SampleRTT data.
    print(f"Acquiring data for {str(count)} pings to {endpoint}. This may take a while.\n")
    
    timeRe = '(?<=time=)\d{1,3}\.?\d{1,3}' # Regular expression for RTT time.
    
    sampleRTT = []
    for i in tqdm(range(count)):
        # Execute ping process to get raw ping data
        rawRTT = subprocess.run(ping, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

        # Parse raw SampleRTT data to float list (ms)
        rtt = re.findall(timeRe, rawRTT)

        # Check if ping succeeded
        if len(rtt) == 1:
            sampleRTT.append(float(rtt[0]))

    # Calculate EstimatedRTT and DevRTT lists
    alpha = 0.125 # EstimatedRTT coefficient
    beta = 0.25 # DevRTT coefficient

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
    print(f"Packet loss: {(count-len(sampleRTT))*100/count}%\n")

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

    # Traceroute:
    print(f"\nExecuting traceroute to {endpoint}...\n")

    trace = ["traceroute", endpoint, "-I"] # Subprocess traceroute command.

    # Execute traceroute subprocess to get raw data.
    rawTraceroute = subprocess.run(trace, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    print (rawTraceroute)

    # Parse raw traceroute data for IP adresses.
    ipRe = "(?<=\()\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    traceroute = re.findall(ipRe, rawTraceroute)

    addresses  = []
    latitudes  = []
    longitudes = []

    if traceroute[0] == traceroute[len(traceroute)-1]:
        print ("Success!\n")

        # Acquire location information via 'ipstack' API.
        token = "?access_key=e9813e976ddae123776ef76ad2e4fbd7"
        url = "http://api.ipstack.com/"

        print(f"Aquiring geolocation data for {len(traceroute)-1} IPs.\n")

        for i in tqdm(range(len(traceroute)-1)):
            req = url + traceroute[i+1] + token
            resp = request.urlopen(req)

            if resp.code == 200:
                rawData = resp.read()
                encoding = resp.info().get_content_charset('utf-8')
                data = json.loads(rawData.decode(encoding))

                addresses.append(data["zip"])
                latitudes.append(data["latitude"])
                longitudes.append(data["longitude"])
    
    print("\n" + latitudes)
    print("\n" + longitudes)
    print("\n" + addresses)






if __name__ == "__main__":
    main()


