# -*- coding: utf-8 -*-
#!/usr/bin/env python
# title: main.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 02.03.2021

"""Módulo principal de execução da simulação ORION.

Este arquivo orquestra a execução completa do sistema, incluindo:

- inicialização de componentes de fila, tarefas, nuvens e escalonamento;
- configuração e inicialização da simulação SUMO via TraCI;
- criação de nuvens veiculares e inserção/escalonamento de tarefas;
- monitoramento do estado do sistema ao longo dos passos de simulação;
- persistência de resultados, métricas e logs.

As funções aqui definidas são responsáveis pelo ciclo de vida fim a fim da
simulação, desde o parsing de argumentos da linha de comando até o encerramento
controlado do processo do SUMO.
"""

import sys
import subprocess
import logging
import time
import warnings
import os

from optparse import OptionParser

# Vehicular Cloud
import sumo_manager
import log_manager
import traci

import utils.constants as CONSTANTS

# queue system
from utils.queue import Queue
queue = Queue()

# task manager
from task_manager import Task
tasks = Task()

# cloud manager
from cloud_manager import Clouds
clouds = Clouds()

# scheduling manager
from scheduling_manager import SchedulingManager
schedule = SchedulingManager(clouds)

# system monitor agent
from system_monitor import SchedulingMonitor
monitor = SchedulingMonitor()

# create necessary directories
dirs = ["log", "output", "results", "summary"]
for d in dirs:
    if not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)

def create_dataset(step, radius, resource):
	"""Prepara o dataset de nós/veículos para o passo atual da simulação.

	Args:
		step (float): Instante atual da simulação.
		radius (int): Raio de comunicação considerado para vizinhança.
		resource (int): Perfil de recurso computacional dos veículos.
	"""
	clouds.prepare_nodes(step, traci.vehicle.getIDList(), radius, resource)

def clustering(step, resource):
	"""Executa a formação de nuvens veiculares no passo atual.

	Args:
		step (float): Instante atual da simulação.
		resource (int): Tipo/nível de recurso (ex.: 1, 2, 3, 4 em MIPS).
	"""
	# resource => 1, 2, 3, 4 (MIPS)
	clouds.build_vehicular_clouds(step, resource, schedule)

def run_scheduling(step, algorithm, start_process):
	"""Dispara o escalonamento de tarefas quando o tempo mínimo é atingido.

	Args:
		step (float): Instante atual da simulação.
		algorithm (str): Nome do algoritmo de escalonamento.
		start_process (int): Tempo mínimo para iniciar o escalonamento.
	"""
	# pass
	if step >= start_process:
		# print("[DEBUG] ESCALONANDO TAREFAS...")
		schedule.insert(tasks, queue, clouds, algorithm, step)

