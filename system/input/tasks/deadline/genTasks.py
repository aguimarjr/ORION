#!/usr/bin/env python
# title: genTasks.py
# author: Joahannes Costa <joahannes@lrc.ic.unicamp.br>
# date: 01.03.2021

import numpy as np
import random
import os

def generate_tasks(task_n, size_n, cycle_n, deadline_initial, deadline_n, seed_n):

	print("Configuration:")
	print(' * ' + str(task_n) + ' tasks')
	print(' * ' + str(size_n) + ' Mb')
	print(' * ' + str(cycle_n) + ' cycles')
	print(' * (' + str(deadline_initial) + ', ' + str(deadline_n) + ') seconds')
	print(' * ' + str(seed_n) + ' seed')

	tasks = []
	# TASKS_SIZE_10_CPU_10_SEED_1
	task_file = open(str(deadline_n) + '/TASKS_SIZE_' + str(size_n) + '_CPU_' + str(cycle_n) + '_SEED_' + str(seed_n) + '.txt', 'w')

	last = 0.2

	for i in range(task_n):
		# <id, size, value, deadline>
		# 
		if len(str(i)) == 1:
			task_id = 'id-0000' + str(i)
		elif len(str(i)) == 2:
			task_id = 'id-000' + str(i)
		elif len(str(i)) == 3:
			task_id = 'id-00' + str(i)
		elif len(str(i)) == 4:
			task_id = 'id-0' + str(i)
		elif len(str(i)) == 5:
			task_id = 'id-' + str(i)
		task_size = random.randint(1,size_n)
		task_value = random.randint(2,task_size*2)
		task_cycle = random.randint(1,cycle_n)
		task_deadline = round( random.uniform(deadline_initial,deadline_n), 1)

		task_file.write(str(task_id) + "\t" + str(task_size) + "\t" + str(task_value) + "\t" + str(task_cycle) + "\t" + str(task_deadline) + "\n")

	task_file.close()

	return tasks

number = 20000
max_size = [10, 15, 20]
max_cycle = [10, 20, 30]
max_deadline = [0.5, 0.8, 1, 3, 5, 7]

SEEDS = [1,2,3,4,5]

for seed in SEEDS:
	for i in range(len(max_size)):
		for j in range(len(max_cycle)):
			lower_bound_deadline = 0.2
			for k in range(len(max_deadline)):
				# verifica se diretorio existe
				diretorio = str(max_deadline[k])
				if os.path.isdir(diretorio):
					generate_tasks(number, max_size[i], max_cycle[j], lower_bound_deadline, max_deadline[k], seed)
					lower_bound_deadline = max_deadline[k]
				else:
					os.makedirs(str(max_deadline[k]))
					generate_tasks(number, max_size[i], max_cycle[j], lower_bound_deadline, max_deadline[k], seed)
					lower_bound_deadline = max_deadline[k]
