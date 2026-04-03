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

	def __init__(self):
		self.clouds = {}
		self.basestations = self.get_bs_positions()
		self.probabilities = {}

	def add(self, cloud_id, members, v_cpu, v_memory, bs_cpu, bs_memory, mips_future):

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
		pass

	def run_mobility_prediction(self):
		pass

	def build_vehicular_clouds(self, step, resources, schedule):
		'''
		Build vehicular clouds base on dataset.
		'''
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

		for id_bs in vehicular_clouds:
			filename = open(CONSTANTS.DATASET_FILE + str(id_bs) + '.txt', 'a')
			resources = len(vehicular_clouds[id_bs])
			filename.write(str(int(step)) + '\t' + str(resources) + '\n')
			filename.close()
			# print(str(id_bs) + " > " + str(resources))