def run(network, begin, end, interval, requests, radius, resource, weight, rate, megacycles, algorithm, seed_sumo, seed_task, deadline, start_process, step_lenght):
	"""Executa o loop principal da simulação e do escalonamento.

	Configura geração de tarefas, monitora o sistema a cada passo, realiza
	clusterização periódica das nuvens veiculares, insere tarefas na fila e
	aciona o escalonador conforme a política definida.

	Args:
		network (str): Arquivo de definição da rede (informativo no fluxo atual).
		begin (int): Tempo de início do processamento de tarefas.
		end (int): Duração/fim da janela de simulação.
		interval (int): Intervalo de clusterização de nuvens veiculares.
		requests (int): Intervalo de chegada de requisições (parâmetro externo).
		radius (int): Raio de comunicação entre veículos.
		resource (int): Perfil de recurso computacional dos veículos.
		weight (int): Peso médio das tarefas.
		rate (int): Taxa de geração de tarefas.
		megacycles (int): Carga computacional média das tarefas.
		algorithm (str): Algoritmo de escalonamento selecionado.
		seed_sumo (int|str): Semente usada pelo SUMO.
		seed_task (int|str): Semente usada para geração de tarefas.
		deadline (int|str): Parâmetro de deadline para tarefas.
		start_process (int): Tempo para habilitar escalonamento.
		step_lenght (float): Tamanho do passo da simulação.
	"""

	print(f"\n{algorithm} starting...\n")

	# simulation time
	simulation_time = float(begin + end)

	logging.debug("Building scenario")	
	logging.debug("Running simulation now")
	logging.debug("Algorithm -> " + algorithm)
	logging.debug("Generating tasks")

	# LOG
	log_manager.get_informations(radius, resource, weight, rate, megacycles, algorithm, seed_task, deadline)
	
	# load the poisson distribution and create the tasks set
	tasks.number_of_tasks(rate, seed_task)
	tasks.load_task_file(weight, megacycles, seed_task, deadline)

	# interval in seconds
	logging.debug("Clustering interval: %d" % interval)
	logging.debug("Tasks interval: %d" % requests)

	# counts total tasks in the system
	total_tasks = 0

	print(f" > Scheduling tasks...")

	# simulation start
	step = 1
	while step == 1 or traci.simulation.getMinExpectedNumber() > 0:

		# https://docs.python.org/2/tutorial/floatingpoint.html
		# simulation step in milliseconds
		step = round(step, 1)

		logging.debug("Minimum expected number of vehicles: %d" % traci.simulation.getMinExpectedNumber())
		traci.simulationStep()
		logging.debug("Simulation time %d" % step)

		# print("Step %.2f" % step)
		# cria base de dados (lat, lon) para cada veículo
		# getVehiclePositions(step)

		# task scheduling process start
		if step >= begin:

			if CONSTANTS.CREATE_DATASET == True:

				create_dataset(step, radius, resource)

			else:

				# system monitor executes at each simulation time step
				monitor.get_status(step, schedule, tasks, clouds, queue, step_lenght)
				
				# vc formation process
				if step % interval == 0:
					
					logging.debug(f"Forming Vehicular Clouds: {step}")
					clustering(step, resource)
				
				if step < simulation_time and round(step,1) % 1 == 0:

					# print("ENTERING TASKS")

					tasks_now = int(tasks.tasks_number.pop(0))
					total_tasks = total_tasks + tasks_now

					logging.debug("Tasks coming up: %d" % tasks_now)
					# print("Tasks coming up: %d" % tasks_now)

					# if task arrived in current step
					if tasks_now > 0:

						internal_control = 0
						temp = []
						for i in tasks.task_set:
							if internal_control != tasks_now:
								logging.debug("Adicionando tarefa %s ao sistema" % i)
								# print("Adicionando tarefa %s ao sistema" % i)
								queue.enqueue(i, tasks.task_set, step)
								temp.append(i)
								internal_control += 1
							else:
								break

						# removes tasks from the initial task set 
						for i in temp:
							logging.debug("Removendo tarefa %s do conjunto inicial de tarefas" % i)
							# print("Removendo tarefa %s do conjunto inicial de tarefas" % x)
							del tasks.task_set[i]

				# checks waiting queue
				if len(queue.get_queue()) > 0:
					run_scheduling(step, algorithm, start_process)
					# pass

			# print()
		
		# simulation ends
		if step == simulation_time + 2:
			# print("Simulation time has ended.")
			break
		
		# increments the simulation time step by 1 time unit
		step += step_lenght

	print(f"\n{algorithm} completed!")
	print("\nThe results were recorded:")
	logging.debug("* Total de tarefas inseridas no sistema %d " % total_tasks)

	# show task table
	# print(queue.task_table)

	# log_manager.log_results(queue.final_queue)
	log_manager.log_results_final(queue.final_queue)

	# print("\nLoad Balance:")
	# print(schedule.load_balance)
	log_manager.load_balance(schedule.load_balance)

	# simulation control
	time.sleep(1)
	logging.debug("Simulation finished")
	print("\nSimulation finished!\n")
	traci.close()
	sys.stdout.flush()
	time.sleep(1)
		
