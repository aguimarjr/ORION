#!/usr/bin/env python
# title: cloud_manager.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 18.06.2023

import os
import traci

from scipy.spatial import distance

import utils.constants as CONSTANTS

EXPERIMENTS 		= CONSTANTS.EXPERIMENTS
BS_POSITION_FILE	= CONSTANTS.BS_POSITION_FILE
BS_FILE				= CONSTANTS.BS_FILE
BS_CPU 				= CONSTANTS.BS_CPU
BS_MEMORY			= CONSTANTS.BS_MEMORY
PREDICTION_WINDOW 	= CONSTANTS.PREDICTION_WINDOW

'''
For data collection and creation of vehicular mobility dataset
'''
if CONSTANTS.CREATE_DATASET == True:
	dir_name = CONSTANTS.DATASET_FILE
	if not os.path.isdir(dir_name):
		os.makedirs(dir_name)
	else:
		os.system('rm ' + dir_name + '*.txt')



class Clouds():
	"""
	Classe responsável por gerenciar nuvens veiculares associadas às estações-base (BSs).

	A classe mantém o estado dos recursos computacionais de cada nuvem (CPU veicular,
	CPU da BS e MIPS total), executa atualização de recursos durante alocação/conclusão
	de tarefas, forma nuvens veiculares a partir da mobilidade observada e também permite
	construção baseada em dataset com janela de predição.

	Principais responsabilidades:
		- Carregar posições das BSs.
		- Criar e atualizar nuvens veiculares.
		- Atualizar capacidade disponível após uso de recursos.
		- Associar veículos às BSs por proximidade (clustering por raio).
		- Gerar dataset de mobilidade por BS.

	Atributos:
		- clouds (dict): Estrutura principal com dados de cada nuvem por ID de BS.
		- basestations (dict): Mapeamento das posições (x, y) de cada estação-base.
		- probabilities (dict): Probabilidades associadas a cada nuvem/BS.
	"""

	def __init__(self):
		"""
		Inicializa a estrutura de gerenciamento das nuvens.

		Side Effects:
			- Cria dicionário vazio para nuvens (`clouds`).
			- Carrega posições das BSs por meio de `get_bs_positions()`.
			- Cria dicionário de probabilidades (`probabilities`).
		"""
		self.clouds = {}
		self.basestations = self.get_bs_positions()
		self.probabilities = {}

	def add(self, cloud_id, members, v_cpu, v_memory, bs_cpu, bs_memory, mips_future):
		"""
		Adiciona uma nova nuvem veicular na estrutura interna.

		Args:
			cloud_id (int): Identificador da nuvem (normalmente ID da BS).
			members (int): Quantidade de veículos membros da nuvem.
			v_cpu (int | float): CPU disponível no conjunto veicular.
			v_memory (int | float): Memória veicular disponível (mantida para compatibilidade).
			bs_cpu (int | float): CPU disponível na estação-base.
			bs_memory (int | float): Memória da estação-base (mantida para compatibilidade).
			mips_future (list): Vetor de previsão de recursos/MIPS para janelas futuras.

		Side Effects:
			- Cria/atualiza entrada em `self.clouds[cloud_id]`.
			- Inicializa probabilidade fixa da nuvem em `self.probabilities`.
		"""

		self.id					= cloud_id
		self.members			= members
		self.v_cpu 				= v_cpu
		self.v_memory			= v_memory
		self.bs_cpu 			= bs_cpu
		self.bs_memory			= bs_memory
		self.mips				= self.v_cpu + self.bs_cpu
		self.prediction			= mips_future # FOR PREDICTION
		self.clouds[self.id] 	= {
			'members':self.members,
			'vehicle_cpu':self.v_cpu,
			# 'vehicle_memory':self.v_memory,
			'bs_cpu':self.bs_cpu,
			# 'bs_memory':self.bs_memory,
			'mips':self.mips,
			'prediction':self.prediction
		}

		# TODO: update the number of BSs (1/|BS|)
		self.probabilities[self.id] = (1/14)

	def vc_update(self, cloud_id, members, v_cpu, v_memory, bs_cpu, bs_memory, mips_future):
		"""
		Atualiza os dados de uma nuvem veicular já existente.

		Args:
			cloud_id (int): Identificador da nuvem (ID da BS).
			members (int): Quantidade atual de veículos na nuvem.
			v_cpu (int | float): CPU veicular disponível após atualização.
			v_memory (int | float): Memória veicular (não persistida atualmente).
			bs_cpu (int | float): CPU disponível da BS após atualização.
			bs_memory (int | float): Memória da BS (não persistida atualmente).
			mips_future (list): Vetor de previsão de recursos/MIPS futuros.

		Side Effects:
			- Atualiza campos de `self.clouds[cloud_id]` in-place.
		"""
		
		self.id					= cloud_id
		self.members			= members
		self.v_cpu 				= v_cpu
		self.v_memory			= v_memory
		self.bs_cpu 			= bs_cpu
		self.bs_memory			= bs_memory
		self.mips				= self.v_cpu + self.bs_cpu
		self.prediction			= mips_future # FOR PREDICTION

		self.clouds[self.id].update({'members':self.members})
		self.clouds[self.id].update({'vehicle_cpu':self.v_cpu})
		# self.clouds[cloud_id].update({'v_memory':v_memory})
		self.clouds[self.id].update({'bs_cpu':self.bs_cpu})
		# self.clouds[cloud_id].update({'bs_memory':bs_memory})
		self.clouds[self.id].update({'mips':self.mips})
		self.clouds[self.id].update({'prediction':self.prediction})

	def update(self, cloud_id, usage, update_type):
		"""
		Atualiza recursos disponíveis de uma nuvem após eventos de execução de tarefas.

		Args:
			cloud_id (int): Identificador da nuvem a ser atualizada.
			usage (dict): Estrutura com consumo/liberação de recursos.
				- Para `update_type == 'add'`: esperado dicionário de tarefas,
				  cada uma contendo chaves `vehicle` e `bs`.
				- Para `update_type == 'complete'`: esperado dicionário único
				  com chaves `vehicle` e `bs`.
			update_type (str): Tipo de atualização ('add' ou 'complete').

		Side Effects:
			- Modifica `vehicle_cpu`, `bs_cpu` e `mips` em `self.clouds[cloud_id]`.
			- Em caso de tipo inválido, imprime "INVALID!".
		"""
		
		self.cloud_id = cloud_id
		self.cpu_usage = 0
		self.usage = usage

		if update_type == 'add':
			for i in self.usage:
				self.cpu_usage += (self.usage[i]['vehicle'] + self.usage[i]['bs'])
				self.clouds[self.cloud_id]['vehicle_cpu'] -= self.usage[i]['vehicle']
				self.clouds[self.cloud_id]['bs_cpu'] -= self.usage[i]['bs']
			
			self.clouds[self.cloud_id]['mips'] -= self.cpu_usage

		elif update_type == 'complete':
			self.cpu_usage += (self.usage['vehicle'] + self.usage['bs'])
			self.clouds[self.cloud_id]['vehicle_cpu'] += self.usage['vehicle']
			self.clouds[self.cloud_id]['bs_cpu'] += self.usage['bs']
			self.clouds[self.cloud_id]['mips'] += self.cpu_usage

		else:
			print("INVALID!")		

	def get_clouds(self):
		"""
		Retorna a estrutura de nuvens gerenciadas.

		Returns:
			dict: Dicionário com estado atual das nuvens.
		"""
		pass

	def run_mobility_prediction(self):
		"""
		Executa rotina de predição de mobilidade (método reservado).

		Notes:
			- Método ainda não implementado.
		"""
		pass

	def build_vehicular_clouds(self, step, resources, schedule):
		"""
		Constrói/atualiza nuvens veiculares com base em dataset de mobilidade e predição.

		A função lê os dados por BS, calcula a janela de predição a partir do `step`
		corrente e atualiza a capacidade disponível considerando recursos já alocados
		no agendador (`schedule.resource_usage`).

		Args:
			step (int): Passo de tempo atual da simulação.
			resources (int | float): Recurso computacional por veículo.
			schedule (object): Objeto de escalonamento contendo `resource_usage`.

		Side Effects:
			- Cria ou atualiza entradas em `self.clouds`.
			- Calcula e persiste previsões em `prediction` para cada BS.
		"""
		self.resources = resources

		prediction_window = [(x+step) for x in range(PREDICTION_WINDOW+1)]
		# [t, t+1, t+2, ..., t+PREDICTION_WINDOW]
		# {t:value_t, t+1:value_t+1, t+2:value_t+2, ..., t+PREDICTION_WINDOW: value_PREDICTION_WINDOW}
		bs_file = open(BS_POSITION_FILE,'r')
		# first time
		if len(self.clouds) == 0:
			for bs in bs_file:
				self.predictions = []
				bs = bs.split()
				id_bs = int(bs[0])

				# current value
				self.clouds[id_bs] = {}

				mobility_data = open(BS_FILE + str(id_bs) + '.txt', 'r')
				with mobility_data as f:
					lines = f.readlines()
				
				cont_control = 0
				for i in lines:
					if int(i.split()[0]) in prediction_window:
						self.predictions.append(int(i.split()[1]) * self.resources)
						cont_control += 1
						# break for loop to reduce computing time
						if cont_control == PREDICTION_WINDOW+1:
							break
				
				# example
				# predictions = [1, 2, 3, 4, 5, 6]
				# predictions[0] = 1
				self.members = self.predictions[0]
				self.v_cpu = self.members * self.resources

				# example
				# predictions[1:6] = [2, 3, 4, 5, 6]
				# resource_prediction = [(2+BS_CPU), (3+BS_CPU), (4+BS_CPU), (5+BS_CPU), (6+BS_CPU)]
				self.resource_prediction = [(mips + BS_CPU) for mips in self.predictions[1:PREDICTION_WINDOW+1]]
				self.add(id_bs, self.members, self.v_cpu, self.v_cpu, BS_CPU, BS_MEMORY, self.resource_prediction)
		else:

			# VERIFICA RECURSOS JA EM USO E CONSIDERA O VALOR NA ATUALIZACAO ATUAL

			self.discount = {}
			for current_proc in schedule.resource_usage:
				self.discount[current_proc] = {}
				self.discount[current_proc]['vehicle'] = 0
				self.discount[current_proc]['bs'] = 0
				if len(schedule.resource_usage[current_proc]) > 0:
					for each_task in schedule.resource_usage[current_proc]:
						self.discount[current_proc]['vehicle'] += schedule.resource_usage[current_proc][each_task]['vehicle']
						self.discount[current_proc]['bs'] += schedule.resource_usage[current_proc][each_task]['bs']
				# print(current_proc)

			# print("TOTAL DE DESCONTOS:")
			# print(self.discount)

			for bs in bs_file:
				self.predictions = []
				bs = bs.split()
				id_bs = int(bs[0])

				mobility_data = open(BS_FILE + str(id_bs) + '.txt', 'r')
				with mobility_data as f:
					lines = f.readlines()
				
				cont_control = 0
				for i in lines:
					if int(i.split()[0]) in prediction_window:
						self.predictions.append(int(i.split()[1]) * self.resources)
						cont_control += 1
						# break for loop to reduce computing time
						if cont_control == PREDICTION_WINDOW+1:
							break

				self.members = self.predictions[0]
				self.v_cpu = (self.members * self.resources) - (self.discount[id_bs]['vehicle'])
				self.bs_cpu = BS_CPU - self.discount[id_bs]['bs']
				# mips = v_cpu + BS_CPU
				self.resource_prediction = [(mips + BS_CPU) for mips in self.predictions[1:PREDICTION_WINDOW+1]]
				self.vc_update(id_bs, self.members, self.v_cpu, self.v_cpu, self.bs_cpu, BS_MEMORY, self.resource_prediction)

	def prepare_nodes(self, step, vehicles_list, radius, resources):
		"""
		Prepara nós veiculares e forma nuvens com base na posição atual dos veículos.

		A função coleta posições via TraCI, executa clustering por raio e depois cria/
		atualiza as nuvens veiculares com os recursos informados.

		Args:
			step (int): Passo de tempo atual da simulação.
			vehicles_list (list): Lista de IDs de veículos ativos no passo atual.
			radius (int | float): Raio máximo de cobertura para associação veículo-BS.
			resources (int | float): Recurso computacional por veículo.

		Side Effects:
			- Atualiza `self.vehicles` com coordenadas dos veículos.
			- Pode atualizar `self.clouds` via `create_vehicular_clouds`.
		"""
		
		# print("[DEBUG] >> FORMANDO NUVENS VEICULARES...")
		
		# MAPEAMENTO DOS VEICULOS ONLINE NO STEP ATUAL
		self.vehicles = {}
		for i in range(len(vehicles_list)):
			x = str(traci.vehicle.getPosition(vehicles_list[i])).split(",")
			x = str(x[0]).split("(")

			y = str(traci.vehicle.getPosition(vehicles_list[i])).split()
			y = str(y[1]).split(")")

			x = float(x[1])
			y = float(y[0])

			self.vehicles[vehicles_list[i]] 		= {}
			self.vehicles[vehicles_list[i]]['x'] 	= x
			self.vehicles[vehicles_list[i]]['y'] 	= y
			# vehicles.append([vehicles_list[i], x, y]) # vehicles_list[i]	

		# ASSOCIACAO DE VEICULOS NA BS -> SINR-BASED
		vehicular_clouds = self.run_clustering(radius, step)

		# FORMA NUVENS VEICULARES
		self.create_vehicular_clouds(vehicular_clouds, resources)

	def run_clustering(self, radius, step):
		"""
		Executa associação de veículos às BSs por menor distância dentro de um raio.

		O algoritmo primeiro identifica todas as BSs que cobrem cada veículo e, quando
		há múltipla cobertura, escolhe a BS mais próxima.

		Args:
			radius (int | float): Raio de cobertura para considerar um veículo atendido.
			step (int): Passo de tempo atual (usado para geração de dataset).

		Returns:
			dict: Mapeamento `id_bs -> [ids_veiculos]` com nuvens veiculares atuais.

		Side Effects:
			- Chama `create_dataset(step, actual_vehicular_clouds)`.
		"""
		# print("RAIO DE %d METROS!" % radius)
		# radius = 2000
		mapeamento = {}
		for i in self.basestations:
			veiculos_cobertos = []
			for j in self.vehicles:
				position = (self.vehicles[j]['x'],self.vehicles[j]['y'])
				distancia = distance.euclidean(position, (self.basestations[i]['x'], self.basestations[i]['y']))
				if distancia <= radius:
					dados = (j, distancia)
					veiculos_cobertos.append(dados)
			mapeamento[i] = veiculos_cobertos

		# print(mapeamento)
		controle = mapeamento.copy()
		unicos = {}

		for i in mapeamento:
			if len(mapeamento[i]) > 0:
				for j in mapeamento[i]:
					if j[0] not in unicos:
						unicos[j[0]] = (i, j[1])
					else:
						# print(j, "EM MAIS DE UMA BS")
						if j[1] < unicos[j[0]][1]:
							unicos[j[0]] = (i, j[1])

		# print(unicos)
		actual_vehicular_clouds = {}
		cont = 0
		for i in self.basestations:
			lista_temp = []
			for key,values in unicos.items():
				if i == values[0]:
					cont += 1
					lista_temp.append(key)
			actual_vehicular_clouds[i] = lista_temp

		# print("CRIACAO DE DATASET PARA CADA BS")
		self.create_dataset(step, actual_vehicular_clouds)
		return actual_vehicular_clouds

	def create_vehicular_clouds(self, vehicular_clouds, resources):
		"""
		Cria ou atualiza nuvens veiculares a partir do mapeamento BS-veículos.

		Args:
			vehicular_clouds (dict): Mapeamento `id_bs -> lista de veículos`.
			resources (int | float): Recurso computacional fornecido por veículo.

		Side Effects:
			- Se não houver nuvens, cria com `add`.
			- Caso contrário, atualiza com `vc_update`.
			- Atualiza previsão padrão (`self.prediction`) com janela fixa.
		"""
		
		cont_membros = 0
		if len(self.clouds) == 0:
			for i in vehicular_clouds:
				# print(i, vehicular_clouds[i])
				members = len(vehicular_clouds[i])
				v_cpu = members * resources

				# TODO: # MUDAR PARA DADOS DA PREDICAO
				mips = v_cpu + BS_CPU
				# PARA PREDICAO
				self.prediction = [mips] * PREDICTION_WINDOW
				# ADICIONA NA ESTRUTURA DE NUVENS
				self.add(i, members, v_cpu, v_cpu, BS_CPU, BS_MEMORY, self.prediction)
				cont_membros += members
			# print("TOTAL DE VEICULOS:",cont_membros)
		else:
			for i in vehicular_clouds:
				# print(i, vehicular_clouds[i])
				members = len(vehicular_clouds[i])
				v_cpu = members * resources

				mips = v_cpu + BS_CPU
				# PARA PREDICAO
				self.prediction = [mips] * PREDICTION_WINDOW
				# ADICIONA NA ESTRUTURA DE NUVENS
				self.vc_update(i, members, v_cpu, v_cpu, BS_CPU, BS_MEMORY, self.prediction)
				cont_membros += members
			# print("TOTAL DE VEICULOS:",cont_membros)

	def get_bs_positions(self):
		"""
		Carrega a posição das estações-base a partir do arquivo configurado.

		Returns:
			dict: Dicionário no formato `{id_bs: {'x': float, 'y': float}}`.

		Side Effects:
			- Atualiza `self.basestations`.
		"""

		# print("Pegando posicao das BSs...")
		
		self.basestations = {}

		self.bs_file = open(BS_POSITION_FILE,'r')
		for bs in self.bs_file:
			bs 								= bs.split()
			id_bs 							= int(bs[0])
			self.basestations[id_bs] 		= {}
			self.basestations[id_bs]['x'] 	= float(bs[1])
			self.basestations[id_bs]['y'] 	= float(bs[2])

		return self.basestations

	def create_dataset(self, step, vehicular_clouds):
		"""
		Registra em arquivo a quantidade de veículos por BS no passo atual.

		Args:
			step (int): Passo de tempo da simulação.
			vehicular_clouds (dict): Mapeamento `id_bs -> lista de veículos`.

		Side Effects:
			- Escreve/append em arquivos de dataset por BS em `CONSTANTS.DATASET_FILE`.
		"""

		for id_bs in vehicular_clouds:
			filename = open(CONSTANTS.DATASET_FILE + str(id_bs) + '.txt', 'a')
			resources = len(vehicular_clouds[id_bs])
			filename.write(str(int(step)) + '\t' + str(resources) + '\n')
			filename.close()
			# print(str(id_bs) + " > " + str(resources))
