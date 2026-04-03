#!/usr/bin/python3
# title: ORION.py
# author: Matheus Ramos Esteves
# date: 17.11.2025
# modified: Refatorado para objetivos diretos (custo e taxa de sucesso)

import random
import math
import utils.general_management as management

from .include.pareto_manager import get_pareto_manager

def run(queue, clouds, tasks):
    # print("[DEBUG] Running ORION...")
    # Coleta tarefas pendentes
    local_tasks = {}
    deadlines = {}
    for tid in queue.get_queue():
        info = queue.task_queue_control[tid]
        if info['status'] == 'PENDING':
            local_tasks[tid] = info['size']
            deadlines[tid] = info['deadline']

    if len(local_tasks) == 0:
        return {}, {}

    # Preparar lista ordenada de task_ids para indexação
    task_ids = list(local_tasks.keys())
    cloud_ids = list(clouds.clouds.keys())
    capacities = {cid: clouds.clouds[cid]['mips'] for cid in cloud_ids}

    # Se não houver tarefas ou houver só uma tarefa, evita EA e faz alocação simples/gulosa
    if len(task_ids) == 0:
        return {}, {}
    if len(task_ids) == 1:
        tid = task_ids[0]
        for cid in cloud_ids:
            if local_tasks[tid] <= capacities[cid]:
                allocation = {cid: {tid: -1}}
                proc = management.get_processing_time(capacities[cid], tasks, allocation[cid])
                for t in proc:
                    allocation[cid][t] = proc[t]
                resource_splited = {cid: management.split_resource(allocation[cid], clouds. clouds[cid], local_tasks)}
                return allocation, resource_splited
        return {}, {}

    # Parâmetros evolutivos
    POP = 30
    GENS = 10
    CX_PROB = 0.9
    MUT_PROB = 0.15

    # Inicializa população
    population = [random_individual(task_ids, cloud_ids, capacities, local_tasks) for _ in range(POP)]
    population = [repair(ind, task_ids, cloud_ids, capacities, local_tasks) for ind in population]

    for gen in range(GENS):
        offspring = []
        while len(offspring) < POP:
            p1, p2 = tournament(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)
            if random.random() < CX_PROB:
                c1, c2 = crossover(p1, p2)
            else:
                c1, c2 = p1[:], p2[:]
            if random.random() < MUT_PROB:
                mutate(c1, cloud_ids)
            if random.random() < MUT_PROB:
                mutate(c2, cloud_ids)
            c1 = repair(c1, task_ids, cloud_ids, capacities, local_tasks)
            c2 = repair(c2, task_ids, cloud_ids, capacities, local_tasks)
            offspring.append(c1)
            offspring.append(c2)

        # Combina e seleciona usando não-dominância + crowding
        population = environmental_selection(population + offspring,
                                             task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds, POP)

    # ========================================
    # PLOT OTIMIZADO DA FRENTE DE PARETO (2D)
    # ========================================
    try:
        from utils.pareto_collector import pareto_collector
        # Calcula objetivos da população final
        pop_objs = [evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds) 
                    for ind in population]
        
        pareto_collector.add_execution('nsga2', pop_objs)
            
    except Exception as e:
        # print(f"[ERRO] Falha ao processar Pareto: {e}")
        import traceback
        traceback.print_exc()

    # Escolhe melhores frentes
    fronts = fast_nondominated_sort(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)

    # Escolhe melhor indivíduo da primeira fronteira
    # Critério: menor custo como desempate (ou você pode usar outro critério)
    best_front = fronts[0]
    best = min(best_front, key=lambda ind: evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)[0])

    # print(f"[DEBUG] Melhor solução: Custo=${evaluate(best, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)[0]:.2f}, "
        #   f"Taxa de Sucesso={-evaluate(best, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)[1]*100:.1f}%")

    # Constrói resultado final
    result, resource_splited = build_result(best, task_ids, cloud_ids, capacities, tasks, local_tasks, deadlines, clouds)
    return result, resource_splited

# ---------- Funções auxiliares ----------

def random_individual(task_ids, cloud_ids, capacities, local_tasks):
    # Atribui cada tarefa a uma nuvem aleatória
    return [random.choice(cloud_ids) for _ in task_ids]