def start_simulation(sumo, scenario, network, begin, end, interval, requests, output, summary, radius, resource, weight, rate, megacycles, algorithm, seed_sumo, seed_task, deadline, start_process, step_lenght):
	"""Inicializa o SUMO/TraCI e delega a execução ao loop principal.

	A função reserva uma porta livre, inicia o SUMO em modo servidor, conecta
	o TraCI e executa a simulação. Em caso de falha, registra exceções e garante
	encerramento do processo do SUMO.

	Args:
		sumo (str): Comando/binário do SUMO.
		scenario (str): Arquivo de configuração do cenário SUMO.
		network (str): Arquivo da rede.
		begin (int): Tempo de início da simulação lógica.
		end (int): Tempo final da simulação lógica.
		interval (int): Intervalo de clusterização.
		requests (int): Intervalo de requisições.
		output (str): Arquivo de saída tripinfo.
		summary (str): Arquivo de saída de resumo.
		radius (int): Raio de comunicação.
		resource (int): Perfil de recurso veicular.
		weight (int): Peso médio das tarefas.
		rate (int): Taxa de tarefas.
		megacycles (int): Carga de processamento das tarefas.
		algorithm (str): Algoritmo de escalonamento.
		seed_sumo (int|str): Semente do SUMO.
		seed_task (int|str): Semente de tarefas.
		deadline (int|str): Prazo das tarefas.
		start_process (int): Instante de início do escalonamento.
		step_lenght (float): Tamanho do passo da simulação.
	"""
	logging.debug("Finding unused port")
	
	unused_port_lock = sumo_manager.UnusedPortLock()
	unused_port_lock.__enter__()
	remote_port = sumo_manager.find_unused_port()

	logging.debug("Port %d was found" % remote_port)
	
	logging.debug("Starting SUMO as a server")
	
	# Defining the Time Step Length
	# https://sumo.dlr.de/docs/Simulation/Basic_Definition.html
	# step_length = step_lenght

	sumo = subprocess.Popen([sumo, "-c", scenario, "--step-length", str(step_lenght), "--seed", seed_sumo, "-W", "--tripinfo-output", output, "--device.emissions.probability", "1.0", "--summary-output", summary ,"--remote-port", str(remote_port)], stdout=sys.stdout, stderr=sys.stderr)    
	
	unused_port_lock.release()
	
	try:
		traci.init(remote_port)
		run(network, begin, end, interval, requests, radius, resource, weight, rate, megacycles, algorithm, seed_sumo, seed_task, deadline, start_process, step_lenght)
	except:
		logging.exception("Something bad happened")
	finally:
		logging.exception("Terminating SUMO")  
		sumo_manager.terminate_sumo(sumo)
		unused_port_lock.__exit__()
		
