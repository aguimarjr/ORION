#!/usr/bin/python3
# title: pareto_plot_2d.py
# author: Matheus Ramos Esteves
# date: 22.11.2025
# modified: Refatorado para objetivos diretos (custo e taxa de sucesso)

import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sem GUI para ambientes servidor

def save_pareto_plot_2d(population_objs, ids=None, out_dir="system/output/pareto_plots", 
                        prefix="pareto_2d", obj_x=0, obj_y=1, 
                        labels=None, title=None, mark_pareto_front=True):
    """
    Gera e salva um plot 2D da frente de Pareto.
    
    Args:
        population_objs: lista de tuplas (custo, taxa_falha) com os objetivos
        ids: lista de identificadores dos indivíduos (opcional)
        out_dir: diretório de saída
        prefix: prefixo do arquivo
        obj_x: índice do objetivo para eixo X (0=custo, 1=taxa_falha)
        obj_y: índice do objetivo para eixo Y
        labels: dict com labels dos eixos, ex: {0: 'Custo Total ($)', 1: 'Taxa de Falha'}
        title: título do plot (opcional)
        mark_pareto_front: se True, destaca indivíduos não-dominados
    
    Returns:
        str: caminho do arquivo salvo
    """
    if not population_objs:
        # print("[PLOT 2D] População vazia, pulando plot.")
        return None
    
    # Garante que diretório existe
    os.makedirs(out_dir, exist_ok=True)
    
    # Labels padrão para os novos objetivos
    default_labels = {
        0: 'Custo Monetário Total ($)',
        1: 'Taxa de Falha (%)'
    }
    labels = labels or default_labels
    
    # Extrai coordenadas
    x_coords = [obj[obj_x] for obj in population_objs]
    y_coords = [obj[obj_y] * 100 if obj_y == 1 else obj[obj_y] for obj in population_objs]  # Converte taxa para %
    
    # Cria figura
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Identifica frente de Pareto se solicitado
    if mark_pareto_front:
        pareto_indices = get_pareto_front_indices_2d(population_objs)
        non_pareto_indices = [i for i in range(len(population_objs)) if i not in pareto_indices]
        
        # Plota não-dominados
        if non_pareto_indices:
            x_non = [x_coords[i] for i in non_pareto_indices]
            y_non = [y_coords[i] for i in non_pareto_indices]
            ax.scatter(x_non, y_non, c='lightgray', alpha=0.5, s=50, 
                      label='Soluções Dominadas', zorder=1)
        
        # Plota frente de Pareto
        if pareto_indices:
            x_pareto = [x_coords[i] for i in pareto_indices]
            y_pareto = [y_coords[i] for i in pareto_indices]
            
            # Ordena pontos para desenhar linha conectando a frente
            sorted_pairs = sorted(zip(x_pareto, y_pareto), key=lambda p: p[0])
            x_sorted = [p[0] for p in sorted_pairs]
            y_sorted = [p[1] for p in sorted_pairs]
            
            # Linha conectando a frente
            ax.plot(x_sorted, y_sorted, 'r--', alpha=0.4, linewidth=2, zorder=2)
            
            # Pontos da frente
            ax.scatter(x_sorted, y_sorted, c='red', s=120, marker='o',
                      edgecolors='darkred', linewidths=2,
                      label='Frente de Pareto (Ótimos)', zorder=3)
            
            # Destaca melhor custo e melhor taxa de sucesso
            best_cost_idx = x_sorted.index(min(x_sorted))
            best_success_idx = y_sorted.index(min(y_sorted))
            
            ax.scatter([x_sorted[best_cost_idx]], [y_sorted[best_cost_idx]], 
                      c='gold', s=200, marker='*', edgecolors='black', linewidths=2,
                      label='Menor Custo', zorder=4)
            
            ax.scatter([x_sorted[best_success_idx]], [y_sorted[best_success_idx]], 
                      c='lime', s=200, marker='*', edgecolors='black', linewidths=2,
                      label='Maior Taxa de Sucesso', zorder=4)
    else:
        # Plot simples sem destacar frente
        ax.scatter(x_coords, y_coords, c='blue', alpha=0.6, s=60)
    
    # Configurações do plot
    xlabel = labels.get(obj_x, f'Objetivo {obj_x}')
    ylabel = labels.get(obj_y, f'Objetivo {obj_y}')
    
    ax.set_xlabel(xlabel, fontsize=13, fontweight='bold')
    ax.set_ylabel(ylabel, fontsize=13, fontweight='bold')
    
    if title:
        ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    else:
        ax.set_title(f'Frente de Pareto: Trade-off Custo vs Taxa de Sucesso',
                    fontsize=15, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
    
    if mark_pareto_front:
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
    
    # Adiciona anotações estatísticas
    stats_text = f'População: {len(population_objs)} soluções'
    if mark_pareto_front and pareto_indices:
        stats_text += f'\nFrente de Pareto: {len(pareto_indices)} soluções não-dominadas'
        
        # Estatísticas da frente de Pareto
        costs_pareto = [population_objs[i][0] for i in pareto_indices]
        failures_pareto = [population_objs[i][1] * 100 for i in pareto_indices]
        
        stats_text += f'\n\nCusto: ${min(costs_pareto):.2f} - ${max(costs_pareto):.2f}'
        stats_text += f'\nSucesso: {100-max(failures_pareto):.1f}% - {100-min(failures_pareto):.1f}%'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=10, verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8, edgecolor='black'))
    
    # Adiciona região de interesse (baixo custo + alta taxa de sucesso)
    if mark_pareto_front and pareto_indices and len(x_coords) > 0:
        min_cost = min(x_coords)
        max_cost = max(x_coords)
        min_fail = min(y_coords)
        
        # Destaca região "ideal" (canto inferior esquerdo)
        ideal_region = plt.Rectangle(
            (min_cost, min_fail), 
            (max_cost - min_cost) * 0.3, 
            (max(y_coords) - min_fail) * 0.3,
            alpha=0.1, facecolor='green', edgecolor='darkgreen', 
            linestyle='--', linewidth=2, zorder=0
        )
        ax.add_patch(ideal_region)
        ax.text(min_cost + (max_cost - min_cost) * 0.15, 
               min_fail + (max(y_coords) - min_fail) * 0.15,
               'Região\nIdeal', fontsize=9, ha='center', color='darkgreen',
               fontweight='bold', alpha=0.7)
    
    # Salva figura
    filename = f"{prefix}_custo_vs_sucesso.png"
    filepath = os.path.join(out_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=200, bbox_inches='tight')
    plt.close(fig)
    
    return filepath


