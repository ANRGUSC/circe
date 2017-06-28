import os

import datetime
from os import path
from netifaces import AF_INET, AF_INET6, AF_LINK
import netifaces as ni

def task(queue):

    while True:
        if not queue.empty():
            execution_time=datetime.datetime.utcnow()
            file = queue.get()

            task2 = file.replace('.txt','')+"_task2.txt"

            pathout=os.path.join(os.path.dirname(os.path.abspath(__file__)),'output/')
            pathin=os.path.join(os.path.dirname(os.path.abspath(__file__)),'input/')

            pathrun=os.path.join(path.dirname(path.dirname(path.abspath(__file__))),'runtime/')
            task_name=path.basename(__file__).split('.')[0]
            file_name=task2.split('_')[0]

            my_ip=ni.ifaddresses('eth0')[AF_INET][0]['addr']
            runtime_file=os.path.join(pathrun,'droplet_runtime_task_%s'%(my_ip))
            with open(runtime_file, 'a') as f:
                line = 'execution_time,%s,%s,%s,%s,%f\n' %(my_ip,task_name,file_name,execution_time,0)
                f.write(line)

            file_output = open(pathout+task2, 'a')

            data = []
            with open(pathin+file,'r') as file_input:
                for line in file_input:
                    data.extend(map(int, line.strip().split(' ')))
            data = sorted(data)
            file_output.writelines( "%s " % item for item in data )

            file_input.close()
            file_output.close()

            finished_time=datetime.datetime.utcnow()
            output_size= os.path.getsize(pathout+task2)/1000 #in Kbits
            finishedtime_file=os.path.join(pathrun,'droplet_runtime_finished_%s'%(my_ip))
            with open(finishedtime_file, 'a') as f:
                line = 'finished_time,%s,%s,%s,%s,%f\n' %(my_ip,task_name,file_name,finished_time,output_size)
                f.write(line)