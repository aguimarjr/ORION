#!/usr/bin/python3
# title: pareto_plot_3d.py
# author: Matheus Ramos Esteves
# date: 22.11.2025

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sem GUI

# Importa seaborn para estilo visual melhorado
try:
    import seaborn as sns
    sns.set_theme()
    sns.set_style("whitegrid")
    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("[WARNING] Seaborn não encontrado. Instalando estilo matplotlib padrão.")

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap

def save_pareto_plot_3d(population_objs, ids=None, out_dir="system/output/pareto_plots", 
                        prefix="pareto_3d", mark_pareto_front=True, 
                        elevation=25, azimuth=45, figsize=(12, 9)):
    """
    Gera e salva um plot 3D interativo da frente de Pareto.
    
    Args:
        population_objs: lista de tuplas (f1, f2, f3) com os objetivos
        ids: lista de identificadores dos indivíduos (opcional)
        out_dir: diretório de saída
        prefix: prefixo do arquivo
        mark_pareto_front: se True, destaca indivíduos não-dominados
        elevation: ângulo de elevação da câmera (graus)
        azimuth: ângulo azimutal da câmera (graus)
        figsize: tamanho da figura (largura, altura)
    
    Returns:
        str: caminho do arquivo salvo
    """
    if not population_objs:
        print("[PLOT 3D] População vazia, pulando plot.")
        return None
    
    # Garante que diretório existe
    os.makedirs(out_dir, exist_ok=True)
    
    # Extrai coordenadas
    x_coords = np.array([obj[0] for obj in population_objs])  # Latência
    y_coords = np.array([obj[1] for obj in population_objs])  # Violação
    z_coords = np.array([obj[2] for obj in population_objs])  # Desbalanceamento
    
    # Cria figura com alta resolução
    fig = plt.figure(figsize=figsize, dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    
    # Configura estilo seaborn se disponível
    if HAS_SEABORN:
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')
    
    # Identifica frente de Pareto se solicitado
    if mark_pareto_front:
        pareto_indices = get_pareto_front_indices_3d(population_objs)
        non_pareto_indices = [i for i in range(len(population_objs)) if i not in pareto_indices]
        
        # Plota soluções dominadas (cinza claro, menor)
        if non_pareto_indices:
            x_non = x_coords[non_pareto_indices]
            y_non = y_coords[non_pareto_indices]
            z_non = z_coords[non_pareto_indices]
            
            ax.scatter(x_non, y_non, z_non, 
                      c='lightgray', 
                      alpha=0.3, 
                      s=30, 
                      marker='o',
                      label='Soluções Dominadas',
                      edgecolors='gray',
                      linewidths=0.5)
        
        # Plota frente de Pareto (gradiente de cor baseado na latência)
        if pareto_indices:
            x_pareto = x_coords[pareto_indices]
            y_pareto = y_coords[pareto_indices]
            z_pareto = z_coords[pareto_indices]
            
            # Gradiente de cor: azul (melhor) -> vermelho (pior) baseado na latência
            if HAS_SEABORN:
                colors = sns.color_palette("coolwarm", as_cmap=True)(
                    (x_pareto - x_pareto.min()) / (x_pareto.max() - x_pareto.min() + 1e-10)
                )
            else:
                colors = cm.coolwarm(
                    (x_pareto - x_pareto.min()) / (x_pareto.max() - x_pareto.min() + 1e-10)
                )
            
            scatter = ax.scatter(x_pareto, y_pareto, z_pareto,
                               c=colors,
                               s=150,
                               marker='o',
                               edgecolors='darkred',
                               linewidths=2,
                               alpha=0.9,
                               label='Frente de Pareto')
            
            # Conecta pontos da frente (opcional - pode ficar poluído)
            # if len(pareto_indices) <= 20:  # Só se não for muitos pontos
            #     ax.plot_trisurf(x_pareto, y_pareto, z_pareto, alpha=0.1, color='red')
    
    else:
        # Plot simples sem destacar frente
        scatter = ax.scatter(x_coords, y_coords, z_coords,
                           c=x_coords,  # Cor baseada na latência
                           cmap='viridis',
                           s=80,
                           alpha=0.7,
                           edgecolors='black',
                           linewidths=0.5)
        
        # Adiciona barra de cor
        cbar = plt.colorbar(scatter, ax=ax, pad=0.1, shrink=0.8)
        cbar.set_label('Latência Média (s)', fontsize=11, fontweight='bold')
    
    # Labels dos eixos
    ax.set_xlabel('Latência Média (s)', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_ylabel('Taxa de Violação', fontsize=12, fontweight='bold', labelpad=10)
    ax.set_zlabel('Desbalanceamento', fontsize=12, fontweight='bold', labelpad=10)
    
    # Título
    if mark_pareto_front and pareto_indices:
        title = f'Frente de Pareto 3D - NSGA-II\n({len(pareto_indices)} soluções não-dominadas de {len(population_objs)} total)'
    else:
        title = f'Espaço de Objetivos 3D - NSGA-II\n({len(population_objs)} soluções)'
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    
    # Ajusta ângulo de visualização
    ax.view_init(elev=elevation, azim=azimuth)
    
    # Grid mais suave
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Legenda
    if mark_pareto_front:
        ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    
    # Estatísticas no canto
    stats_text = _get_statistics_text(population_objs, pareto_indices if mark_pareto_front else None)
    ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes,
              fontsize=9, verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
              family='monospace')
    
    # Salva figura
    filename = f"{prefix}.png"
    filepath = os.path.join(out_dir, filename)
    plt.tight_layout()
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    print(f"[PLOT 3D] Salvo: {filename}")
    return filepath


def save_pareto_plot_3d_multiple_views(population_objs, out_dir="system/output/pareto_plots",
                                        prefix="pareto_3d_views", mark_pareto_front=True):
    """
    Gera um plot 3D com múltiplas perspectivas (4 ângulos diferentes).
    Útil para análise completa da frente de Pareto.
    
    Args:
        population_objs: lista de tuplas (f1, f2, f3)
        out_dir: diretório de saída
        prefix: prefixo do arquivo
        mark_pareto_front: se True, destaca frente de Pareto
    
    Returns:
        str: caminho do arquivo salvo
    """
    if not population_objs:
        print("[PLOT 3D] População vazia, pulando plot.")
        return None
    
    os.makedirs(out_dir, exist_ok=True)
    
    # Extrai coordenadas
    x_coords = np.array([obj[0] for obj in population_objs])
    y_coords = np.array([obj[1] for obj in population_objs])
    z_coords = np.array([obj[2] for obj in population_objs])
    
    # Identifica frente de Pareto
    pareto_indices = get_pareto_front_indices_3d(population_objs) if mark_pareto_front else []
    non_pareto_indices = [i for i in range(len(population_objs)) if i not in pareto_indices]
    
    # Cria figura com 4 subplots (2x2)
    fig = plt.figure(figsize=(16, 14))
    
    # Diferentes ângulos de visualização
    views = [
        (25, 45, 'Vista Padrão'),
        (15, 135, 'Vista Lateral Esquerda'),
        (45, 225, 'Vista Traseira'),
        (60, 315, 'Vista Superior Direita')
    ]
    
    for idx, (elev, azim, view_name) in enumerate(views, 1):
        ax = fig.add_subplot(2, 2, idx, projection='3d')
        
        # Plota dominadas
        if non_pareto_indices:
            ax.scatter(x_coords[non_pareto_indices], 
                      y_coords[non_pareto_indices], 
                      z_coords[non_pareto_indices],
                      c='lightgray', alpha=0.2, s=20, marker='o')
        
        # Plota frente de Pareto
        if pareto_indices:
            x_pareto = x_coords[pareto_indices]
            y_pareto = y_coords[pareto_indices]
            z_pareto = z_coords[pareto_indices]
            
            if HAS_SEABORN:
                colors = sns.color_palette("coolwarm", as_cmap=True)(
                    (x_pareto - x_pareto.min()) / (x_pareto.max() - x_pareto.min() + 1e-10)
                )
            else:
                colors = cm.coolwarm(
                    (x_pareto - x_pareto.min()) / (x_pareto.max() - x_pareto.min() + 1e-10)
                )
            
            ax.scatter(x_pareto, y_pareto, z_pareto,
                      c=colors, s=100, marker='o',
                      edgecolors='darkred', linewidths=1.5, alpha=0.9)
        
        # Configurações
        ax.set_xlabel('Latência (s)', fontsize=10, fontweight='bold')
        ax.set_ylabel('Violação', fontsize=10, fontweight='bold')
        ax.set_zlabel('Desbalanceamento', fontsize=10, fontweight='bold')
        ax.set_title(view_name, fontsize=11, fontweight='bold')
        ax.view_init(elev=elev, azim=azim)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Título geral
    fig.suptitle(f'Frente de Pareto 3D - Múltiplas Perspectivas\n'
                 f'{len(pareto_indices)} soluções não-dominadas de {len(population_objs)} total',
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Salva
    filename = f"{prefix}.png"
    filepath = os.path.join(out_dir, filename)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    
    print(f"[PLOT 3D] Múltiplas vistas salvas: {filename}")
    return filepath


def save_pareto_plot_3d_interactive(population_objs, out_dir="system/output/pareto_plots",
                                     prefix="pareto_3d_interactive", mark_pareto_front=True):
    """
    Gera um HTML interativo com plot 3D usando Plotly (se disponível).
    Permite rotação, zoom e hover com informações.
    
    Args:
        population_objs: lista de tuplas (f1, f2, f3)
        out_dir: diretório de saída
        prefix: prefixo do arquivo
        mark_pareto_front: se True, destaca frente de Pareto
    
    Returns:
        str: caminho do arquivo HTML salvo (ou None se plotly não disponível)
    """
    #try:
    #    import plotly.graph_objects as go
    #    from plotly.subplots import make_subplots
    #except ImportError:
    #    print("[PLOT 3D] Plotly não disponível. Instale com: pip install plotly")
    #    return None
    
    if not population_objs:
        print("[PLOT 3D] População vazia, pulando plot.")
        return None
    
    os.makedirs(out_dir, exist_ok=True)
    
    # Extrai coordenadas
    x_coords = [obj[0] for obj in population_objs]
    y_coords = [obj[1] for obj in population_objs]
    z_coords = [obj[2] for obj in population_objs]
    
    # Identifica frente de Pareto
    pareto_indices = get_pareto_front_indices_3d(population_objs) if mark_pareto_front else []
    non_pareto_indices = [i for i in range(len(population_objs)) if i not in pareto_indices]
    
    # Cria figura
    fig = go.Figure()
    
    # Plota soluções dominadas
    if non_pareto_indices:
        fig.add_trace(go.Scatter3d(
            x=[x_coords[i] for i in non_pareto_indices],
            y=[y_coords[i] for i in non_pareto_indices],
            z=[z_coords[i] for i in non_pareto_indices],
            mode='markers',
            name='Dominadas',
            marker=dict(
                size=4,
                color='lightgray',
                opacity=0.3,
                line=dict(color='gray', width=0.5)
            ),
            hovertemplate='<b>Dominada</b><br>' +
                         'Latência: %{x:.3f}s<br>' +
                         'Violação: %{y:.2%}<br>' +
                         'Desbalanceamento: %{z:.3f}<extra></extra>'
        ))
    
    # Plota frente de Pareto
    if pareto_indices:
        x_pareto = [x_coords[i] for i in pareto_indices]
        y_pareto = [y_coords[i] for i in pareto_indices]
        z_pareto = [z_coords[i] for i in pareto_indices]
        
        fig.add_trace(go.Scatter3d(
            x=x_pareto,
            y=y_pareto,
            z=z_pareto,
            mode='markers',
            name='Frente de Pareto',
            marker=dict(
                size=8,
                color=x_pareto,  # Cor baseada na latência
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Latência (s)", x=1.1),
                opacity=0.9,
                line=dict(color='darkred', width=2)
            ),
            hovertemplate='<b>Pareto</b><br>' +
                         'Latência: %{x:.3f}s<br>' +
                         'Violação: %{y:.2%}<br>' +
                         'Desbalanceamento: %{z:.3f}<extra></extra>'
        ))
    
    # Layout
    fig.update_layout(
        title=dict(
            text=f'Frente de Pareto 3D Interativa - NSGA-II<br>' +
                 f'<sub>{len(pareto_indices)} não-dominadas de {len(population_objs)} total</sub>',
            font=dict(size=18, family='Arial Black')
        ),
        scene=dict(
            xaxis=dict(title='Latência Média (s)', backgroundcolor='rgb(230, 230,230)'),
            yaxis=dict(title='Taxa de Violação', backgroundcolor='rgb(230, 230,230)'),
            zaxis=dict(title='Desbalanceamento', backgroundcolor='rgb(230, 230,230)'),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.3)
            )
        ),
        showlegend=True,
        legend=dict(x=0.7, y=0.9),
        hovermode='closest',
        template='plotly_white'
    )
    
    # Salva como HTML
    filename = f"{prefix}.html"
    filepath = os.path.join(out_dir, filename)
    fig.write_html(filepath)
    
    print(f"[PLOT 3D] Plot interativo salvo: {filename}")
    print(f"[PLOT 3D] Abra o arquivo em um navegador para interagir!")
    return filepath