def main():
	"""Ponto de entrada da aplicação.

	Realiza o parsing dos argumentos de linha de comando, configura o sistema de
	logs e inicia a execução da simulação com os parâmetros fornecidos.
	"""
	# Option handling
	parser = OptionParser()
	parser.add_option("-a", "--command", dest="command", default="sumo", help="The command used to run SUMO [default: %default]", metavar="COMMAND")
	parser.add_option("-b", "--scenario", dest="scenario", default="cologne.sumo.cfg", help="A SUMO configuration file [default: %default]", metavar="FILE")
	parser.add_option("-c", "--network", dest="network", default="network.net.xml", help="A SUMO network definition file [default: %default]", metavar="FILE")    
	parser.add_option("-d", "--begin", dest="begin", type="int", default=0, action="store", help="The simulation time (s) at which the re-routing begins [default: %default]", metavar="BEGIN")
	parser.add_option("-e", "--end", dest="end", type="int", default=10800, action="store", help="The simulation time (s) at which the re-routing ends [default: %default]", metavar="END")
	parser.add_option("-f", "--interval", dest="interval", type="int", default=10, action="store", help="The interval (s) of clustering [default: %default]", metavar="INTERVAL")
	parser.add_option("-g", "--output", dest="output", default="reroute.xml", help="The XML file at which the output must be written [default: %default]", metavar="FILE")
	parser.add_option("-t", "--logfile", dest="logfile", default="sumo-launchd.log", help="log messages to logfile [default: %default]", metavar="FILE")
	parser.add_option("-i", "--summary", dest="summary", default="summary.xml", help="The XML file at which the summary output must be written [default: %default]", metavar="FILE")
	
	# for Vehicular Cloud Environments
	parser.add_option("-j", "--radius", dest="radius", type="int", default=100, action="store", help="Transmission range [default: %default]", metavar="RADIUS")
	parser.add_option("-k", "--resource", dest="resource", type="int", default=1, action="store", help="Resource for each vehicle [default: %default]", metavar="RESOURCE")
	parser.add_option("-l", "--weight", dest="weight", type="int", default=1, action="store", help="Avg weight for each task [default: %default]", metavar="WEIGHT")
	parser.add_option("-m", "--requests", dest="requests", type="int", default=15, action="store", help="The interval (s) of tasks arrival [default: %default]", metavar="REQUESTS")
	parser.add_option("-n", "--rate", dest="rate", type="int", default=10, action="store", help="The interval (s) of tasks arrival [default: %default]", metavar="RATE")
	parser.add_option("-o", "--megacycles", dest="megacycles", type="int", default=10, action="store", help="The interval (s) of tasks arrival [default: %default]", metavar="MEGACYCLES")
	parser.add_option("-p", "--algorithm", dest="algorithm", default="MARINA", help="Algorithm for task scheduling [default: %default]", metavar="ALGORITHM")

	# sumo seed
	parser.add_option("-q", "--seed_sumo", dest="seed_sumo", default=1, help="Seed for SUMO [default: %default]", metavar="SEED-SUMO")
	# task seed
	parser.add_option("-r", "--seed_task", dest="seed_task", default=1, help="Seed for task scheduling [default: %default]", metavar="SEED-TASK")
	# deadline
	parser.add_option("-s", "--deadline", dest="deadline", default=1, help="Deadline for task scheduling [default: %default]", metavar="DEADLINE")
	# start scheduling process
	parser.add_option("-u", "--start_process", dest="start_process", type="int", default=0, action="store", help="The simulation time (s) at which the re-routing begins [default: %default]", metavar="START-PROCESS")
	# step-lenght
	parser.add_option("-v", "--step_lenght", dest="step_lenght", type="float", default=1.0, action="store", help="The simulation time (s) at which the re-routing begins [default: %default]", metavar="STEP-LENGHT")

	(options, args) = parser.parse_args()
	
	logging.basicConfig(filename=options.logfile, level=logging.DEBUG)
	logging.debug("Logging to %s" % options.logfile)
	
	if args:
		logging.warning("Superfluous command line arguments: \"%s\"" % " ".join(args))

	start_simulation(options.command, options.scenario, options.network, options.begin, options.end, options.interval, options.requests, options.output, options.summary, options.radius, options.resource, options.weight, options.rate, options.megacycles, options.algorithm, options.seed_sumo, options.seed_task, options.deadline, options.start_process, options.step_lenght)

def getVehiclePositions(step):
	"""Registra as posições dos veículos em arquivos por ID.

	Para cada veículo presente na simulação, cria/atualiza um arquivo texto com
	linhas no formato: ``tempo x y``.

	Args:
		step (float): Instante atual da simulação.
	"""

	veiculos = traci.vehicle.getIDList()

	for i in range(len(veiculos)):
		arquivo = open(CONSTANTS.PATH + 'src/data/' + str(veiculos[i]) + '.txt', 'a')

		x = str(traci.vehicle.getPosition(veiculos[i])).split(",")
		x = str(x[0]).split("(")

		y = str(traci.vehicle.getPosition(veiculos[i])).split()
		y = str(y[1]).split(")")

		x = float(x[1])
		y = float(y[0])

		arquivo.write(str(step) + " " + str(x) + " " + str(y) + "\n")
		arquivo.close()

if __name__ == "__main__":
	warnings.simplefilter("ignore")
	main()