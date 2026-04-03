
def first_fit_decreasing_algorithm(sizes, sizes_deadline, max_summed_size_per_bin, return_sizes=None):
	
	# print("Capacidade:",max_summed_size_per_bin)
	# print("TarefasSize:",sizes)
	# print("TaredasDeadline:",sizes_deadline)
	best_schedule = {}
	list_of_bins = []

	# sort the objects in decreasing order by their sizes:
	# objects = list(sizes.keys())
	# sort in descending order
	# sorted_objects = objects
	# NAO FAZ ORDENACAO PARA NAO PERDER ORDEM DE PRIORIDADE DA HEAP -> DEADLINE
	# sorted(objects, key=lambda x: sizes[x], reverse=True)

	# DEBUG:
	# ORDEM DE ESCALONAMENTO BASEADA NO DEADLINE DAS TAREFAS
	objects = list(sizes.keys())
	sorted_objects = sorted(objects, key=lambda x: sizes[x], reverse=False)

	# print("SORTED TASKS by deadline")
	# print(sorted_objects)

	# insert each object in the first bin with sufficient remaining space:
	for my_object in sorted_objects:
		found_a_bin = False
		object_size = sizes[my_object]
		# print(my_object)
		# check if there is a bin with space for this object
		for index, my_bin in enumerate(list_of_bins): # 'my_bin' is a set of objects in a bin
			# print("Bin:",index)
			# get the summed size of the objects in my_bin:
			summed_sizes_in_bin = sum([sizes[x] for x in my_bin])
			# if there is room for this object in the bin, put it in this bin:
			# print(" * SOMA:",summed_sizes_in_bin)
			if object_size <= (max_summed_size_per_bin - summed_sizes_in_bin):
				# print("  * cabe aqui > ",my_object)
				list_of_bins[index].add(my_object)
				found_a_bin = True
				break # jump out of the 'for index, my_bin' loop
		# if we didn't put my_object in any bin, then put it in a new bin:
		if object_size <= max_summed_size_per_bin:
			if found_a_bin == False:
				list_of_bins.append({my_object})
		else:
			pass
			# print("NAO DEVE SER ABERTO UM BIN")

	# print("Bins:",list_of_bins)
	# DEBUG: RETORNA BIN COM MAIOR NUMERO DE TAREFAS
	if len(list_of_bins) > 0:
		best_schedule = get_best_allocation(list_of_bins)
	# return list_of_bins # RETORNA ATRIBUICAO NOS BINS
	return best_schedule # RETORNA BIN COM MAIOR NUMERO DE ITENS

def get_best_allocation(final_bins):
	# seleciona escalonamento com maior numero de tarefas
	# print("BEST")
	id_best = -1
	best = -1
	best_allocation = {}
	for j in range(len(final_bins)):
		if len(final_bins[j]) > best:
			best = len(final_bins[j])
			id_best = j

	# TESTE DE ESTIMATIVA DE PROCESSAMENTO <ID_TAREFA, ESTIMATIVA>
	for k in final_bins[id_best]:
		best_allocation[k] = -1
		# del local_tasks[k]

	# print(best_allocation)
	return best_allocation