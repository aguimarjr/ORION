#!/usr/bin/env python
# title: monitor.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 04.11.2021

import random
import logging

class SchedulingMonitor():
	"""
	Classe responsável por monitorar o estado das tarefas escalonadas durante a simulação.

	A classe atualiza filas de tarefas, identifica tarefas concluídas ou expiradas,
	libera recursos nas nuvens veiculares correspondentes e calcula o custo monetário
	de execução com base no uso de recursos.

	Métodos:
		- get_status(step, schedule, task, cloud, queue, step_lenght): Atualiza o estado
		  das tarefas no instante atual da simulação.
		- check_vehicular_cloud(cloud, queue): Método auxiliar para verificação de
		  recursos em nuvens veiculares.
		- resource_price(uso_recursos): Calcula o custo de processamento conforme os
		  recursos utilizados.

	Atributos:
		- current_time (float | int): Tempo atual considerado no ciclo de monitoramento.
		- remove_now (list): Lista temporária com pares [cloud_id, task_id] de tarefas
		  que devem ser removidas da estrutura de escalonamento.
	"""

	def get_status(self, step, schedule, task, cloud, queue, step_lenght):
		"""
		Atualiza o estado das tarefas no tempo atual da simulação.

		O método executa as seguintes etapas:
			1. Atualiza a fila de tarefas para o instante `step`.
			2. Percorre as tarefas escalonadas em cada nuvem veicular.
			3. Verifica se tarefas já alcançaram seu `finish_time`.
			4. Para tarefas `SUBMITTED`, marca como `COMPLETED`, define `remove_time`,
			   remove da fila ativa, calcula custo e libera recursos.
			5. Para tarefas `EXPIRED`, calcula custo e libera recursos.
			6. Remove tarefas concluídas/expiradas da estrutura `schedule.escalonamento`.

		Args:
			step (int | float): Instante atual da simulação.
			schedule (object): Estrutura de escalonamento contendo mapeamento de tarefas
				por nuvem e controle de uso de recursos.
			task (object): Referência para o gerenciador de tarefas (não utilizado
				diretamente neste método).
			cloud (object): Componente responsável por atualizar o estado dos recursos
				da nuvem veicular.
			queue (object): Estrutura de filas e controle de estado das tarefas.
			step_lenght (int | float): Duração do passo da simulação.

		Side Effects:
			- Atualiza `self.current_time` e `self.remove_now`.
			- Modifica `queue.task_queue_control` e `queue.final_queue`.
			- Remove itens de `queue.task_queue`.
			- Atualiza recursos via `cloud.update(...)`.
			- Remove entradas em `schedule.resource_usage` e `schedule.escalonamento`.
			- Registra mensagens de debug no logger.
		"""

		self.current_time = step

		# UPDATE TASK QUEUE
		queue.update(step, schedule, step_lenght)

		self.remove_now = []
			
		for cloud_i, tasks_j in schedule.escalonamento.items():
			
			for item in tasks_j:

				if float(self.current_time) >= float(queue.task_queue_control[item]['finish_time']):
					
					if queue.task_queue_control[item]['status'] == 'SUBMITTED':
						# print(item + " concluiu seu processamento!")
						logging.debug("%s concluiu seu processamento!" % item)

						# task_remove_time = float(self.current_time) + round(random.random(), 4)
						task_remove_time = round(queue.task_queue_control[item]['finish_time'] + random.uniform(0.1, 0.5), 4)
						queue.task_queue_control[item]['remove_time'] = task_remove_time
						queue.task_queue_control[item]['status'] = 'COMPLETED'
						queue.final_queue[item]['remove_time'] = task_remove_time
						queue.final_queue[item]['status'] = 'COMPLETED'
						
						# remove task queued
						queue.task_queue.remove(item)

						# READICIONA RECURSO NA VC CORRESPONDENTE
						task_info_resource = schedule.resource_usage[cloud_i][item]
						# print(task_info_resource)

						# compute cost
						local_cost = self.resource_price(task_info_resource)
						queue.final_queue[item]['cost'] = local_cost

						cloud.update(cloud_i, task_info_resource, 'complete')
						del schedule.resource_usage[cloud_i][item]
						self.remove_now.append([cloud_i, item])
				
					elif queue.task_queue_control[item]['status'] == 'EXPIRED':

						task_info_resource = schedule.resource_usage[cloud_i][item]
						
						# compute cost
						local_cost = self.resource_price(task_info_resource)
						queue.final_queue[item]['cost'] = local_cost
						
						cloud.update(cloud_i, task_info_resource, 'complete')
						del schedule.resource_usage[cloud_i][item]
						self.remove_now.append([cloud_i, item])

		# REMOVE TAREFAS CONCLUIDAS DA ESTRUTURA DE ESCALONAMENTO
		for remove_id in self.remove_now:
			del schedule.escalonamento[remove_id[0]][remove_id[1]]

	def check_vehicular_cloud(self, cloud, queue):
		"""
		Verifica recursos disponíveis em cada nuvem veicular.

		Atualmente este método está implementado como placeholder e retorna 0.

		Args:
			cloud (object): Estrutura contendo o estado das nuvens veiculares.
			queue (object): Estrutura de filas de tarefas em processamento/espera.

		Returns:
			int: Valor fixo `0` indicando ausência de lógica implementada.
		"""
		return 0

	def resource_price(self, uso_recursos):
		"""
		Define o custo monetário com base nos recursos consumidos pela tarefa.

		O cálculo considera preços unitários para recursos de veículos e estação
		base (BS), multiplicados pelo tempo de processamento e pela quantidade de
		recursos utilizada.

		Args:
			uso_recursos (dict): Dicionário com informações de uso de recursos,
				esperando as chaves:
				- 'processing_time' (float): Tempo de processamento da tarefa.
				- 'vehicle' (int | float): Quantidade de recurso de veículo utilizada.
				- 'bs' (int | float): Quantidade de recurso de estação base utilizada.

		Returns:
			float: Custo total arredondado para 3 casas decimais.

		Side Effects:
			- Nenhum. O método apenas realiza o cálculo e retorna o valor.
		"""
		# print(uso_recursos)
		total_price = 0
		time_using = uso_recursos['processing_time']
		
		vehicle_price = 5.17296 # c8a.metal-24xl
		bs_price = 10.34592 # c8a.48xlarge

		vehicle_total_cost = (vehicle_price * uso_recursos['vehicle']) * time_using
		bs_total_cost = (bs_price * uso_recursos['bs']) * time_using

		total_price = round(vehicle_total_cost + bs_total_cost, 3)

		return total_price
