
from paretoset import paretoset
import pandas as pd

def run_pareto_set(tasks_pareto, cloud_capacity):

	# FAZ MAPEAMENTO CUSTO E TIME PARA PARETO
	# time = cpu / cloud_capacity
	# deadline = task['deadline']
	lista_tarefas = []
	lista_time = []
	lista_deadline = []
	for i in tasks_pareto:
		lista_tarefas.append(i)
		current_time = round(tasks_pareto[i][0] / cloud_capacity, 3)
		lista_time.append(current_time)
		lista_deadline.append(tasks_pareto[i][2])

	# print("LISTAS PARETO")
	# print("Ids:",lista_tarefas)
	# print("Times:",lista_time)
	# print("Deadline:",lista_deadline)

	local_tasks_pareto = pd.DataFrame({'time': lista_time, 'deadline':lista_deadline})
	mask = paretoset(local_tasks_pareto, sense=["min", "min"])

	# print("Pareto:",mask)

	lista_resultado = []
	contador = 0
	for i in range(len(mask)):
		if mask[i] == True:
			lista_resultado.append(lista_tarefas[contador])
		contador += 1
	
	# print("LISTA FINAL")
	# print(lista_resultado)

	return lista_resultado