def repair(ind, task_ids, cloud_ids, capacities, local_tasks):
    """
    Garante que soma(size) <= capacidade por nuvem. 
    Estratégia: se exceder, remove (marca None) tarefas maiores primeiro daquela nuvem.
    Agora ignora entradas None e cid desconhecidos.
    """
    # inicializa listas por nuvem
    sizes_by_cloud = {cid: [] for cid in cloud_ids}

    # agrupa tarefas por nuvem, ignorando None e nuvens não presentes
    for pos, cid in enumerate(ind):
        if cid is None:
            # tarefa não alocada — ignora
            continue
        if cid not in sizes_by_cloud:
            # proteção extra: se houver um cid inválido, ignora
            continue
        tid = task_ids[pos]
        sizes_by_cloud[cid].append((tid, local_tasks[tid], pos))

    # para cada nuvem, verifica se a soma excede capacidade e remove tarefas maiores até caber
    for cid in cloud_ids:
        used = sum(x[1] for x in sizes_by_cloud[cid])
        if used > capacities[cid]:
            # ordena por tamanho decrescente e remove até caber
            for (tid, sz, pos) in sorted(sizes_by_cloud[cid], key=lambda x: x[1], reverse=True):
                if used <= capacities[cid]:
                    break
                # marca a posição como não alocada
                ind[pos] = None
                used -= sz
    return ind

def resource_price(uso_recursos):
    """
    Calcula custo monetário baseado no uso de recursos.
    Replica a função do system_monitor.py
    """
    total_price = 0
    time_using = uso_recursos['processing_time']
    
    vehicle_price = 5.17296 # c8a.metal-24xl
    bs_price = 10.34592 # c8a.48xlarge

    vehicle_total_cost = (vehicle_price * uso_recursos['vehicle']) * time_using
    bs_total_cost = (bs_price * uso_recursos['bs']) * time_using

    total_price = round(vehicle_total_cost + bs_total_cost, 3)
    return total_price

def evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Nova função de avaliação com 2 objetivos diretos:
    f1: Custo monetário total (minimizar)
    f2: Taxa de falha (1 - taxa de sucesso) (minimizar)
    
    Retorna: (total_cost, failure_rate)
    """
    # Monta alocação
    allocation = {cid: [] for cid in cloud_ids}
    for pos, cid in enumerate(ind):
        if cid is not None:
            allocation[cid].append(task_ids[pos])

    total_cost = 0.0
    successful_tasks = 0
    total_tasks = 0

    for cid in cloud_ids:
        task_set = allocation[cid]
        if len(task_set) == 0:
            continue
        
        # Calcula tempo de processamento
        sub_dict = {tid: -1 for tid in task_set}
        proc = management.get_processing_time(capacities[cid], tasks_global, sub_dict)
        
        # Calcula uso de recursos para cada tarefa
        tasks_with_times = {tid: proc[tid] for tid in task_set}
        resource_usage = management.split_resource(tasks_with_times, clouds. clouds[cid], local_tasks)
        
        for tid in task_set:
            total_tasks += 1
            proc_time = proc[tid]
            
            # f2: Conta tarefas bem-sucedidas (dentro do deadline)
            if proc_time <= deadlines[tid]:
                successful_tasks += 1
            
            # f1: Acumula custo monetário
            task_cost = resource_price(resource_usage[tid])
            total_cost += task_cost

    # Calcula taxa de sucesso
    if total_tasks == 0:
        failure_rate = 1.0  # Pior caso: nenhuma tarefa alocada
    else:
        success_rate = successful_tasks / total_tasks
        failure_rate = 1.0 - success_rate

    # Retorna (custo_total, taxa_de_falha)
    # Ambos devem ser minimizados
    return (total_cost, failure_rate)

def dominates(f1, f2):
    """
    Verifica se f1 domina f2 (dominância de Pareto).
    f1 domina f2 se é melhor ou igual em todos objetivos e estritamente melhor em pelo menos um.
    """
    return all(a <= b for a, b in zip(f1, f2)) and any(a < b for a, b in zip(f1, f2))

def fast_nondominated_sort(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Algoritmo de ordenação rápida não-dominada do NSGA-II.
    Atualizado para usar a nova função evaluate com 2 objetivos.
    """
    fitness_cache = {}
    S = {}
    n = {}
    fronts = [[]]

    for p in population:
        fp = evaluate(p, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
        fitness_cache[id(p)] = fp
        S[id(p)] = []
        n[id(p)] = 0
        for q in population:
            if p is q:
                continue
            fq = fitness_cache. get(id(q))
            if fq is None:
                fq = evaluate(q, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
                fitness_cache[id(q)] = fq
            if dominates(fp, fq):
                S[id(p)].append(q)
            elif dominates(fq, fp):
                n[id(p)] += 1
        if n[id(p)] == 0:
            fronts[0].append(p)

    i = 0
    while len(fronts[i]) > 0:
        next_front = []
        for p in fronts[i]:
            for q in S[id(p)]:
                n[id(q)] -= 1
                if n[id(q)] == 0:
                    next_front. append(q)
        i += 1
        fronts. append(next_front)
    if len(fronts[-1]) == 0:
        fronts.pop()
    return fronts

def crowding_distance(front, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Calcula a distância de crowding para manter diversidade na população.
    Atualizado para 2 objetivos.
    """
    if len(front) == 0:
        return {}
    distances = {id(ind): 0.0 for ind in front}
    fitness_values = [evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds) for ind in front]
    num_obj = len(fitness_values[0])  # Agora será 2
    
    for m in range(num_obj):
        sorted_idx = sorted(range(len(front)), key=lambda i: fitness_values[i][m])
        distances[id(front[sorted_idx[0]])] = float('inf')
        distances[id(front[sorted_idx[-1]])] = float('inf')
        min_m = fitness_values[sorted_idx[0]][m]
        max_m = fitness_values[sorted_idx[-1]][m]
        if max_m == min_m:
            continue
        for k in range(1, len(front)-1):
            prev = fitness_values[sorted_idx[k-1]][m]
            nextv = fitness_values[sorted_idx[k+1]][m]
            distances[id(front[sorted_idx[k]])] += (nextv - prev) / (max_m - min_m)
    return distances

def environmental_selection(pop, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds, POP):
    """
    Seleção ambiental usando não-dominância e crowding distance.
    """
    fronts = fast_nondominated_sort(pop, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
    new_pop = []
    for front in fronts:
        if len(new_pop) + len(front) <= POP:
            new_pop.extend(front)
        else:
            cd = crowding_distance(front, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
            sorted_front = sorted(front, key=lambda ind: cd[id(ind)], reverse=True)
            needed = POP - len(new_pop)
            new_pop. extend(sorted_front[:needed])
            break
    return new_pop

def tournament(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds, k=2):
    """
    Seleção por torneio binário usando dominância + crowding. 
    """
    cands = random.sample(population, k)
    fronts = fast_nondominated_sort(cands, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
    # pega frente 0; se empate usa crowding
    if len(fronts[0]) == 1:
        winner = fronts[0][0]
    else:
        cd = crowding_distance(fronts[0], task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
        winner = max(fronts[0], key=lambda ind: cd[id(ind)])
    # segundo vencedor só para cruzamento
    second = random.choice([ind for ind in cands if ind is not winner])
    return winner, second

def crossover(p1, p2):
    """
    Operador de cruzamento de um ponto. 
    """
    n = len(p1)
    if n < 2:
        return p1[:], p2[:]
    point = random.randint(1, n-1)
    c1 = p1[:point] + p2[point:]
    c2 = p2[:point] + p1[point:]
    return c1, c2

def mutate(ind, cloud_ids):
    """
    Operador de mutação: troca aleatoriamente a alocação de uma tarefa.
    """
    if len(ind) == 0 or len(cloud_ids) == 0:
        return ind
    pos = random.randint(0, len(ind)-1)
    ind[pos] = random.choice(cloud_ids)
    return ind

def build_result(best, task_ids, cloud_ids, capacities, tasks_global, local_tasks, deadlines, clouds):
    """
    Constrói o resultado final a partir do melhor indivíduo. 
    """
    # best é vetor de cloud_ids ou None
    allocation = {}
    for pos, cid in enumerate(best):
        if cid is None:
            continue
        tid = task_ids[pos]
        allocation. setdefault(cid, {})[tid] = -1

    result = {}
    resource_splited = {}

    for cid in allocation:
        # calcula processing times
        proc = management.get_processing_time(capacities[cid], tasks_global, allocation[cid])
        for tid in proc:
            allocation[cid][tid] = proc[tid]
        result[cid] = allocation[cid]
        # mapeia recursos
        resource_splited[cid] = management.split_resource(allocation[cid], clouds.clouds[cid], local_tasks)

    return result, resource_splited