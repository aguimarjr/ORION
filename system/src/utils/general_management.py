#!/usr/bin/env python
# title: general_management.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 18.06.2023

def get_processing_time(cloud_frequency, tasks, local_schedule):
	
	tasks_frequency		= {}
	total_frequency		= cloud_frequency
	scheduled_tasks 	= len(local_schedule)
	shared_frequency	= total_frequency / scheduled_tasks

	for task in local_schedule:
		medida_tarefa = tasks.task_set_control[task]['cpu']
		task_time = round((medida_tarefa / shared_frequency), 2)
		tasks_frequency[task] = task_time

	return tasks_frequency

def split_resource(local_schedule, current_cloud, local_tasks):
	"Return the resources usage."
	
	resources	= {}
	vehicle		= current_cloud['vehicle_cpu']
	bs			= current_cloud['bs_cpu']

	for task in local_schedule:
		used_vehicle = 0
		used_bs = 0
		resources[task] = {}
		size_task = local_tasks[task]
		for i in range(1, size_task + 1):

			if vehicle > 0:
				vehicle -= 1
				used_vehicle += 1
			elif vehicle == 0:
				size_task = size_task - used_vehicle
				if bs > 0:
					bs -= 1
					used_bs += 1
			
			resources[task]['vehicle']			= used_vehicle
			resources[task]['bs'] 				= used_bs
			resources[task]['processing_time'] 	= local_schedule[task]
			resources[task]['size'] 			= local_tasks[task]

	# print("Resouces Usage:",resources)
	return resources