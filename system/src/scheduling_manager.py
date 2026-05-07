#!/usr/bin/python3
# title: scheduling_manager.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 22.10.2021

# general
import log_manager as log
import time
import numpy as np

import logging

from cloud_manager import Clouds

# algorithms
from scheduler import FCFS
from scheduler import MAB
from scheduler import TEMIS
from scheduler import ORION
from scheduler import NSGA3
from scheduler import PSO
from scheduler import LOA



class SchedulingManager:
	"""
	Classe responsável pelo gerenciamento do escalonamento de tarefas nas nuvens.

	A classe `SchedulingManager` executa algoritmos de escalonamento, registra tempos
	de execução, atualiza o estado das tarefas nas filas de controle/final e mantém
	informações de balanceamento de carga e uso de recursos por nuvem/BS.

	Métodos:
		- __init__(clouds): Inicializa as estruturas internas de escalonamento e métricas.
		- insert(tasks, queue, clouds, algorithm, step): Executa o algoritmo selecionado e
		  aplica as atualizações de estado e recursos.
		- update_vc_resources(): Método reservado para atualização de recursos da VC.
		- get_scheduling(): Exibe o estado atual do escalonamento registrado.

	Atributos:
		- clouds (Clouds): Referência para o gerenciador de nuvens.
		- escalonamento (dict): Estrutura com tarefas escalonadas por nuvem.
		- bs_list (dict): Lista de BSs/nuvens conhecidas pelo sistema.
		- load_balance (dict): Contador de tarefas/alocações por nuvem.
		- resource_usage (dict): Registro acumulado de uso de recursos por nuvem.
	"""

	def __init__(self, clouds: Clouds):
		"""
		Inicializa o gerenciador de escalonamento e suas estruturas de controle.

		Para cada base station/nuvem disponível em `clouds.basestations`, cria entradas
		de controle para lista de BSs, balanceamento de carga e uso de recursos.

		Args:
			clouds (Clouds): Objeto com a topologia/estado das nuvens e BSs.

		Side Effects:
			- Inicializa os dicionários `escalonamento`, `bs_list`, `load_balance`
			  e `resource_usage`.
		"""
		self.clouds = clouds

		self.escalonamento = {}
		self.bs_list = {}
		self.load_balance = {}
		self.resource_usage = {}

		for id_bs in self.clouds.basestations:
			# popula a lista de BSs com o id da BS e um dicionário vazio para armazenar as tarefas escalonadas naquela BS
			self.bs_list[id_bs] = ''
			# popula a lista de balanceamento de carga com o id da BS e o valor 0 para indicar que nenhuma tarefa foi escalonada naquela BS
			self.load_balance[id_bs] = 0
			# popula a lista de uso de recursos com o id da BS e um dicionário vazio para armazenar as tarefas escalonadas naquela BS
			self.resource_usage[id_bs] = {}

	def insert(self, tasks, queue, clouds, algorithm, step):
		"""
		Executa o escalonamento de tarefas e atualiza métricas/estado do sistema.

		Seleciona o algoritmo informado, processa a fila de tarefas, registra o tempo
		de CPU gasto no escalonador e atualiza:
		- uso de recursos por nuvem;
		- balanceamento de carga;
		- tempos de início/fim de cada tarefa;
		- status das tarefas para `SUBMITTED`;
		- estrutura interna de escalonamento.

		Args:
			tasks: Estrutura de tarefas utilizada pelos algoritmos de escalonamento.
			queue: Fila contendo `task_queue_control` e `final_queue` para atualização.
			clouds: Instância de nuvens para execução de `update` de recursos.
			algorithm (str): Nome do algoritmo (FCFS, MAB, ORION, NSGA3, PSO, LOA, TEMIS).
			step (int | float): Instante atual da simulação para cálculo de tempos.

		Raises:
			Exception: Quando o nome do algoritmo é inválido.

		Side Effects:
			- Escreve logs de tempo de CPU via `log.log_time`.
			- Atualiza `queue.task_queue_control` e `queue.final_queue`.
			- Atualiza `self.escalonamento`, `self.resource_usage` e `self.load_balance`.
			- Chama `clouds.update(cloud, resource_usage, 'add')` para cada nuvem processada.
		"""
		self.result = {}
		self.resource_now = {}

		# RETORNA NUVEM COM TAREFAS ESCALONADAS E SEUS TEMPOS DE PROCESSAMENTO
		# RETORNA UTILIZACAO DOS RECURSOS NA NUVEM

		# initial time
		self.initial_time = time.process_time()
			
		if algorithm == 'FCFS':
			self.result, self.resource_now = FCFS.run(queue, clouds, tasks)

		elif algorithm == 'MAB':
			self.result, self.resource_now = MAB.run(queue, clouds, tasks)

		elif algorithm == 'ORION':
			self.result, self.resource_now = ORION.run(queue, clouds, tasks)

		elif algorithm == 'NSGA3':
			self.result, self.resource_now = NSGA3.run(queue, clouds, tasks)

		elif algorithm == 'PSO':
			self.result, self.resource_now = PSO.run(queue, clouds, tasks)

		elif algorithm == 'LOA':
			self.result, self.resource_now = LOA.run(queue, clouds, tasks)

		elif algorithm == 'TEMIS':
			self.result, self.resource_now = TEMIS.run(queue, clouds, tasks)

		else:
			raise Exception("[SCHEDULING MANAGER]: Scheduling algorithm INVALID!")
		
		# end time
		self.final_time = time.process_time()
		
		# cpu time
		log.log_time(float(self.final_time - self.initial_time))

		# TODO: 
		# - Verificar cada nuvem contida no self.result
		# - Verificar cada tarefa que foi adicionada na nuvem anterior
		# - Atualiza recursos na VC com base na utilização atual [OK, porém falta adicionar ao monitor]
		for id_cloud in self.resource_now:
			self.resource_usage[id_cloud].update(self.resource_now[id_cloud])
			self.load_balance[id_cloud] += 1

		for cloud in self.result:
			
			cloud_cpu_load = 0

			for task in self.result[cloud]:
				
				# print(" > Iniciando processamento da tarefa %s!" % task)
				logging.debug(" > Iniciando processamento da tarefa %s!" % task)

				self.task_id 											= task
				self.task_size											= queue.task_queue_control[self.task_id]['size']
				self.task_value											= queue.task_queue_control[self.task_id]['value']
				self.task_cpu 											= queue.task_queue_control[self.task_id]['cpu']
				self.task_deadline 										= queue.task_queue_control[self.task_id]['deadline']
				
				# print(" * size: ",self.task_size)
				logging.debug(" * size: %s", self.task_size)
				# print(" * deadline: ",self.task_deadline)
				logging.debug(" * deadline: %s", self.task_deadline)

				# ADICIONA TEMPO DE INICIO DO PROCESSAMENTO
				self.task_start_time 									= float(step) # time.time()
				queue.task_queue_control[self.task_id]['start_time'] 	= round(self.task_start_time,1)
				queue.final_queue[self.task_id]['start_time']			= round(self.task_start_time,1)

				# ADICIONA TEMPO ESTIMATIDO PARA CONCLUSAO DO PROCESSAMENTO
				self.task_finish_time									= step + self.result[cloud][self.task_id]
				queue.task_queue_control[self.task_id]['finish_time']	= round(self.task_finish_time,1)
				queue.final_queue[self.task_id]['finish_time']			= round(self.task_finish_time,1)

				# print(" * finish_time: ",self.task_finish_time)
				logging.debug(" * finish_time: %s", self.task_finish_time)
				
				# ATUALIZA STATUS
				self.task_status										= 'SUBMITTED'
				queue.task_queue_control[self.task_id]['status']	 	= self.task_status
				queue.final_queue[self.task_id]['status']				= self.task_status

				if cloud not in self.escalonamento:
					self.escalonamento[cloud] = {
						self.task_id:{
							'size':self.task_size,
							'value':self.task_value,
							'deadline':self.task_deadline,
							# 'insert_time':self.task_insert_time,
							'start_time':self.task_start_time,
							'finish_time':self.task_finish_time,
							'status':self.task_status
						}
					}
				else:
					self.escalonamento[cloud].update(
						{
							self.task_id:{
								'size':self.task_size,
								'value':self.task_value,
								'deadline':self.task_deadline,
								# 'insert_time':self.task_insert_time,
								'start_time':self.task_start_time,
								'finish_time':self.task_finish_time,
								'status':self.task_status
							}
						}
					)

				cloud_cpu_load += self.task_size

			# ATUALIZA INFORMACOES DA NUVEM
			clouds.update(cloud, self.resource_usage[cloud], 'add')

	def update_vc_resources(self):
		"""
		Método placeholder para atualização de recursos da VC.

		Returns:
			int: Retorna 0, indicando que a funcionalidade ainda não foi implementada.
		"""
		return 0

	def get_scheduling(self):
		"""
		Exibe no console o dicionário com o estado atual do escalonamento.

		Side Effects:
			- Imprime o conteúdo de `self.escalonamento`.
		"""
		# retorna o status de execucao das tarefas
		print(" * ",self.escalonamento)