def get_pareto_front_indices_3d(population_objs):
    """
    Identifica índices dos indivíduos na frente de Pareto 3D.
    Otimizado para performance.
    
    Args:
        population_objs: lista de tuplas (f1, f2, f3)
    
    Returns:
        list: índices dos indivíduos não-dominados
    """
    n = len(population_objs)
    is_dominated = [False] * n
    
    for i in range(n):
        if is_dominated[i]:
            continue
        
        objs_i = population_objs[i]
        
        for j in range(i + 1, n):  # Otimização: só compara com posteriores
            if is_dominated[j]:
                continue
            
            objs_j = population_objs[j]
            
            # Verifica dominância i -> j
            i_dominates_j = all(objs_i[k] <= objs_j[k] for k in range(3)) and \
                           any(objs_i[k] < objs_j[k] for k in range(3))
            
            # Verifica dominância j -> i
            j_dominates_i = all(objs_j[k] <= objs_i[k] for k in range(3)) and \
                           any(objs_j[k] < objs_i[k] for k in range(3))
            
            if i_dominates_j:
                is_dominated[j] = True
            elif j_dominates_i:
                is_dominated[i] = True
                break
    
    return [i for i in range(n) if not is_dominated[i]]


def _get_statistics_text(population_objs, pareto_indices=None):
    """Gera texto com estatísticas para exibir no plot."""
    stats = []
    stats.append(f"População: {len(population_objs)}")
    
    if pareto_indices:
        stats.append(f"Pareto: {len(pareto_indices)}")
        
        # Estatísticas da frente
        pareto_objs = [population_objs[i] for i in pareto_indices]
        lat_vals = [o[0] for o in pareto_objs]
        viol_vals = [o[1] for o in pareto_objs]
        imbal_vals = [o[2] for o in pareto_objs]
        
        stats.append(f"")
        stats.append(f"Latência:")
        stats.append(f"  min: {min(lat_vals):.3f}s")
        stats.append(f"  max: {max(lat_vals):.3f}s")
        stats.append(f"Violação:")
        stats.append(f"  min: {min(viol_vals):.1%}")
        stats.append(f"  max: {max(viol_vals):.1%}")
    
    return '\n'.join(stats)


# Função auxiliar para gerar todos os plots 3D de uma vez
def save_all_3d_plots(population_objs, out_dir="system/output/pareto_plots",
                      prefix="pareto_3d", mark_pareto_front=True):
    """
    Gera todos os tipos de plots 3D disponíveis.
    
    Returns:
        dict: dicionário com paths dos arquivos gerados
    """
    files = {}
    
    # Plot 3D padrão
    file1 = save_pareto_plot_3d(population_objs, out_dir=out_dir, 
                                prefix=f"{prefix}_single", 
                                mark_pareto_front=mark_pareto_front)
    if file1:
        files['single_view'] = file1
    
    # Plot com múltiplas vistas
    file2 = save_pareto_plot_3d_multiple_views(population_objs, out_dir=out_dir,
                                               prefix=f"{prefix}_multi",
                                               mark_pareto_front=mark_pareto_front)
    if file2:
        files['multiple_views'] = file2
    
    # Plot interativo (se plotly disponível)
    file3 = save_pareto_plot_3d_interactive(population_objs, out_dir=out_dir,
                                           prefix=f"{prefix}_interactive",
                                           mark_pareto_front=mark_pareto_front)
    if file3:
        files['interactive'] = file3
    
    return files