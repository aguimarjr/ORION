#!/usr/bin/env python
# title: log_manager.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 25.03.2021

# LOG
#===============================================================#
# [0] step														#
# [1] recurso das vccs											#
# [2] numero de tarefas geradas									#
# [3] algoritmo utilizado										#
# [4] ganho por alocar as n tarefas								#
# [5] tarefas que foram alocadas								#
# [6] numero de vccs criadas									#
# [7] peso das tarefas											#
# [8] cpu_time													#
# [9] delay														#
#===============================================================#

import os
import numpy as np

def get_informations(radius, resources, weight, rate, megacycles, algorithm, seed, deadline):
	
	# cria diretorio para cada algoritmo em output
	dirName = 'output/' + algorithm
	if not os.path.isdir(dirName):
		os.makedirs(dirName, exist_ok=True)

	dirNameResult = 'results/' + algorithm
	if not os.path.isdir(dirNameResult):
		os.makedirs(dirNameResult, exist_ok=True)
	
	# # cria diretorio para cada algoritmo em log
	# dirNameLog = 'log/' + algorithm
	# if not os.path.isdir(dirNameLog):
	# 	os.makedirs(dirNameLog)

	global name_alloc
	global name_time
	global name_queue
	global name_cluster
	global name_fila
	global result_name
	global balance_name
	radius_log = int(radius)
	global resource_log 
	resource_log = resources
	weight_log = weight

	name_alloc = dirName + '/SEED_'+str(seed)+'_RESULTS_radius_'+str(radius_log)+'_resource_'+str(resource_log)+'_weight_'+str(weight_log)+'_rate_'+str(rate)+'_megacycles_'+str(megacycles)+'_deadline_'+str(deadline)+'.txt'
	name_time = dirName + '/SEED_'+str(seed)+'_TIME_radius_'+str(radius_log)+'_resource_'+str(resource_log)+'_weight_'+str(weight_log)+'_rate_'+str(rate)+'_megacycles_'+str(megacycles)+'_deadline_'+str(deadline)+'.txt'
	name_queue = dirName + '/SEED_'+str(seed)+'_COST_radius_'+str(radius_log)+'_resource_'+str(resource_log)+'_weight_'+str(weight_log)+'_rate_'+str(rate)+'_megacycles_'+str(megacycles)+'_deadline_'+str(deadline)+'.txt'

	# new result file
	result_name = dirNameResult + '/SEED_'+str(seed)+'_RESULTS_radius_'+str(radius_log)+'_resource_'+str(resource_log)+'_weight_'+str(weight_log)+'_rate_'+str(rate)+'_megacycles_'+str(megacycles)+'_deadline_'+str(deadline)+'.txt'

	balance_name = dirNameResult + '/SEED_'+str(seed)+'_BALANCE_resource_'+str(resource_log)+'_weight_'+str(weight_log)+'_rate_'+str(rate)+'_megacycles_'+str(megacycles)+'_deadline_'+str(deadline)+'.txt'

	if os.path.exists(name_alloc):
		os.system('rm ' + name_alloc)
	if os.path.exists(name_time):
		os.system('rm ' + name_time)
	if os.path.exists(name_queue):
		os.system('rm ' + name_queue)
	if os.path.exists(result_name):
		os.system('rm ' + result_name)
	if os.path.exists(balance_name):
		os.system('rm ' + balance_name)

	name_cluster = dirName + '/CLUSTER_SEED_1_' + str(rate) + '.txt'
	name_fila = dirName + '/FILA_SEED_1_' + str(rate) + '.txt'

def log_resources(step, number, resource_per_cluster, resource, weight, radius):
	resources_file = open('output/resources_'+str(radius)+'_'+str(resource)+'_'+str(weight)+'.txt','a')
	resources_file.write(str(step) + "," + str(number) + "," + str(resource_per_cluster) + "\n")
	resources_file.close()

	return resources_file

def log_tasks(step, number, tasks, resource, weight, radius):
	tasks_file = open('output/tasks_'+str(radius)+'_'+str(resource)+'_'+str(weight)+'.txt','a')
	tasks_file.write(str(step) + "," + str(number) + "," + str(tasks) + "\n")
	tasks_file.close()

	return tasks_file

def log_allocation(step, n_tasks, total_cpu_time):

	total_cpu_time = round(total_cpu_time, 5)

	allocation_file = open(name_alloc,'a')
	allocation_file.write(
		str(step) + "\t" +
		str(n_tasks) + "\t" +
		str(total_cpu_time) + "\n"
		)
	allocation_file.close()

def log_time(resultado):

	time_file = open(name_time,'a')
	time_file.write(str(resultado) + "\n")
	time_file.close()

def log_cost(resultado_price):

	queue_file = open(name_queue,'a')
	queue_file.write(str(resultado_price) + "\n")
	queue_file.close()

def log_cluster(step, nuvens):
	nuvem_escolhida = 4
	cluster_file = open(name_cluster, 'a')
	cluster_file.write(str(step) + '\t' + str(nuvens[nuvem_escolhida][0]) + '\n')
	cluster_file.close()

