#!/usr/bin/python3
# title: pareto_manager.py 
# author: Matheus Ramos Esteves
# date: 22.11.2025

import os
import json
import threading
from datetime import datetime
from .pareto_plot_2d import save_all_2d_combinations, save_pareto_dashboard
from .pareto_plot_3d import save_all_3d_plots

class ParetoPlotManager:
    """
    Gerenciador inteligente de plots de Pareto 2D e 3D.
    Acumula dados e gera plots apenas quando necessário.
    """
    
    def __init__(self, output_dir="system/output/pareto_plots", 
                 plot_frequency=10, max_history=100, 
                 plot_2d=True, plot_3d=True, plot_dashboard=True,
                 plot_3d_multiview=False, plot_3d_interactive=False):
        """
        Args:
            output_dir: diretório para salvar plots
            plot_frequency: gera plot a cada N execuções
            max_history: máximo de execuções a manter no histórico
            plot_2d: se True, gera plots 2D individuais
            plot_3d: se True, gera plot 3D padrão
            plot_dashboard: se True, gera dashboard 2D com todos os eixos
            plot_3d_multiview: se True, gera plot 3D com múltiplas perspectivas
            plot_3d_interactive: se True, gera plot 3D interativo HTML (requer plotly)
        """
        self.output_dir = output_dir
        self.plot_frequency = plot_frequency
        self.max_history = max_history
        self.plot_2d = plot_2d
        self.plot_3d = plot_3d
        self.plot_dashboard = plot_dashboard
        self.plot_3d_multiview = plot_3d_multiview
        self.plot_3d_interactive = plot_3d_interactive
        
        self.execution_count = 0
        self.history = []
        self.lock = threading.Lock()
        
        os.makedirs(output_dir, exist_ok=True)
        self.log_file = os.path.join(output_dir, "pareto_history.jsonl")
    
    def add_execution(self, population_objs, metadata=None, force_plot=False):
        """
        Adiciona uma execução ao histórico.
        
        Args:
            population_objs: lista de tuplas (f1, f2, f3) dos objetivos
            metadata: dict com informações adicionais (opcional)
            force_plot: se True, força geração de plot imediatamente
        
        Returns:
            dict: informações sobre plots gerados
        """
        with self.lock:
            self.execution_count += 1
            timestamp = datetime.utcnow().isoformat()
            
            entry = {
                'execution': self.execution_count,
                'timestamp': timestamp,
                'objectives': population_objs,
                'metadata': metadata or {}
            }
            self.history.append(entry)
            
            if len(self.history) > self.max_history:
                self.history.pop(0)
            
            self._append_log(entry)
            
            should_plot = force_plot or (self.execution_count % self.plot_frequency == 0)
            
            result = {
                'plotted': False,
                'files': []
            }
            
            if should_plot:
                result = self._generate_plots(population_objs, self.execution_count)
                result['plotted'] = True
            
            return result
    
    def _generate_plots(self, population_objs, execution_num):
        """Gera os plots conforme configuração."""
        result = {'files': []}
        prefix = f"nsga2_exec{execution_num}"
        
        try:
            # ===== PLOTS 2D =====
            if self.plot_2d:
                files_2d = save_all_2d_combinations(
                    population_objs,
                    out_dir=self.output_dir,
                    prefix=prefix,
                    mark_pareto_front=True
                )
                result['files'].extend(files_2d)
                # print(f"[PARETO] Plots 2D: {len(files_2d)} arquivos")
            
            if self.plot_dashboard:
                dashboard_file = save_pareto_dashboard(
                    population_objs,
                    out_dir=self.output_dir,
                    prefix=f"{prefix}_dashboard"
                )
                if dashboard_file:
                    result['files'].append(dashboard_file)
                    # print(f"[PARETO] Dashboard 2D gerado")
            
            # ===== PLOTS 3D =====
            if self.plot_3d or self.plot_3d_multiview or self.plot_3d_interactive:
                from .pareto_plot_3d import (save_pareto_plot_3d, 
                                             save_pareto_plot_3d_multiple_views,
                                             save_pareto_plot_3d_interactive)
                
                # Plot 3D padrão
                if self.plot_3d:
                    file_3d = save_pareto_plot_3d(
                        population_objs,
                        out_dir=self.output_dir,
                        prefix=f"{prefix}_3d",
                        mark_pareto_front=True
                    )
                    if file_3d:
                        result['files'].append(file_3d)
                
                # Plot 3D com múltiplas vistas
                if self.plot_3d_multiview:
                    file_3d_multi = save_pareto_plot_3d_multiple_views(
                        population_objs,
                        out_dir=self.output_dir,
                        prefix=f"{prefix}_3d_multiview",
                        mark_pareto_front=True
                    )
                    if file_3d_multi:
                        result['files'].append(file_3d_multi)
                
                # Plot 3D interativo
                if self.plot_3d_interactive:
                    file_3d_html = save_pareto_plot_3d_interactive(
                        population_objs,
                        out_dir=self.output_dir,
                        prefix=f"{prefix}_3d_interactive",
                        mark_pareto_front=True
                    )
                    if file_3d_html:
                        result['files'].append(file_3d_html)
            
            # print(f"[PARETO] Total: {len(result['files'])} arquivos (execução #{execution_num})")
            
        except Exception as e:
            # print(f"[PARETO] Erro ao gerar plots: {e}")
            pass
            import traceback
            traceback.print_exc()
        
        return result
    
    def _append_log(self, entry):
        """Salva entrada no arquivo de log (formato JSONL)."""
        try:
            objs = entry['objectives']
            if not objs:
                return
                
            log_entry = {
                'execution': entry['execution'],
                'timestamp': entry['timestamp'],
                'population_size': len(objs),
                'objectives_stats': {
                    'avg_latency': {
                        'min': min(o[0] for o in objs),
                        'max': max(o[0] for o in objs),
                        'avg': sum(o[0] for o in objs) / len(objs)
                    },
                    'violation_rate': {
                        'min': min(o[1] for o in objs),
                        'max': max(o[1] for o in objs),
                        'avg': sum(o[1] for o in objs) / len(objs)
                    },
                    'imbalance': {
                        'min': min(o[2] for o in objs),
                        'max': max(o[2] for o in objs),
                        'avg': sum(o[2] for o in objs) / len(objs)
                    }
                },
                'metadata': entry['metadata']
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            # print(f"[PARETO] Erro ao salvar log: {e}")
            pass
    
    def generate_summary_plots(self):
        """Gera plots resumo com todas as execuções acumuladas."""
        if not self.history:
            # print("[PARETO] Nenhuma execução no histórico.")
            return {'files': []}
        
        all_objs = []
        for entry in self.history:
            all_objs.extend(entry['objectives'])
        
        # print(f"[PARETO] Gerando plots resumo com {len(all_objs)} indivíduos...")
        
        result = {'files': []}
        
        try:
            # Plots 2D
            if self.plot_2d:
                files_2d = save_all_2d_combinations(
                    all_objs,
                    out_dir=self.output_dir,
                    prefix="nsga2_summary_all",
                    mark_pareto_front=True
                )
                result['files'].extend(files_2d)
            
            if self.plot_dashboard:
                dashboard_file = save_pareto_dashboard(
                    all_objs,
                    out_dir=self.output_dir,
                    prefix="nsga2_summary_dashboard_all"
                )
                if dashboard_file:
                    result['files'].append(dashboard_file)
            
            # Plots 3D
            if self.plot_3d or self.plot_3d_multiview or self.plot_3d_interactive:
                files_3d = save_all_3d_plots(
                    all_objs,
                    out_dir=self.output_dir,
                    prefix="nsga2_summary_all",
                    mark_pareto_front=True
                )
                result['files'].extend(files_3d.values())
            
            # print(f"[PARETO] Plots resumo: {len(result['files'])} arquivos")
            
        except Exception as e:
            # print(f"[PARETO] Erro ao gerar plots resumo: {e}")
            pass
            import traceback
            traceback.print_exc()
        
        return result
    
    def get_statistics(self):
        """Retorna estatísticas do histórico."""
        if not self.history:
            return None
        
        return {
            'total_executions': self.execution_count,
            'history_size': len(self.history),
            'plot_frequency': self.plot_frequency,
            'last_execution': self.history[-1]['timestamp'] if self.history else None,
            'plot_2d_enabled': self.plot_2d,
            'plot_3d_enabled': self.plot_3d,
            'plot_dashboard_enabled': self.plot_dashboard,
            'plot_3d_multiview_enabled': self.plot_3d_multiview,
            'plot_3d_interactive_enabled': self.plot_3d_interactive
        }


_manager = None

def get_pareto_manager(**kwargs):
    """Retorna instância singleton do gerenciador."""
    global _manager
    if _manager is None:
        _manager = ParetoPlotManager(**kwargs)
    return _manager