def save_all_2d_combinations(population_objs, out_dir="system/output/pareto_plots",
                              prefix="pareto_2d", mark_pareto_front=True):
    """
    Gera plot 2D para os 2 objetivos (agora só há uma combinação possível).
    
    Args:
        population_objs: lista de tuplas (custo, taxa_falha)
        out_dir: diretório de saída
        prefix: prefixo dos arquivos
        mark_pareto_front: se True, destaca frente de Pareto
    
    Returns:
        list: lista de caminhos dos arquivos salvos
    """
    if not population_objs:
        return []
    
    num_objectives = len(population_objs[0])
    
    if num_objectives != 2:
        print(f"[AVISO] Esperado 2 objetivos, recebido {num_objectives}")
    
    labels = {
        0: 'Custo Monetário Total ($)',
        1: 'Taxa de Falha (%)'
    }
    
    # Para 2 objetivos, só existe uma combinação: obj0 vs obj1
    filepath = save_pareto_plot_2d(
        population_objs,
        out_dir=out_dir,
        prefix=prefix,
        obj_x=0,
        obj_y=1,
        labels=labels,
        mark_pareto_front=mark_pareto_front
    )
    
    if filepath:
        print(f"[PLOT 2D] Salvo: {os.path.basename(filepath)}")
        return [filepath]
    
    return []


