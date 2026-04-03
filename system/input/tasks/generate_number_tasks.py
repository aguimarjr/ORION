#!/usr/bin/env python

import numpy as np
import random
from scipy.stats import poisson
import matplotlib.pyplot as plt

def generate_number_of_tasks(seed, rate, plot):

	# compute poisson
	poisson_set = compute_poisson(rate)

	# cria arquivo de distribuicao das tarefas
	# task_seed_1_rate_1.txt
	task_file = open('task_seed_' + str(seed) + '_rate_' + str(rate) + '.txt','w')

	# poisson_set.sort()
	for i in poisson_set:
		task_file.write(str(i) + "\n")
	task_file.close()
	
	if plot == True:
		# descomentar para visualizar o plot da poisson
		count, bins, ignored = plt.hist(
			poisson_set,
			# ,
			facecolor='red',
			edgecolor='black',
			density=True,
			align='mid',
			alpha=0.7)
		plt.xlabel('Number of tasks')
		plt.ylabel(r'$P(X = k) = \frac{e^{-k} . \lambda^k}{k!}$')
		plt.title('Seed: ' + str(seed) + ' - Rate: ' + str(rate))
		plt.savefig('tasks_arrival_seed_'+str(seed)+'_rate_'+str(rate)+'.eps', dpi=200, bbox_inches = 'tight', pad_inches = 0.05)
		plt.close()

def compute_poisson(taxa):
	lamb = taxa # esperanca de ocorrencia
	size = 20000
	s = np.random.poisson(lamb,size)
	return s

def plot_poisson():

	PROB = (1,5,10,20,50)
	STYLE = {1:"-", 5:"-.", 10:"-", 20:":", 50:"--"}

	# TESTE 1
	arr = []
	for i in PROB:
		rv = poisson(i)
		for num in range(0,100):
	 		arr.append(rv.pmf(num))

		prob = rv.pmf(i)

		plt.xlabel('Number of tasks')
		plt.ylabel(r'$P(X = k) = \frac{e^{-k} . \lambda^k}{k!}$')

		# plt.grid(True)
		plt.plot(arr, linewidth=1.5, linestyle=STYLE[i], label=r'$\lambda = $'+str(i))
		plt.plot([i], [prob], marker='o', markersize=6, color="red")

		arr = []

	plt.legend()

	plt.savefig('tasks_arrival_TESTE.eps', dpi=400, bbox_inches = 'tight', pad_inches = 0.05)

	plt.close()
	
if __name__ == "__main__":

	# plot_poisson()

	SEED = [1,2,3,4,5]
	RATE = [30]

	for seed in SEED:
		for rate in RATE:
			generate_number_of_tasks(seed, rate, False)


	# plot_poisson()