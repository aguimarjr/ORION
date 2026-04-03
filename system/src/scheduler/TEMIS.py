#!/usr/bin/python3
# title: TEMIS.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 21.12.2023

import utils.general_management as management

from .include import PARETO as PARETOSET
from .include import BCP_PARETO as bincovering
import numpy as np
import threading
import random

# CONSTANT
K = 14
NUM_THREADS = K

def run(queue, clouds, tasks):
	
	# print("[DEBUG] Running TEMIS...")

	result = {}
	resource_splited = {}

	local_tasks = {}
	tasks_pareto = {}
	local_tasks_deadline = {}

	# print("Separar em",K,"partes.")

	temp_set = []
	for item in queue.get_queue():
		# item = [task_id]
		if queue.task_queue_control[item]['status'] == 'PENDING':
			local_tasks[item] = queue.task_queue_control[item]['size']
			local_tasks_deadline[item] = queue.task_queue_control[item]['deadline']
			tasks_pareto[item] = [queue.task_queue_control[item]['cpu'], queue.task_queue_control[item]['size'], queue.task_queue_control[item]['deadline']]
			temp_set.append(item)

	# print("Tasks:")
	tasks_k = split_list(temp_set, K)
	# print(tasks_k)

	# organiza lista de VCs
	local_clouds = {}
	for i in clouds.clouds:
		local_clouds[i] = clouds.clouds[i]['mips']

	sorted_clouds = sorted(clouds.probabilities, key=lambda x: clouds.probabilities[x], reverse=True)
	
	# print("Lista de nuvens:")
	# print(sorted_clouds)
	clouds_k = split_list(sorted_clouds, K)
	# print(clouds_k)
	
	threads = []

	# Cria e inicia as threads
	for t in range(NUM_THREADS):
		parte_task = tasks_k[t]
		parte_cloud = clouds_k[t]
		# cria thread apenas se existir elementos na lista
		if len(parte_task) > 0:
			thread = MinhaThread(parte_cloud, parte_task, tasks, clouds, queue, t)
			thread.start()
			threads.append(thread)

	# Espera todas as threads terminarem
	for thread in threads:
		thread.join()

	# print("Resultados")
	for thread in threads:
		# print(thread.result)
		# print(thread.resource_splited)
		result.update(thread.result)
		resource_splited.update(thread.resource_splited)

	# # NEW -> TEST
	# result, resource_splited = process_tasks(sorted_clouds, local_clouds, local_tasks, tasks_pareto, local_tasks_deadline, tasks, clouds)

	# print("RESULT E RESOURCE_SPLITED:")
	# print(result)
	# print(resource_splited)

	# return
	return result, resource_splited


