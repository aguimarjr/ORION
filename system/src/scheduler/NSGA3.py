#!/usr/bin/python3
# title: NSGA3. py
# author: Matheus Ramos Esteves
# date: 17.11.2025
# modified: Refatorado para objetivos diretos (custo e taxa de sucesso)

import random
import math
import utils.general_management as management

def run(queue, clouds, tasks):
    """
    NSGA-III scheduler entrypoint.  Retorna (result, resource_splited) compatível com o NSGA-II.
    """
    # print("[DEBUG] Running NSGA-III...")
    # Coleta tarefas pendentes
    local_tasks = {}
    deadlines = {}
    for tid in queue. get_queue():
        info = queue.task_queue_control[tid]
        if info['status'] == 'PENDING':
            local_tasks[tid] = info['size']
            deadlines[tid] = info['deadline']

    if len(local_tasks) == 0:
        return {}, {}

    task_ids = list(local_tasks.keys())
    cloud_ids = list(clouds.clouds.keys())
    capacities = {cid: clouds.clouds[cid]['mips'] for cid in cloud_ids}

    if len(task_ids) == 0:
        return {}, {}
    if len(task_ids) == 1:
        # comportamento idêntico ao NSGA-II para 1 tarefa
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

    # Parâmetros — ajuste conforme necessário
    POP = 30
    GENS = 15
    CX_PROB = 0.9
    MUT_PROB = 0.15

    # Número de objetivos: agora são 2 (custo e taxa de falha)
    M = 2
    # Geração de pontos de referência (Das & Dennis).  Para 2 objetivos, divisões lineares
    ref_divisions = 12  # Maior divisão para melhor cobertura em 2D
    reference_points = generate_reference_points(M, ref_divisions)

    # print(f"[DEBUG] NSGA-III: {len(reference_points)} pontos de referência gerados para {M} objetivos")

    # Inicializa população
    population = [random_individual(task_ids, cloud_ids) for _ in range(POP)]
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

        # Sobrevivência: NSGA-III selection
        population = nsga3_selection(population + offspring,
                                     POP, reference_points,
                                     task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)
        
    try:
        from utils.pareto_collector import pareto_collector
        
        # Calcula objetivos da população final
        pop_objs = [evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds) 
                    for ind in population]
        
        # Adiciona ao coletor global
        pareto_collector.add_execution('nsga3', pop_objs)
        
    except Exception as e:
        print(f"[AVISO] Falha ao coletar dados para plots: {e}")

    # Escolhe melhor indivíduo a partir da frente 0 (critério: menor custo)
    fronts = fast_nondominated_sort(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)
    best_front = fronts[0]
    best = min(best_front, key=lambda ind: evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)[0])

    # print(f"[DEBUG] Melhor solução: Custo=${evaluate(best, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)[0]:.2f}, "
        #   f"Taxa de Sucesso={-evaluate(best, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks, clouds)[1]*100 + 100:.1f}%")

    result, resource_splited = build_result(best, task_ids, cloud_ids, capacities, tasks, local_tasks, deadlines, clouds)
    return result, resource_splited

# ----------------- Representação e reparo (compatível com NSGA-II) -----------------

def random_individual(task_ids, cloud_ids):
    return [random.choice(cloud_ids) for _ in task_ids]

def repair(ind, task_ids, cloud_ids, capacities, local_tasks):
    sizes_by_cloud = {cid: [] for cid in cloud_ids}
    for pos, cid in enumerate(ind):
        if cid is None:
            continue
        if cid not in sizes_by_cloud:
            continue
        tid = task_ids[pos]
        sizes_by_cloud[cid].append((tid, local_tasks[tid], pos))

    for cid in cloud_ids:
        used = sum(x[1] for x in sizes_by_cloud[cid])
        if used > capacities[cid]:
            for (tid, sz, pos) in sorted(sizes_by_cloud[cid], key=lambda x: x[1], reverse=True):
                if used <= capacities[cid]:
                    break
                ind[pos] = None
                used -= sz
    return ind

