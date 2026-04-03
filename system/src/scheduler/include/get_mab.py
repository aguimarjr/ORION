
import random

def get_mab_scheduling(cloud_id, cloud_size, tasks):
    '''
    Entrada:
    Lista com peso das tarefas = [5, 4, 2, 1, 2]
    Lista com recursos das nuvens = {'id' : 1, 'bin_capacity': 10},
    '''
    # print(f"Nuvem {cloud_id} possui {cloud_size} unidades de recurso!")
    # print(f"Tasks: {tasks}")

    # Gere uma lista de itens com tamanhos aleatórios
    task_control = {}
    item_sizes = []
    contador = 0
    for task in tasks:
        item_sizes.append(tasks[task])
        task_control[contador] = task
        contador += 1

    # print("Tasks New", item_sizes)
    # print("Tasks Control", task_control)

    bins = [
        {'id' : cloud_id, 'bin_capacity': cloud_size},
        # {'id' : 2, 'bin_capacity': 5},
        # {'id' : 3, 'bin_capacity': 12},
    ]

    # Extração das capacidades dos recipientes
    bin_capacities = {bin_['id']: bin_['bin_capacity'] for bin_ in bins}

    # Define os parâmetros do problema
    num_items = len(item_sizes)

    # bin_capacity = 10
    num_trials = 1000

    # Inicialize as informações do Bandit (recompensas e contagens)
    bandit_info = [{"total_size": 0, "reward": 0, "count": 0} for _ in range(num_items)]

    # Lista para manter o registro das atribuições de itens a recipientes
    item_allocations = [None] * num_items

    # print(item_allocations)

    # Função para calcular o fitness de uma alocação
    def fitness(bin_allocation):
        bin_count = 0
        bin_usage = {bin_['id']: 0 for bin_ in bins}
        
        for item in range(num_items):
            fit = False
            for bin_ in bins:
                bin_id = bin_['id']
                bin_capacity = bin_['bin_capacity']
                if bin_usage[bin_id] + item_sizes[item] <= bin_capacity:
                    fit = True
                    bin_usage[bin_id] += item_sizes[item]
                    item_allocations[item] = bin_id  # Registra a alocação do item ao recipiente
                    break
            if not fit:
                # para execução ao abrir novo bin!
                break
                bin_count += 1
                bin_id = bin_count
                bin_usage[bin_id] = item_sizes[item]
                item_allocations[item] = bin_id  # Registra a alocação do item ao recipiente
        
        return bin_count

    # Algoritmo MAB simplificado
    for trial in range(num_trials):
        # Seleciona um braço (item) usando uma estratégia do MAB (por exemplo, epsilon-greedy)
        epsilon = 0.1  # Probabilidade de exploração
        if random.random() < epsilon:
            # Exploração aleatória
            selected_item = random.randint(0, num_items - 1)
        else:
            # Exploração com base na recompensa média
            selected_item = max(range(num_items), key=lambda x: bandit_info[x]["reward"] / (bandit_info[x]["count"] + 1e-5))
        
        # Aloca o item ao recipiente e calcula a recompensa
        bin_allocation = [bin["total_size"] for bin in bandit_info]
        bin_allocation[selected_item] += item_sizes[selected_item]
        reward = fitness(bin_allocation)
        
        # Atualiza as informações do Bandit
        bandit_info[selected_item]["total_size"] += item_sizes[selected_item]
        bandit_info[selected_item]["reward"] += reward
        bandit_info[selected_item]["count"] += 1

    # Encontra a melhor alocação
    best_allocation = [bin["total_size"] for bin in bandit_info]
    best_fitness = fitness(best_allocation)

    # Imprime a melhor alocação encontrada
    # print("Melhor alocação:", best_allocation)
    # print("Número total de recipientes usados:", best_fitness)

    scheduled_tasks = []

    # # Imprime as alocações de itens aos recipientes
    for item, bin_ in enumerate(item_allocations):
        if bin_ != None:
            # print(f"Item {item} alocado ao recipiente {bin_}")
            scheduled_tasks.append(task_control[item])

    return scheduled_tasks