def process_tasks(sorted_clouds, tasks_k, tasks, clouds, queue, index):
	
	# print(f"Index: {index}")
	# print("Tasks",tasks_k)
	# print("Cloud:",sorted_clouds)

	local_tasks = {}
	tasks_pareto = {}
	local_tasks_deadline = {}

	# Cria estruturas internas
	for item in queue.get_queue():
		# item = [task_id]
		if item in tasks_k:
			if queue.task_queue_control[item]['status'] == 'PENDING':
				local_tasks[item] = queue.task_queue_control[item]['size']
				local_tasks_deadline[item] = queue.task_queue_control[item]['deadline']
				tasks_pareto[item] = [queue.task_queue_control[item]['cpu'], queue.task_queue_control[item]['size'], queue.task_queue_control[item]['deadline']]

	result = {}
	resource_splited = {}

	local_clouds = {}
	for i in sorted_clouds:
		# print("LOL",i)
		local_clouds[i] = clouds.clouds[i]['mips']
	
	for cloud in range(len(sorted_clouds)):
		
		if len(local_tasks) > 0:

			# PEGA DICIONARIO DE NUVENS
			items = sorted_clouds
			atualiza_valor = 0
			probabilities = []
			for index_cloud in clouds.probabilities:
				if index_cloud in sorted_clouds:
					probabilities.append(clouds.probabilities[index_cloud])
			# SELECIONA NUVEM COM BASE NA PROBABILIDADE
			id_nuvem, atualiza_valor = select_item_with_rejection(items, probabilities)
			clouds.probabilities[id_nuvem] = atualiza_valor
			# id_nuvem = sorted_clouds[cloud]
			result[id_nuvem] = {}

			# print("Nuvem:",id_nuvem)

			cloud_capacity = sorted_clouds[cloud]
			local_result = {}

			min_task_size = min(local_tasks, key=local_tasks.get)
			if local_tasks[min_task_size] > local_clouds[id_nuvem]:
				# print("NUVEM SEM RECURSOS!")
				break
			
			# EXECUTA ABORDAGEM DE ESCALONAMENTO AQUI
			# PARETO
			# while cloud_capacity > 0:

			# EXECUTA PARETO
			temporary_result = PARETOSET.run_pareto_set(tasks_pareto, cloud_capacity)

			# print("CANDIDATAS:")
			# print(temporary_result)

			local_pareto_to_bcp = {}
			local_pareto_deadline = {}
			for item_pareto in temporary_result:
				local_pareto_to_bcp[item_pareto] = local_tasks[item_pareto]
				local_pareto_deadline[item_pareto] = local_tasks_deadline[item_pareto]

			# print("PARETO TO BCP")
			# print(local_pareto_to_bcp)
			
			# EXECUTA BCP
			local_result = bincovering.first_fit_decreasing_algorithm(local_pareto_to_bcp, local_tasks_deadline, local_clouds[id_nuvem])
				
			if len(local_result) > 0:

				# print("LOCAL RESULT")
				# print(local_result)

				# GUARDA DEADLINE DAS CANDIDATAS
				deadlines = {}
				for task in local_result:
					deadlines[task] = local_pareto_deadline[task]
				sorted_deadlines = sorted(list(deadlines.keys()), key=lambda x: deadlines[x], reverse=True)

				to_remove_based_on_deadline = {}
				# VERIFICA RECURSOS PARA CADA t \in T DA JANELA DE PREDICAO
				# print("MINHA CLOUD:",clouds.clouds[id_nuvem]['prediction'])
				for cloud_t in clouds.clouds[id_nuvem]['prediction']:
					items = [local_tasks[x] if x in local_tasks else 0 for x in local_result]
					sum_tasks = sum(items)
					# print("SOMA:",sum_tasks)
					value = abs(cloud_t - sum_tasks)
					# SE DIFERENCA DE RECURSOS FOR MAIOR QUE ZERO
					if value > 0:
						# SE SOMA DE TAREFAS FOR MAIOR QUE CAPACIDADE ATUAL
						# REMOVE A TAREFA COM MAIOR DEADLINE, OU SEJA, PODE ESPERAR MAIS
						if sum_tasks > cloud_t:
							maximo = sorted_deadlines[0]
							# print("MAXIMO ATUAL:",maximo)
							del local_result[maximo]
							sorted_deadlines.remove(maximo)

				# VERIFICA PROCESSAMENTO E ADICIONA ESTIMATIVA NA TAREFA
				processing = management.get_processing_time(local_clouds[id_nuvem], tasks, local_result)
				for task in processing:
					local_result[task] = processing[task]

				# MAPEAMENTO DE USO DOS RECURSOS
				resource_splited[id_nuvem] = management.split_resource(local_result, clouds.clouds[id_nuvem], local_tasks)

				# REMOVE TAREFAS ESCALONADAS E VERIFICADAS
				for i in local_result:
					del local_tasks[i]
					del tasks_pareto[i]

				result[id_nuvem] = local_result

			else:
				# SEM RESULTADO
				pass
		else:
			# TODAS TAREFAS ESCALONADAS
			break
	
	# print(" ** ",result)
	return result, resource_splited

def split_list(task_list, k):
    """"Retorna lista de k listas."""
    lists = []
    new_lists = np.array_split(task_list, k)
    for item in new_lists:
        lists.append(list(item))
    return lists

def processar_lista(tasks_k, clouds_k, index):
	
	result = {index}
	resource_splited = {index}

	# print(f"Thread {index} tratando tasks {tasks_k} nas VCs {clouds_k}!")
	return result, resource_splited

# Classe para encapsular a execução da thread
class MinhaThread(threading.Thread):
    def __init__(self, clouds_k, tasks_k, tasks, clouds, queue, index):
        
        # print(f"Iniciou thread {index}")
        threading.Thread.__init__(self)
        self.index = index
        self.sorted_clouds = clouds_k
        self.tasks_pareto = tasks_k
        self.tasks = tasks
        self.clouds = clouds
        self.queue = queue
        self.result = None
        self.resource_splited = None
        self.lock = threading.Lock()  # Lock para sincronização

    def run(self):
        # Chama a função e armazena o resultado
        result, resource_splited = process_tasks(self.sorted_clouds, self.tasks_pareto, self.tasks, self.clouds, self.queue, self.index)

        # Atualiza o resultado protegendo com o lock
        with self.lock:
            self.result = result
            self.resource_splited = resource_splited
            # print(f"Resultado da Thread {self.index} é: {self.resultado}")

def select_item_with_rejection(items, probabilities):
	selected_item = None
	value = None

	# print("OPCOES:",probabilities)

	while selected_item is None:
		# Escolhe um item aleatoriamente com base nas probabilidades
		selected_item = random.choices(items, probabilities)[0]

		# print("SELECIONADO", selected_item)

		# Verifica se o item já foi selecionado anteriormente
		if selected_item in items:
			# Calcula a nova probabilidade de seleção
			item_index = items.index(selected_item)
			probabilities[item_index] *= 0.5  # Pode ajustar o fator de redução conforme necessário
			value = probabilities[item_index]
			
			# Verifica se a probabilidade é maior que zero
			if probabilities[item_index] <= 0:
				probabilities[item_index] = 0.0001  # Define um valor mínimo para evitar zero absoluto
				selected_item = None  # Reinicia o processo de seleção
				value = probabilities[item_index]

	# print(selected_item, value)
	return selected_item, value