def log_fila(step, fila):
	fila_file = open(name_fila, 'a')
	fila_file.write(str(step) + '\t' + str(len(fila)) + '\n')
	fila_file.close()

def log_results(resultados):
	
	total_tasks = len(resultados)
	escalonadas = 0
	delay = []
	queue_time = []

	status_aceitos = ['PENDING', 'SUBMITTED', 'EXPIRED']

	for i in resultados:

		insert_time = float(resultados[i]['insert_time'])
		remove_time = float(resultados[i]['remove_time'])
		queue_time.append(remove_time - insert_time)

		if resultados[i]['status'] not in status_aceitos:
			start_time = float(resultados[i]['start_time'])
			finish_time = float(resultados[i]['finish_time'])
			delay.append(finish_time - start_time)
			escalonadas += 1
			
	porcentagem 			= round((escalonadas * 100 / total_tasks),2)
	total_delay 			= round(np.mean(delay), 2)
	total_delay_std 		= round(np.std(delay), 2)
	total_queue_time 		= round(np.mean(queue_time), 2)
	total_queue_time_std 	= round(np.std(queue_time), 2)

	print(" * Total:",total_tasks)
	print(" * Escalonadas:",escalonadas)
	print(" * Porcentagem:",porcentagem)
	print(" * Delay:", total_delay)
	print(" * Queue:", total_queue_time)

	allocation_file = open(name_alloc,'a')
	allocation_file.write(
		str(total_tasks) + "\t" +
		str(escalonadas) + "\t" +
		str(porcentagem) + "\t" +
		str(total_delay) + "\t" +
		str(total_delay_std) + "\t" +
		str(total_queue_time) + "\t" +
		str(total_queue_time_std) + "\n"
		)
	allocation_file.close()

def log_results_final(results):

	# guarda informacoes de processamento em arquivo de log
	total_tasks = len(results)

	# result file
	scheduling_file = open(name_alloc,'a')
	for task in results:
		scheduling_file.write(
			str(total_tasks) 					+ "\t" +
			str(task) 							+ "\t" +
			str(results[task]['size']) 			+ "\t" +
			str(results[task]['value']) 		+ "\t" +
			str(results[task]['cpu']) 			+ "\t" +
			str(results[task]['deadline']) 		+ "\t" +
			str(results[task]['insert_time']) 	+ "\t" +
			str(results[task]['start_time']) 	+ "\t" +
			str(results[task]['finish_time']) 	+ "\t" +
			str(results[task]['remove_time']) 	+ "\t" +
			str(results[task]['waiting_time']) 	+ "\t" +
			str(results[task]['cost']) 			+ "\t" +
			str(results[task]['status']) 		+ "\n"
		)
	scheduling_file.close()

	# consolidated result
	scheduled 		= 0
	processing_time = []
	queue_time 		= []
	cost 			= []

	for task in results:

		# para calcular tempo total de fila
		insert_time = float(results[task]['insert_time'])
		remove_time = float(results[task]['remove_time'])
		queue_time.append(remove_time - insert_time)

		# considera apenas tarefas que iniciaram o processamento
		if results[task]['start_time'] != None:

			# calcula tempo de processamento
			start_time = float(results[task]['start_time'])
			finish_time = float(results[task]['finish_time'])
			processing_time.append(finish_time - start_time)

			# contabiliza tarefas concluidas
			if results[task]['status'] == 'COMPLETED':
				scheduled += 1

			# tarefas podem usar recursos sem terem concluido seu processamento (escalonamento ruim)
			if results[task]['cost'] != None:
				cost.append(results[task]['cost'])
			
	percentage 				= round((scheduled * 100 / total_tasks), 3)
	total_delay 			= round(np.mean(processing_time), 3)
	total_delay_std 		= round(np.std(processing_time), 3)
	total_queue_time 		= round(np.mean(queue_time), 3)
	total_queue_time_std 	= round(np.std(queue_time), 3)
	total_cost				= round(np.mean(cost), 3)

	print(" * Total:",total_tasks)
	print(" * Scheduled:",scheduled)
	print(" * Percentage:",percentage)
	print(" * Delay:", total_delay)
	# print(" * Delay Std:", total_delay_std)
	print(" * Queue:", total_queue_time)
	# print(" * Queue Std:", total_queue_time_std)
	print(" * Cost:",total_cost)

	# consolidated result file
	result_file = open(result_name,'w')
	result_file.write(
		str(total_tasks) 		+ "\t" +
		str(scheduled)			+ "\t" +
		str(percentage)			+ "\t" +
		str(total_delay)		+ "\t" +
		str(total_queue_time)	+ "\t" +
		str(total_cost) 		+ "\n"
	)
	result_file.close()

def load_balance(results):
	balance = open(balance_name, 'w')
	total = 0
	for i in results:
		total += results[i]
	balance.write("total \t" + str(total) + "\n")
	for id_bs in results:
		balance.write(
			str(id_bs) 			+ "\t" +
			str(results[id_bs]) + "\n" 
		)
	balance.close()