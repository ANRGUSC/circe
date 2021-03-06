"""
 * Copyright (c) 2017, Autonomous Networks Research Group. All rights reserved.
 *     contributors: 
 *      Pranak Sakulkar
 *      Jiatong Wang
 *      Aleksandra Knezevic
 *      Bhaskar Krishnamachari
 *     Read license file in main directory for more details  
"""

import sys
import numpy as np
import os
import time

pktPerHost = dict()
ipBinStart = dict()


def get_pkgPerhost(ipsum_filename,pathin):
    nbStd = 2.0  # Detection threshold

    with open(os.path.join(pathin,ipsum_filename), 'r') as f:
        for line in f:

            # ignore header
            if line.startswith("!"):
                continue

            # get each fields of the tuple
            fields = line.split()
            ts = float(fields[0])
            ipSrc = fields[1]
            ipDst = fields[3]

            if ipSrc in pktPerHost:
                pktPerHost[ipSrc] += 1
            else:
                pktPerHost[ipSrc] = 1

            if ipDst in pktPerHost:
                pktPerHost[ipDst] += 1
            else:
                pktPerHost[ipDst] = 1

    # compute the threshold based on the mean and standard deviation
    pktCount = np.array(list(pktPerHost.values()))
    mean = np.mean(pktCount)
    std = pktCount.std()
    threshold = mean + nbStd * std

    if True:
        print("Packet counts:", pktCount)
        print("Mean:", mean)
        print("Std deviation:", std)
        print("Threshld:", threshold)

        for host, val in pktPerHost.items():
            print(host, val)
            break

    return threshold

    # report anomalous IP addresses
    # with open('anomalies_simple.log', 'w') as f:
    #   for host, val in pktPerHost.iteritems():
    #     if val > threshold:
    #        f.write(host+":* *:*;"+str(binStart)+";"+str(binEnd)+";"+str(val)+"\n")
    #        f.write("*:* "+host+":*;"+str(binStart)+";"+str(binEnd)+";"+str(val)+"\n")


def task(filename, pathin, pathout):

    time.sleep(10)
    num = filename.partition('m')[0]

    threshold = get_pkgPerhost(filename,pathin)

    binSize = 10
    binStart = 0
    lines=[]


    with open(os.path.join(pathin, filename), 'r') as f:
        for line in f:

        # ignore header
            if line.startswith("!"):
                continue

            # get each fields of the tuple
            fields = line.split()
            ts = float(fields[0])
            ipSrc = fields[1]
            ipDst = fields[3]

            if ts > binStart + binSize:
              if binStart == 0:  # first time in the loop
                  binStart = ts

              val_src = pktPerHost[ipSrc]
              val_dst = pktPerHost[ipDst]

              if val_src > threshold:
                  lines.append(ipSrc + ":* *:*;" + str(
                                        binStart) + ";" + str(binStart + binSize) + "\n")

              if val_dst > threshold:
                  lines.append("*:* "+ipDst+":*;" + str(binStart) + ";" + str(binStart + binSize) + "\n")

              binStart += binSize

    with open(os.path.join(pathout, num+'anomalies_simple0.log'), 'w') as writeout:
        for k in lines:
            writeout.write(k)


if __name__ == '__main__':

    filename = '1merged_file0.ipsum'
    task(filename, '/home/apac/security_app','/home/apac/security_app')
