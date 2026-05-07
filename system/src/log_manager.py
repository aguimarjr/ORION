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

"""
Módulo para gerenciamento de logs e consolidação de resultados da simulação.

Este módulo centraliza a criação de arquivos de saída, registro de métricas
intermediárias (tempo, custo, filas, recursos e tarefas) e geração de
estatísticas consolidadas ao final da execução.

Principais responsabilidades:
    - Preparar diretórios e nomes de arquivos de log por configuração.
    - Registrar eventos e métricas por passo da simulação.
    - Consolidar resultados finais de escalonamento.
    - Exportar relatório de balanceamento de carga.

Observações:
    - O módulo utiliza variáveis globais para armazenar os nomes dos arquivos
      de saída após a chamada de `get_informations`.
    - As funções de escrita assumem que `get_informations` foi executada antes.
"""


import os
import numpy as np

def get_informations(radius, resources, weight, rate, megacycles, algorithm, seed, deadline):
	"""
	Inicializa diretórios e arquivos de saída para uma execução da simulação.

	Esta função define caminhos de arquivos globais usados pelas demais rotinas
	de log e remove arquivos antigos (quando existirem) para evitar mistura de
	resultados entre execuções.

	Args:
		radius (int | float): Raio utilizado no cenário.
		resources (int): Quantidade de recursos disponíveis.
		weight (int | float): Peso/configuração de carga.
		rate (int): Taxa de chegada de tarefas.
		megacycles (int): Demanda de CPU em megaciclos.
		algorithm (str): Nome do algoritmo em execução.
		seed (int): Semente para reprodutibilidade.
		deadline (int | float): Deadline adotado no cenário.

	Side Effects:
		- Cria diretórios em `output/<algorithm>` e `results/<algorithm>`.
		- Define variáveis globais com paths de arquivos de log.
		- Remove arquivos existentes com os mesmos nomes.

	Returns:
		None
	"""
	
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
	"""
	Registra o estado de recursos por passo da simulação.

	Cada linha salva possui o formato: `step,number,resource_per_cluster`.

	Args:
		step (int): Passo atual da simulação.
		number (int): Identificador/contador associado ao registro.
		resource_per_cluster (int | float): Recursos observados por cluster.
		resource (int): Configuração global de recurso para nome do arquivo.
		weight (int | float): Configuração de peso para nome do arquivo.
		radius (int | float): Configuração de raio para nome do arquivo.

	Returns:
		TextIOWrapper: Referência do arquivo (já fechado ao retornar).
	"""
	resources_file = open('output/resources_'+str(radius)+'_'+str(resource)+'_'+str(weight)+'.txt','a')
	resources_file.write(str(step) + "," + str(number) + "," + str(resource_per_cluster) + "\n")
	resources_file.close()

	return resources_file

def log_tasks(step, number, tasks, resource, weight, radius):
	"""
	Registra a quantidade de tarefas por passo da simulação.

	Cada linha salva possui o formato: `step,number,tasks`.

	Args:
		step (int): Passo atual da simulação.
		number (int): Identificador/contador associado ao registro.
		tasks (int): Quantidade de tarefas observada no passo.
		resource (int): Configuração global de recurso para nome do arquivo.
		weight (int | float): Configuração de peso para nome do arquivo.
		radius (int | float): Configuração de raio para nome do arquivo.

	Returns:
		TextIOWrapper: Referência do arquivo (já fechado ao retornar).
	"""
	tasks_file = open('output/tasks_'+str(radius)+'_'+str(resource)+'_'+str(weight)+'.txt','a')
	tasks_file.write(str(step) + "," + str(number) + "," + str(tasks) + "\n")
	tasks_file.close()

	return tasks_file

