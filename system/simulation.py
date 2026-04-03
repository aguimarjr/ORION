#!/usr/bin/python3
# Autor: Joahannes B. D. da Costa <joahannes.costa@unifesp.br>
# Data: 31.10.2025
# Descricao: Simulator for Task Scheduling in Vehicular Edge Computing

import argparse
import os

parser = argparse.ArgumentParser(description='Simulator for Task Scheduling in Vehicular Edge Computing ')
parser.add_argument("-a", "--scenario", dest="scenario", help="", metavar="SCENARIO")
parser.add_argument("-b", "--interval", dest="interval", default=10, help="", metavar="INTERVAL")
parser.add_argument("-c", "--tasks", dest="tasks", default=1, help="", metavar="TASKS")
parser.add_argument("-d", "--begin", dest="begin", default=1, help="", metavar="BEGIN")
parser.add_argument("-e", "--end", dest="end", default=3600, help="", metavar="END")
parser.add_argument("-f", "--radius", dest="radius", default=2000, help="", metavar="RADIUS")
parser.add_argument("-g", "--resources", dest="resources", default=1, help="", metavar="RESOURCES")
parser.add_argument("-i", "--weight", dest="weight", default=10, help="", metavar="WEIGHT")
parser.add_argument("-j", "--taskrate", dest="taskrate", default=1, help="", metavar="RATE")
parser.add_argument("-k", "--cpucycle", dest="cpucycle", default=10, help="", metavar="CPU")
parser.add_argument("-l", "--algorithm", dest="algorithm", default="MARINA", help="", metavar="ALGORITHM")
parser.add_argument("-m", "--seed_sumo", dest="seed_sumo", default=1, help="", metavar="SEED_SUMO")
parser.add_argument("-n", "--seed_task", dest="seed_task", default=1, help="", metavar="SEED_TASK")
parser.add_argument("-o", "--deadline", dest="deadline", default=1, help="", metavar="DEADLINE")
parser.add_argument("-p", "--startprocess", dest="start_process", default=1, help="", metavar="START_PROCESS")
parser.add_argument("-q", "--steplenght", dest="step_lenght", default=1.0, help="", metavar="STEP_LENGHT")

options = parser.parse_args()

# print("+-------------------------------+")
# print("+         Ambiente VEC          +")
# print("+-------------------------------+")
# print(" Cenário:",options.scenario)
# print(" Intervalo:",options.interval)
# print(" Tarefas:",options.tasks)
# print(" Início:",options.begin)
# print(" Fim:",options.end)
# print(" Raio:",options.radius)
# print(" Recursos:",options.resources)
# print(" Peso:",options.weight)
# print(" Taxa de chegada:",options.taskrate)
# print(" Ciclos de CPU:",options.cpucycle)
# print(" Algoritmo:",options.algorithm)
# print(" SeedSUMO:",options.seed_sumo)
# print(" SeedTarefa:",options.seed_task)
# print(" Prazo:",options.deadline)
# print(" Início do Processo:",options.start_process)
# print(" Comprimento do Passo:",options.step_lenght)
# print("+-------------------------------+")

dirName = 'log/' + str(options.algorithm)
if not os.path.isdir(dirName):
	os.makedirs(dirName)
else:
	pass

# simulation log
current_config = dirName + '/' + str(options.algorithm) + '_TASKS_' + str(options.tasks) + '_RESOURCES_' + str(options.resources) + '_SIZE_' + str(options.weight) + '_RATE_' + str(options.taskrate) + '_CPU_' + str(options.cpucycle) + '_DEADLINE_' + str(options.deadline) + '_SEED-SUMO_' + str(options.seed_sumo) + '_SEED-TASK_' + str(options.seed_task) + '.txt'

# replace file
if os.path.exists(current_config):
	os.system('rm ' + current_config)

os.system('python src/main.py --scenario scenario/cologne/cologne100.sumocfg --network scenario/cologne/cologne2.net.xml --interval ' + str(options.interval) + ' --requests ' + str(options.tasks) + ' --begin ' + str(options.begin) + ' --end ' + str(options.end) + ' --output output/cologne-output.xml --logfile ' + current_config + ' --summary summary/cologne.summary.xml --radius ' + str(options.radius) + ' --resource ' + str(options.resources) + ' --weight ' + str(options.weight) + ' --rate ' + str(options.taskrate) + ' --megacycles ' + str(options.cpucycle) + ' --algorithm ' + str(options.algorithm) + ' --seed_sumo ' + str(options.seed_sumo) + ' --seed_task ' + str(options.seed_task) + ' --deadline ' + str(options.deadline) + ' --start_process ' + str(options.start_process) + ' --step_lenght ' + str(options.step_lenght))

