#!/usr/bin/python3
# title: LOA.py
# author: Matheus Ramos Esteves
# desc: Implementação simplificada do Lion Optimization Algorithm (LOA)
# interface: mesma assinatura e retorno de utils.GWO.gwo_solution(sw, tasks)

import random
import numpy as np

# --- Funções de fitness (mesmas do GWO original) ---
def F5(x):
    dim  = len(x)
    o = np.sum(100*(x[1:dim]-(x[0:dim-1]**2))**2+(x[0:dim-1]-1)**2)
    return o

def F6(x):
    o=np.sum(abs((x+.5))**2)
    return o

def _fitness(vec, sw):
    """
    Fitness com penalização por violar a capacidade 'sw' e leve incentivo
    para usar a capacidade sem ultrapassar.
    vec = [size, deadline]
    """
    base = F5(vec)

    size = float(vec[0])
    cap_penalty = 0.0
    # penaliza forte overflow de capacidade
    if size > sw:
        # quadrática no excesso para crescer rápido
        cap_penalty += 1e6 * (size - sw)**2

    # (opcional, fraco) penaliza "capacidade ociosa" para tender a usar bem o recurso,
    # mas sem forçar: peso bem menor que o overflow
    if sw > 0 and 0 <= size <= sw:
        slack = (sw - size) / sw
        cap_penalty += 1e2 * (slack**2)

    return base + cap_penalty