def log_allocation(step, n_tasks, total_cpu_time):
	"""
	Registra dados resumidos de alocação em arquivo de resultados principal.

	Args:
		step (int): Passo atual da simulação.
		n_tasks (int): Número de tarefas alocadas/processadas no passo.
		total_cpu_time (float): Tempo total de CPU consumido.

	Side Effects:
		- Escreve no arquivo global `name_alloc`.

	Returns:
		None
	"""

	total_cpu_time = round(total_cpu_time, 5)

	allocation_file = open(name_alloc,'a')
	allocation_file.write(
		str(step) + "\t" +
		str(n_tasks) + "\t" +
		str(total_cpu_time) + "\n"
		)
	allocation_file.close()

def log_time(resultado):
	"""
	Registra uma métrica temporal em arquivo de tempo.

	Args:
		resultado (int | float | str): Valor temporal a ser registrado.

	Side Effects:
		- Escreve no arquivo global `name_time`.

	Returns:
		None
	"""

	time_file = open(name_time,'a')
	time_file.write(str(resultado) + "\n")
	time_file.close()

def log_cost(resultado_price):
	"""
	Registra métrica de custo/preço em arquivo dedicado.

	Args:
		resultado_price (int | float | str): Valor de custo a ser registrado.

	Side Effects:
		- Escreve no arquivo global `name_queue`.

	Returns:
		None
	"""

	queue_file = open(name_queue,'a')
	queue_file.write(str(resultado_price) + "\n")
	queue_file.close()

def log_cluster(step, nuvens):
	"""
	Registra informação de um cluster específico no passo atual.

	Atualmente, a função fixa `nuvem_escolhida = 4` e registra o primeiro campo
	da estrutura correspondente em `nuvens[nuvem_escolhida][0]`.

	Args:
		step (int): Passo atual da simulação.
		nuvens (list | dict): Estrutura com dados dos clusters/nuvens.

	Side Effects:
		- Escreve no arquivo global `name_cluster`.

	Returns:
		None
	"""
	nuvem_escolhida = 4
	cluster_file = open(name_cluster, 'a')
	cluster_file.write(str(step) + '\t' + str(nuvens[nuvem_escolhida][0]) + '\n')
	cluster_file.close()

def log_fila(step, fila):
	"""
	Registra o tamanho da fila de tarefas no passo atual.

	Args:
		step (int): Passo atual da simulação.
		fila (list | dict | set): Estrutura que representa a fila de tarefas.

	Side Effects:
		- Escreve no arquivo global `name_fila`.

	Returns:
		None
	"""
	fila_file = open(name_fila, 'a')
	fila_file.write(str(step) + '\t' + str(len(fila)) + '\n')
	fila_file.close()

def log_results(resultados):
	"""
	Consolida e registra estatísticas gerais de uma execução.

	A função calcula, a partir do dicionário `resultados`, métricas como:
	percentual escalonado, média/desvio de delay e média/desvio de tempo em fila.
	Também imprime um resumo no terminal e grava uma linha consolidada em
	`name_alloc`.

	Args:
		resultados (dict): Dicionário com tarefas e seus metadados de execução.

	Side Effects:
		- Imprime estatísticas no console.
		- Escreve uma linha de consolidação em `name_alloc`.

	Returns:
		None
	"""
	
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
	"""
	Gera logs detalhados e consolidados finais de processamento.

	Etapas realizadas:
		1. Salva, em `name_alloc`, os dados completos de cada tarefa.
		2. Calcula métricas consolidadas (percentual concluído, delay médio,
		   tempo médio de fila e custo médio).
		3. Exibe resumo no terminal.
		4. Salva consolidação final em `result_name`.

	Args:
		results (dict): Dicionário com resultados finais por tarefa.

	Side Effects:
		- Escreve log detalhado em `name_alloc`.
		- Imprime métricas no console.
		- Escreve consolidação em `result_name`.

	Returns:
		None
	"""

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
	"""
	Salva relatório de balanceamento de carga por estação base/cluster.

	O arquivo gerado contém uma linha com o total agregado e, em seguida,
	uma linha por identificador presente em `results`.

	Args:
		results (dict): Mapeamento `{id: valor_de_carga}`.

	Side Effects:
		- Escreve relatório no arquivo global `balance_name`.

	Returns:
		None
	"""
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