# ----------------- Avaliação (2 objetivos diretos) -----------------

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
        resource_usage = management.split_resource(tasks_with_times, clouds.clouds[cid], local_tasks)
        
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
    """
    return all(a <= b for a, b in zip(f1, f2)) and any(a < b for a, b in zip(f1, f2))

def fast_nondominated_sort(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Algoritmo de ordenação rápida não-dominada.
    Atualizado para passar o objeto clouds.
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

# ----------------- NSGA-III specific utilities -----------------

def generate_reference_points(M, p):
    """
    Das & Dennis reference point generation for M objectives with p divisions.
    Returns list of M-dimensional unit vectors. 
    
    Para M=2: gera p+1 pontos uniformemente distribuídos na linha de 0 a 1. 
    """
    ref_points = []
    # generate all non-negative integer tuples of length M summing to p
    for comb in compositions(p, M):
        vec = [c / float(p) for c in comb]
        ref_points.append(tuple(vec))
    
    # convert to unit direction vectors (avoid zero vector)
    cleaned = []
    for v in ref_points:
        norm = math.sqrt(sum(x * x for x in v))
        if norm < 1e-9:  # Evita vetor zero
            continue
        cleaned.append(tuple(x / norm for x in v))
    
    return cleaned

def compositions(n, k):
    """
    Generate all k-tuples of non-negative integers summing to n. 
    """
    if k == 1:
        yield (n,)
    else:
        for i in range(n + 1):
            for tail in compositions(n - i, k - 1):
                yield (i,) + tail

def nsga3_selection(pop, POP, reference_points,
                    task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Seleção NSGA-III: combina não-dominância com associação a pontos de referência.
    """
    # 1) non-dominated sort
    fronts = fast_nondominated_sort(pop, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
    new_pop = []
    for front in fronts:
        if len(new_pop) + len(front) <= POP:
            new_pop.extend(front)
        else:
            # precisamos escolher alguns da 'front' usando associação a reference points
            to_add = POP - len(new_pop)
            selected = reference_based_selection(front, to_add, reference_points,
                                                 task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
            new_pop.extend(selected)
            break
    return new_pop

def reference_based_selection(front, slots, reference_points,
                              task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Seleciona 'slots' indivíduos da 'front' usando associação a reference_points.
    Procedimento NSGA-III:
      - compute objective vectors
      - shift by ideal point and normalize by intercepts
      - associate each individual to nearest reference direction (perpendicular distance)
      - niching: preencha por referência com menos associados, escolhendo o mais próximo
    """
    # calcula valores objetivos para individuals
    objs = [evaluate(ind, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds) for ind in front]
    M = len(objs[0])  # Agora M=2

    # ideal point = min em cada objetivo
    ideal = [min(o[i] for o in objs) for i in range(M)]
    
    # intercepts: usamos max por objetivo (alternativa: calcular hiperplano)
    intercepts = [max(o[i] for o in objs) for i in range(M)]
    
    # evita divisão por zero
    intercepts = [intercepts[i] if intercepts[i] - ideal[i] > 1e-9 else ideal[i] + 1.0 for i in range(M)]

    # normaliza objetivos: z = (f - ideal) / (intercept - ideal)
    normalized = []
    for o in objs:
        z = [(o[i] - ideal[i]) / (intercepts[i] - ideal[i]) if (intercepts[i] - ideal[i]) > 1e-9 else 0.0 
             for i in range(M)]
        normalized.append(z)

    # Associação: calcular distância perpendicular a cada referência
    assoc = {i: [] for i in range(len(reference_points))}
    distances = []  # distance from each individual to its assigned ref
    
    for idx, z in enumerate(normalized):
        best_r = None
        best_dist = None
        z_vec = z
        for r_idx, r in enumerate(reference_points):
            # r já é unitário
            # projeção escalar: d = z . r
            d1 = sum(z_vec[j] * r[j] for j in range(M))
            
            # vetor projetado sobre r
            proj = [d1 * r[j] for j in range(M)]
            
            # distância perpendicular
            perp = math.sqrt(sum((z_vec[j] - proj[j]) ** 2 for j in range(M)))
            
            if best_dist is None or perp < best_dist:
                best_dist = perp
                best_r = r_idx
        
        assoc[best_r].append(idx)
        distances.append(best_dist)

    # niching: escolha iterativa por referência
    selected_indices = set()
    reference_list = list(range(len(reference_points)))
    
    # count associated already selected (init 0)
    rho = {r: 0 for r in reference_list}
    
    # precompute nearest order for each ref
    sorted_per_ref = {}
    for r in reference_list:
        members = assoc[r]
        # sort members by distance ascending
        sorted_per_ref[r] = sorted(members, key=lambda i: distances[i])

    # while slots remain, iterate pelas referências escolhendo 1 por vez
    while len(selected_indices) < slots:
        # seleciona a referência com menor rho e que possua membros não selecionados
        min_r = None
        for r in reference_list:
            # count of unselected members
            unselected = [i for i in sorted_per_ref[r] if i not in selected_indices]
            if len(unselected) == 0:
                continue
            if min_r is None or rho[r] < rho[min_r]:
                min_r = r
        
        if min_r is None:
            # nenhuma referência com membros restantes -> escolhe qualquer não-selecionado
            for i in range(len(front)):
                if i not in selected_indices:
                    selected_indices.add(i)
                    break
            continue
        
        # escolha o membro mais próximo não selecionado da referência min_r
        for i in sorted_per_ref[min_r]:
            if i not in selected_indices:
                selected_indices.add(i)
                rho[min_r] += 1
                break

    # map selected_indices (indices relativos à front) aos indivíduos
    selected = [front[i] for i in selected_indices]
    return selected

# ----------------- Crossover/Mutação/Seleção (simples, compatível) -----------------

def tournament(population, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds, k=2):
    """
    Seleção por torneio usando não-dominância e crowding distance.
    """
    cands = random.sample(population, k)
    fronts = fast_nondominated_sort(cands, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
    if len(fronts[0]) == 1:
        winner = fronts[0][0]
    else:
        cd = crowding_distance(fronts[0], task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds)
        winner = max(fronts[0], key=lambda ind: cd[id(ind)])
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

def crowding_distance(front, task_ids, cloud_ids, capacities, local_tasks, deadlines, tasks_global, clouds):
    """
    Calcula a distância de crowding para manter diversidade.
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

# ----------------- Resultado -----------------

def build_result(best, task_ids, cloud_ids, capacities, tasks_global, local_tasks, deadlines, clouds):
    """
    Constrói o resultado final a partir do melhor indivíduo.
    """
    allocation = {}
    for pos, cid in enumerate(best):
        if cid is None:
            continue
        tid = task_ids[pos]
        allocation. setdefault(cid, {})[tid] = -1

    result = {}
    resource_splited = {}

    for cid in allocation:
        proc = management.get_processing_time(capacities[cid], tasks_global, allocation[cid])
        for tid in proc:
            allocation[cid][tid] = proc[tid]
        result[cid] = allocation[cid]
        resource_splited[cid] = management.split_resource(allocation[cid], clouds.clouds[cid], local_tasks)

    return result, resource_splited