# --- LOA (versão compacta, adequada ao contexto do problema) ---
def loa_solution(sw, tasks):
    """
    sw: capacidade (resource budget) da nuvem atual (igual ao usado no GWO).
    tasks: dicionário {task_id: [size, deadline]} como em TOVEC.py.

    Retorna exatamente o mesmo formato do GWO.gwo_solution: [task_id, size, deadline].
    Requer que exista uma função `_fitness(vec, sw)` (vec=[size, deadline]).
    """

    import numpy as np

    # 1) Transformar dicionário em lista, como no GWO
    serv_list = []
    for task in tasks:
        serv_list.append([task, tasks[task][0], tasks[task][1]])

    # --- Pré-filtro de viabilidade: se houver pelo menos uma tarefa <= sw, mantém só as viáveis
    feasible = [rec for rec in serv_list if rec[1] <= sw]  # rec = [task_id, size, deadline]
    if len(feasible) > 0:
        serv_list = feasible

    n = len(serv_list)
    if n == 0:
        return None

    dim = 2  # usamos [size, deadline] como posição

    # Matriz de posições (cada leão corresponde a uma tarefa neste contexto)
    positions = np.zeros((n, dim))
    for j in range(n):
        positions[j, 0] = serv_list[j][1]  # size
        positions[j, 1] = serv_list[j][2]  # deadline

    # 2) Parâmetros LOA (valores compactos, estáveis para nosso uso)
    max_iter = 10
    pride_ratio = 0.8           # proporção de leões em prides (resto são nômades)
    mating_rate = 0.3           # fração de leões que participam do acasalamento
    roaming_prob = 0.3          # probabilidade de nômade vagar
    defense_pressure = 0.5      # força com que o território (melhores) puxa o grupo
    wander_scale = 0.1          # passo de exploração
    eps = 1e-9

    # Utilitário simples de clamping (garante size>=0, deadline>=0)
    def _clamp_inplace(v):
        v[0] = max(0.0, float(v[0]))
        v[1] = max(0.0, float(v[1]))

    # 3) Avaliação inicial (com sw)
    fitness = np.array([_fitness(positions[i, :], sw) for i in range(n)])
    order = np.argsort(fitness)
    positions = positions[order]
    serv_list = [serv_list[i] for i in order]
    fitness = fitness[order]

    best_pos = positions[0].copy()
    best_score = float(fitness[0])

    # 4) Divisão em prides e nômades
    pride_size = max(1, int(pride_ratio * n))
    nomad_size = n - pride_size
    pride = positions[:pride_size, :].copy()
    pride_fit = fitness[:pride_size].copy()
    pride_tasks = serv_list[:pride_size].copy()

    nomads = positions[pride_size:, :].copy()
    nomads_fit = fitness[pride_size:].copy()
    nomad_tasks = serv_list[pride_size:].copy()

    rng = np.random.default_rng()

    # 5) Loop principal do LOA
    for it in range(max_iter):
        # --- Hunting (caça): o pride move-se em direção ao melhor do pride ---
        leader_idx = int(np.argmin(pride_fit))
        leader = pride[leader_idx].copy()

        for i in range(pride.shape[0]):
            if i == leader_idx:
                continue
            # movimento em direção ao líder + pequena aleatoriedade (cercar a presa)
            direction = leader - pride[i]
            step = defense_pressure * direction + wander_scale * rng.normal(size=dim)
            pride[i] = pride[i] + step
            _clamp_inplace(pride[i])

        # líder também se move um pouco exploratoriamente
        pride[leader_idx] = leader + wander_scale * rng.normal(size=dim)
        _clamp_inplace(pride[leader_idx])

        # --- Roaming (vagância): nômades vagam aleatoriamente ---
        for i in range(nomads.shape[0]):
            if rng.random() < roaming_prob:
                nomads[i] = nomads[i] + rng.normal(size=dim)
                _clamp_inplace(nomads[i])

        # --- Mating (acasalamento): mistura genética entre membros do pride ---
        if pride.shape[0] >= 2:
            m_count = max(1, int(mating_rate * pride.shape[0]))
            for _ in range(m_count):
                p1, p2 = rng.choice(pride.shape[0], size=2, replace=False)
                beta = rng.random()
                child = beta * pride[p1] + (1 - beta) * pride[p2]
                # pequena mutação
                child = child + wander_scale * rng.normal(size=dim)
                _clamp_inplace(child)

                # substituir o pior do pride se o filho for melhor
                child_eval = _fitness(child, sw)
                worst_idx = int(np.argmax(pride_fit))
                if child_eval + eps < pride_fit[worst_idx]:
                    pride[worst_idx] = child
                    pride_fit[worst_idx] = child_eval
                    # herdamos a tarefa do melhor dos pais (aproximação para manter mapeamento)
                    better_parent = p1 if _fitness(pride[p1], sw) < _fitness(pride[p2], sw) else p2
                    pride_tasks[worst_idx] = pride_tasks[better_parent]

        # --- Reavaliação (com sw) ---
        pride_fit = np.array([_fitness(pride[i], sw) for i in range(pride.shape[0])])
        nomads_fit = np.array([_fitness(nomads[i], sw) for i in range(nomads.shape[0])]) if nomads.shape[0] else np.array([])

        # --- Territorial takeovers: nômades desafiam piores do pride ---
        if nomads.shape[0] > 0:
            worst_pride_idx = int(np.argmax(pride_fit))
            best_nomad_idx = int(np.argmin(nomads_fit)) if nomads_fit.size > 0 else None
            if best_nomad_idx is not None and nomads_fit[best_nomad_idx] + eps < pride_fit[worst_pride_idx]:
                # troca
                tmp_pos, tmp_fit, tmp_task = pride[worst_pride_idx].copy(), float(pride_fit[worst_pride_idx]), pride_tasks[worst_pride_idx]
                pride[worst_pride_idx], pride_fit[worst_pride_idx], pride_tasks[worst_pride_idx] = (
                    nomads[best_nomad_idx].copy(), float(nomads_fit[best_nomad_idx]), nomad_tasks[best_nomad_idx]
                )
                nomads[best_nomad_idx], nomads_fit[best_nomad_idx], nomad_tasks[best_nomad_idx] = tmp_pos, tmp_fit, tmp_task

        # --- Atualiza melhor global ---
        min_pride_idx = int(np.argmin(pride_fit))
        if pride_fit[min_pride_idx] + eps < best_score:
            best_score = float(pride_fit[min_pride_idx])
            best_pos = pride[min_pride_idx].copy()

    # 6) Seleciona a tarefa cuja posição é mais próxima do melhor vetor encontrado
    def _dist(a, b): 
        return float(np.linalg.norm(a - b))

    best_idx = 0
    best_d = float('inf')
    if nomads.shape[0] > 0:
        full_positions = np.vstack([pride, nomads])
        full_tasks = pride_tasks + nomad_tasks
    else:
        full_positions = pride
        full_tasks = pride_tasks

    for i in range(full_positions.shape[0]):
        d = _dist(full_positions[i], best_pos)
        if d < best_d:
            best_d = d
            best_idx = i

    best_task = full_tasks[best_idx]  # [task_id, size, deadline]

    # OBS: Agora 'sw' influencia diretamente o fitness (penalização),
    # e opcionalmente um termo fraco de "capacidade ociosa" (conforme _fitness).

    return best_task
