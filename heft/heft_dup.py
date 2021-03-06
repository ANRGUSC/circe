from __future__ import division
import create_input
from create_input import init
from copy import deepcopy
import numpy as np

"""
This module is the HEFT algorithm.
"""

# Time duration about a task
class Duration:
    def __init__(self, task, start, end):
        self.task_num = task
        self.start = start
        self.end = end


# Task class represent a task
class Task:
    def __init__(self, num):
        self.number = num
        self.ast = -1
        self.aft = -1
        self.processor_num = -1
        self.up_rank = -1
        self.down_rank = -1
        self.comp_cost = []
        self.avg_comp = 0
        self.pre_task_num = -1


# Processor class represent a processor
class Processor:
    def __init__(self, num):
        self.number = num
        self.time_line = []


# A class of scheduling algorithm
class HEFT:
    def __init__(self, filename):
        """
        Initialize some parameters.
        """
        self.num_task, self.task_names, self.num_processor, comp_cost, self.rate, self.data,self.quaratic_profile = init(filename)

        self.tasks = [Task(n) for n in range(self.num_task)]
        self.processors = [Processor(n) for n in range(self.num_processor)]
        self.start_task_num, self.end_task_num = 0, self.num_task-1
        self.dup_tasks = []
        self.critical_pre_task_num = -1


        for i in range(self.num_task):
            self.tasks[i].comp_cost = comp_cost[i]

        for task in self.tasks:
            task.avg_comp = sum(task.comp_cost) / self.num_processor

        self.cal_up_rank(self.tasks[self.start_task_num])
        self.cal_down_rank(self.tasks[self.end_task_num])
        self.tasks.sort(cmp=lambda x, y: cmp(x.up_rank, y.up_rank), reverse=True)

    # Modified communication part
    def cal_comm_quadratic(self,file_size,quaratic_profile):
        # quaratic_profile[0]*x^2 + quaratic_profile[1]*x +c; x=file_size[Kbit]
        return (np.square(file_size)*quaratic_profile[0] + file_size*quaratic_profile[1] + quaratic_profile[2])

    def cal_avg_comm(self, task1, task2):
        """
        Calculate the average communication cost between task1 and task2.
        """

        #self.data[task1.number][task2.number] Kbit
        res = 0
        for i in range(self.num_processor):
            for j in range(self.num_processor):
                if i==j: continue
                res += self.cal_comm_quadratic(self.data[task1.number][task2.number],self.quaratic_profile[i][j])

        return res / (self.num_processor ** 2 - self.num_processor)

    # def cal_avg_comm(self, task1, task2):
    #     """
    #     Calculate the average communication cost between task1 and task2.
    #     """
    #
    #     res = 0
    #     for line in self.rate:
    #         for rate in line:
    #             if rate != 0:
    #
    #                 res += self.data[task1.number][task2.number] / rate
    #
    #     return res / (self.num_processor ** 2 - self.num_processor)

    def cal_up_rank(self, task):
        """
        Calculate the upper rank of all tasks.
        Parameter task is the entry node of the DAG.
        """
        longest = 0
        for successor in self.tasks:
            if self.data[task.number][successor.number] != -1:
                if successor.up_rank == -1:
                    self.cal_up_rank(successor)

                longest = max(longest, self.cal_avg_comm(task, successor) + successor.up_rank)

        task.up_rank = task.avg_comp + longest

    def cal_down_rank(self, task):
        """
        Calculate the down rank of all tasks.
        Parameter task is the exit node of the DAG.
        """
        if task == self.tasks[self.start_task_num]:
            task.down_rank = 0
            return
        for pre in self.tasks:
            if self.data[pre.number][task.number] != -1:
                if pre.down_rank == -1:
                    self.cal_down_rank(pre)
    
                task.down_rank = max(task.down_rank,
                                     pre.down_rank + pre.avg_comp + self.cal_avg_comm(pre, task))

    # Modified communication part
    def cal_est(self, task, processor):
        """
        Calculate the earliest start time of task on processor.
        """
        est = 0
        for pre in self.tasks:
            if self.data[pre.number][task.number] != -1:
                if pre.processor_num != processor.number:
                    for dup_task in self.dup_tasks:
                        if dup_task.number == pre.number and dup_task.processor_num == task.processor_num:
                            c = 0
                            break
                    else:
                        c = self.cal_comm_quadratic(self.data[pre.number][task.number],self.quaratic_profile[pre.processor_num][processor.number])
                        #c = self.data[pre.number][task.number] / self.rate[pre.processor_num][processor.number]
                else:
                    c = 0
                if pre.aft + c > est:
                    est = pre.aft + c
                    self.critical_pre_task_num = pre.number

                #est = max(est, pre.aft + c)

        time_slots = []
        if len(processor.time_line) == 0:
            time_slots.append([0, 9999])
        else:
            for i in range(len(processor.time_line)):
                if i == 0:
                    if processor.time_line[i].start != 0:
                        time_slots.append([0, processor.time_line[i].start])
                    else:
                        continue
                else:
                    time_slots.append([processor.time_line[i - 1].end, processor.time_line[i].start])
            time_slots.append([processor.time_line[len(processor.time_line) - 1].end, 9999])

        for slot in time_slots:
            if est < slot[0] and slot[0] + task.comp_cost[processor.number] <= slot[1]:
                return slot[0]
            if est >= slot[0] and est + task.comp_cost[processor.number] <= slot[1]:
                return est


    # def cal_est(self, task, processor):
    #     """
    #     Calculate the earliest start time of task on processor.
    #     """
    #     est = 0
    #     for pre in self.tasks:
    #         if self.data[pre.number][task.number] != -1:
    #             if pre.processor_num != processor.number:
    #                 for dup_task in self.dup_tasks:
    #                     if dup_task.number == pre.number and dup_task.processor_num == task.processor_num:
    #                         c = 0
    #                         break
    #                 else:
    #                     c = self.data[pre.number][task.number] / self.rate[pre.processor_num][processor.number]
    #             else:
    #                 c = 0
    #             if pre.aft + c > est:
    #                 est = pre.aft + c
    #                 self.critical_pre_task_num = pre.number
    #
    #             #est = max(est, pre.aft + c)
    #
    #     time_slots = []
    #     if len(processor.time_line) == 0:
    #         time_slots.append([0, 9999])
    #     else:
    #         for i in range(len(processor.time_line)):
    #             if i == 0:
    #                 if processor.time_line[i].start != 0:
    #                     time_slots.append([0, processor.time_line[i].start])
    #                 else:
    #                     continue
    #             else:
    #                 time_slots.append([processor.time_line[i - 1].end, processor.time_line[i].start])
    #         time_slots.append([processor.time_line[len(processor.time_line) - 1].end, 9999])
    #
    #     for slot in time_slots:
    #         if est < slot[0] and slot[0] + task.comp_cost[processor.number] <= slot[1]:
    #             return slot[0]
    #         if est >= slot[0] and est + task.comp_cost[processor.number] <= slot[1]:
    #             return est

    def duplicate(self):
        """
        Reduce the communication overhead according copying the redundant tasks.
        """
        for pre_task in self.tasks:
            pre_processor_num = pre_task.processor_num
            for task in self.tasks:
                if pre_task == task or task.pre_task_num != pre_task.number:
                    continue
                processor_num = task.processor_num
                if pre_processor_num == processor_num:
                    continue
                dup_task_ast = self.cal_est(pre_task, self.processors[processor_num])
                dup_task_aft = dup_task_ast + pre_task.comp_cost[processor_num]
                if dup_task_aft > task.ast:
                    continue

                dup_task = Task(pre_task.number)
                dup_task.ast = dup_task_ast
                dup_task.aft = dup_task_aft
                dup_task.processor_num = processor_num
                self.dup_tasks.append(dup_task)
                self.processors[dup_task.processor_num].time_line.append(
                                Duration(-1, dup_task.ast, dup_task.aft))
                self.processors[processor_num].time_line.sort(cmp=lambda x, y: cmp(x.start, y.start))
                print 'task %d dup on processor %d' % (pre_task.number, processor_num)

    def reschedule(self):
        """
        After duplication, you should reschedule all tasks except redundant tasks.
        """
        # clear the time line list
        for p in self.processors:
            p.time_line = filter(lambda duration: duration.task_num == -1, p.time_line)

        for task in self.tasks:
            processor_num = task.processor_num
            est = self.cal_est(task, self.processors[processor_num])
            task.ast = est
            task.aft = est + task.comp_cost[processor_num]
            self.processors[task.processor_num].time_line.append(Duration(task.number, task.ast, task.aft))
            self.processors[processor_num].time_line.sort(cmp=lambda x, y: cmp(x.start, y.start))

    def run(self):
        for task in self.tasks:
            if task == self.tasks[0]:
                w = min(task.comp_cost)
                p = task.comp_cost.index(w)
                task.processor_num = p
                task.ast = 0
                task.aft = w
                self.processors[p].time_line.append(Duration(task.number, 0, w))
            else:
                aft = 9999
                for processor in self.processors:
                    est = self.cal_est(task, processor)
		    print("est:",est)
	            print("task:",task.comp_cost[processor.number])
                    if est + task.comp_cost[processor.number] < aft:
                        aft = est + task.comp_cost[processor.number]
                        p = processor.number
                        # Find the critical pre task
                        task.pre_task_num = self.critical_pre_task_num
    
                task.processor_num = p
                task.ast = aft - task.comp_cost[p]
                task.aft = aft
                self.processors[p].time_line.append(Duration(task.number, task.ast, task.aft))
                self.processors[p].time_line.sort(cmp=lambda x, y: cmp(x.start, y.start))

        self.duplicate()
        self.reschedule()


    def output_file(self):
        output = open('../config_security1.txt',"a")
        num = len(self.data)
        #output.write(str(num))
        #output.write('\n')
        #print("DATA:")
        #print(self.data)
        """
        for i in range(len(self.data)):
            output.write("task"+ str(i+1)+" ")
            if i==len(self.data)-1:
                output.write("scheduler")
            for j in range(len(self.data[i])):  
                if self.data[i][j] != -1:
                    output.write("task" +str(j+1)+" ")
            output.write('\n')
        """
        for p in self.processors:
            for duration in p.time_line:
                if duration.task_num != -1:
                    output.write(self.task_names[duration.task_num] + " node"+ str(p.number+1))
                    output.write('\n')

        output.close()

    def display_result(self):
        for t in self.tasks:
            print 'task %d : up_rank = %f, down_rank = %f' % (t.number, t.up_rank, t.down_rank)
            if t.number == self.end_task_num:
                makespan = t.aft

        for p in self.processors:
            print 'processor %d:' % (p.number + 1)
            for duration in p.time_line:
                if duration.task_num != -1:
                    print 'task %d : ast = %d, aft = %d' % (duration.task_num + 1,
                                                            duration.start, duration.end)

        for dup in self.dup_tasks:
            print 'redundant task %s on processor %d' % (dup.number + 1, dup.processor_num + 1)

        print 'makespan = %d' % makespan

