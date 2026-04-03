#!/usr/bin/python3
# title: fcfs.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 21.06.2022

import utils.general_management as management

def run(queue, clouds, tasks):
	
	# print("executando FCFS....")
	result = {}
	
	local_tasks = {}
	local_tasks_deadline = {}

	for i in queue.get_queue():
		if queue.task_queue_control[i]['status'] == 'PENDING':
			local_tasks[i] = queue.task_queue_control[i]['size']
			local_tasks_deadline[i] = queue.task_queue_control[i]['deadline']

	# print("Tarefas:")
	# for i in queue.task_queue_control:
	# 	print(i, queue.task_queue_control[i])
	sorted_clouds = []
	local_clouds = {}
	for i in clouds.clouds:
		local_clouds[i] = clouds.clouds[i]['mips']
		sorted_clouds.append(i)

	# sorted_clouds = sorted(local_clouds, key=lambda x: local_clouds[x], reverse=False)
	# sorted_clouds = sorted(local_clouds, key=lambda x: local_clouds[x], reverse=False)
	resource_splited = {}

	for cloud in range(len(sorted_clouds)):
		
		if len(local_tasks) > 0:

			id_nuvem = sorted_clouds[cloud]
			result[id_nuvem] = {}

			cloud_capacity = sorted_clouds[cloud]
			local_result = {}

			min_task_size = min(local_tasks, key=local_tasks.get)
			if local_tasks[min_task_size] > local_clouds[id_nuvem]:
				# print("NUVEM SEM RECURSOS!")
				break

			# FIFO GREEDY CLASSICO
			for task in local_tasks:
				if local_tasks[task] <= cloud_capacity:
					local_result[task] = -1
					cloud_capacity -= local_tasks[task]
				else:
					break
			
			if len(local_result) > 0:

				# VERIFICA PROCESSAMENTO E ADICIONA ESTIMATIVA NA TAREFA
				processing = management.get_processing_time(local_clouds[id_nuvem], tasks, local_result)
				for task in processing:
					local_result[task] = processing[task]

				# MAPEAMENTO DE USO DOS RECURSOS
				resource_splited[id_nuvem] = management.split_resource(local_result, clouds.clouds[id_nuvem], local_tasks)

				# REMOVE TAREFAS ESCALONADAS E VERIFICADAS
				for i in local_result:
					del local_tasks[i]
					del local_tasks_deadline[i]

				result[id_nuvem] = local_result

			else:
				# SEM RESULTADO
				pass
		else:
			# TODAS TAREFAS ESCALONADAS
			break
	
	# print(" ** ",result)
	return result, resource_splited