def save_pareto_dashboard(population_objs, out_dir="system/output/pareto_plots",
                          prefix="pareto_dashboard", algorithm_name="NSGA-II"):
    """
    Gera um dashboard com análise detalhada da frente de Pareto para 2 objetivos.
    
    Args:
        population_objs: lista de tuplas (custo, taxa_falha)
        out_dir: diretório de saída
        prefix: prefixo do arquivo
        algorithm_name: nome do algoritmo para título
    
    Returns:
        str: caminho do arquivo salvo
    """
    if not population_objs:
        print("[DASHBOARD] População vazia, pulando dashboard.")
        return None
    
    os.makedirs(out_dir, exist_ok=True)
    
    # Identifica frente de Pareto
    pareto_indices = get_pareto_front_indices_2d(population_objs)
    
    # Cria figura com subplots
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    fig.suptitle(f'Dashboard de Análise - {algorithm_name}: Custo vs Taxa de Sucesso', 
                 fontsize=18, fontweight='bold')
    
    # 1. Plot principal: Frente de Pareto
    ax1 = fig.add_subplot(gs[0, :2])
    
    costs = [obj[0] for obj in population_objs]
    failures = [obj[1] * 100 for obj in population_objs]
    
    # Soluções dominadas
    non_pareto = [i for i in range(len(population_objs)) if i not in pareto_indices]
    if non_pareto:
        ax1.scatter([costs[i] for i in non_pareto], 
                   [failures[i] for i in non_pareto],
                   c='lightblue', alpha=0.4, s=60, label='Dominadas', zorder=1)
    
    # Frente de Pareto
    if pareto_indices:
        pareto_costs = [costs[i] for i in pareto_indices]
        pareto_failures = [failures[i] for i in pareto_indices]
        
        sorted_pairs = sorted(zip(pareto_costs, pareto_failures), key=lambda p: p[0])
        x_sorted = [p[0] for p in sorted_pairs]
        y_sorted = [p[1] for p in sorted_pairs]
        
        ax1.plot(x_sorted, y_sorted, 'r--', alpha=0.4, linewidth=2, zorder=2)
        ax1.scatter(x_sorted, y_sorted, c='red', s=120, marker='o',
                   edgecolors='darkred', linewidths=2,
                   label='Frente de Pareto', zorder=3)
    
    ax1.set_xlabel('Custo Monetário Total ($)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Taxa de Falha (%)', fontsize=12, fontweight='bold')
    ax1.set_title('Frente de Pareto: Trade-off Custo vs Sucesso', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='best', fontsize=10)
    
    # 2.  Histograma de Custos
    ax2 = fig.add_subplot(gs[0, 2])
    ax2.hist(costs, bins=20, color='steelblue', alpha=0.7, edgecolor='black')
    if pareto_indices:
        pareto_costs = [costs[i] for i in pareto_indices]
        ax2.hist(pareto_costs, bins=15, color='red', alpha=0.5, 
                edgecolor='darkred', label='Pareto')
    ax2.set_xlabel('Custo ($)', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Frequência', fontsize=10, fontweight='bold')
    ax2.set_title('Distribuição de Custos', fontsize=11)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Histograma de Taxa de Sucesso
    ax3 = fig.add_subplot(gs[1, 0])
    success_rates = [(1 - obj[1]) * 100 for obj in population_objs]
    ax3.hist(success_rates, bins=20, color='green', alpha=0.7, edgecolor='black')
    if pareto_indices:
        pareto_success = [(1 - population_objs[i][1]) * 100 for i in pareto_indices]
        ax3.hist(pareto_success, bins=15, color='red', alpha=0.5,
                edgecolor='darkred', label='Pareto')
    ax3.set_xlabel('Taxa de Sucesso (%)', fontsize=10, fontweight='bold')
    ax3.set_ylabel('Frequência', fontsize=10, fontweight='bold')
    ax3.set_title('Distribuição de Taxa de Sucesso', fontsize=11)
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Box Plot Comparativo
    ax4 = fig.add_subplot(gs[1, 1])
    
    pareto_costs = [costs[i] for i in pareto_indices] if pareto_indices else []
    non_pareto_costs = [costs[i] for i in non_pareto] if non_pareto else []
    
    box_data = []
    labels_box = []
    if pareto_costs:
        box_data.append(pareto_costs)
        labels_box.append('Pareto')
    if non_pareto_costs:
        box_data.append(non_pareto_costs)
        labels_box.append('Dominadas')
    
    if box_data:
        bp = ax4.boxplot(box_data, labels=labels_box, patch_artist=True)
        for patch, color in zip(bp['boxes'], ['red', 'lightblue']):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
    
    ax4.set_ylabel('Custo ($)', fontsize=10, fontweight='bold')
    ax4.set_title('Comparação de Custos', fontsize=11)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # 5. Estatísticas Textuais
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    
    stats_lines = [
        "=== ESTATÍSTICAS ===\n",
        f"População Total: {len(population_objs)}",
        f"Frente de Pareto: {len(pareto_indices)}\n",
        "--- CUSTO ---",
        f"Média: ${sum(costs)/len(costs):.2f}",
        f"Mínimo: ${min(costs):.2f}",
        f"Máximo: ${max(costs):.2f}\n",
        "--- TAXA DE SUCESSO ---",
        f"Média: {sum(success_rates)/len(success_rates):.1f}%",
        f"Máxima: {max(success_rates):.1f}%",
        f"Mínima: {min(success_rates):1f}%\n"
    ]
    
    if pareto_indices:
        pareto_costs = [costs[i] for i in pareto_indices]
        pareto_success = [(1 - population_objs[i][1]) * 100 for i in pareto_indices]
        stats_lines.extend([
            "--- PARETO ---",
            f"Custo: ${min(pareto_costs):.2f} - ${max(pareto_costs):.2f}",
            f"Sucesso: {min(pareto_success):.1f}% - {max(pareto_success):.1f}%"
        ])
    
    stats_text = '\n'.join(stats_lines)
    ax5.text(0.1, 0.9, stats_text, transform=ax5.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Salva
    filename = f"{prefix}.png"
    filepath = os.path.join(out_dir, filename)
    plt.savefig(filepath, dpi=200, bbox_inches='tight')
    plt.close(fig)
    
    print(f"[DASHBOARD] Salvo: {filename}")
    return filepath


def get_pareto_front_indices_2d(population_objs):
    """
    Identifica índices dos indivíduos na frente de Pareto 2D.
    
    Para 2 objetivos a minimizar: (custo, taxa_falha)
    
    Args:
        population_objs: lista de tuplas (custo, taxa_falha)
    
    Returns:
        list: índices dos indivíduos não-dominados
    """
    n = len(population_objs)
    is_dominated = [False] * n
    
    for i in range(n):
        if is_dominated[i]:
            continue
        for j in range(n):
            if i == j or is_dominated[j]:
                continue
            
            # Verifica dominância: j domina i se é melhor ou igual em ambos
            # e estritamente melhor em pelo menos um
            cost_i, fail_i = population_objs[i]
            cost_j, fail_j = population_objs[j]
            
            better_or_equal = (cost_j <= cost_i) and (fail_j <= fail_i)
            strictly_better = (cost_j < cost_i) or (fail_j < fail_i)
            
            if better_or_equal and strictly_better:
                is_dominated[i] = True
                break
    
    return [i for i in range(n) if not is_dominated[i]]


# Mantém compatibilidade com código antigo (3 objetivos)
def get_pareto_front_indices(population_objs, obj_x, obj_y):
    """
    DEPRECATED: Mantido para compatibilidade. 
    Use get_pareto_front_indices_2d() para 2 objetivos.
    """
    print("[AVISO] Função get_pareto_front_indices() está deprecated.  Use get_pareto_front_indices_2d()")
    return get_pareto_front_indices_2d(population_objs)


def get_pareto_front_indices_3d(population_objs):
    """
    DEPRECATED: Não aplicável para 2 objetivos.
    Mantido apenas para compatibilidade com código legado.
    """
    print("[AVISO] get_pareto_front_indices_3d() não aplicável para 2 objetivos.")
    return get_pareto_front_indices_2d(population_objs)