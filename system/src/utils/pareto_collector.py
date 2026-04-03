#!/usr/bin/python3
# title: pareto_collector.py
# author: Matheus Ramos Esteves
# date: 2025

class ParetoCollector:
    """
    Singleton para coletar objetivos da população ao longo da simulação
    e gerar plots apenas ao final. 
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ParetoCollector, cls).__new__(cls)
            cls._instance. data = {
                'nsga2': [],
                'nsga3': [],
                'pso': []
            }
            cls._instance.execution_counts = {
                'nsga2': 0,
                'nsga3': 0,
                'pso': 0
            }
        return cls._instance
    
    def add_execution(self, algorithm, population_objs):
        """
        Adiciona dados de uma execução do algoritmo. 
        
        Args:
            algorithm: 'nsga2', 'nsga3' ou 'pso'
            population_objs: lista de tuplas (custo, taxa_falha)
        """
        if algorithm not in self.data:
            print(f"[AVISO] Algoritmo desconhecido: {algorithm}")
            return
        
        self.data[algorithm]. extend(population_objs)
        self.execution_counts[algorithm] += 1
        
        # print(f"[COLLECTOR] {algorithm. upper()}: {len(population_objs)} soluções coletadas "
        #       f"(execução #{self.execution_counts[algorithm]})")
    
    def get_all_data(self, algorithm):
        """Retorna todos os dados coletados para um algoritmo."""
        return self. data. get(algorithm, [])
    
    def get_execution_count(self, algorithm):
        """Retorna quantas vezes o algoritmo foi executado."""
        return self.execution_counts.get(algorithm, 0)
    
    def clear(self, algorithm=None):
        """Limpa dados coletados (de um algoritmo específico ou todos)."""
        if algorithm:
            self.data[algorithm] = []
            self.execution_counts[algorithm] = 0
        else:
            for alg in self.data:
                self.data[alg] = []
                self.execution_counts[alg] = 0
    
    def generate_final_plots(self, out_dir="system/output/pareto_plots"):
        """
        Gera plots finais consolidados para todos os algoritmos executados.
        """
        from scheduler.include.pareto_plot_2d import save_pareto_plot_2d, save_pareto_dashboard
        import os
        
        os.makedirs(out_dir, exist_ok=True)
        
        # print("\n" + "="*60)
        # print("GERANDO PLOTS FINAIS DA FRENTE DE PARETO")
        # print("="*60)
        
        algorithm_names = {
            'nsga2': 'NSGA-II',
            'nsga3': 'NSGA-III',
            'pso': 'PSO Multi-objetivo'
        }
        
        generated_files = []
        
        for alg_key, alg_name in algorithm_names.items():
            data = self.get_all_data(alg_key)
            exec_count = self.get_execution_count(alg_key)
            
            if not data:
                # print(f"\n[{alg_name}] Nenhum dado coletado, pulando plots.")
                continue
            
            # print(f"\n[{alg_name}] Gerando plots com {len(data)} soluções de {exec_count} execuções...")
            
            try:
                # Plot individual
                plot_file = save_pareto_plot_2d(
                    data,
                    out_dir=out_dir,
                    prefix=f"{alg_key}_final",
                    mark_pareto_front=True
                )
                
                if plot_file:
                    generated_files.append(plot_file)
                    # print(f"  ✓ Plot individual: {os.path.basename(plot_file)}")
                
                # Dashboard completo
                dashboard_file = save_pareto_dashboard(
                    data,
                    out_dir=out_dir,
                    prefix=f"{alg_key}_dashboard_final",
                    algorithm_name=f"{alg_name} (Consolidado)"
                )
                
                if dashboard_file:
                    generated_files.append(dashboard_file)
                    # print(f"  ✓ Dashboard: {os.path.basename(dashboard_file)}")
                    
            except Exception as e:
                # print(f"  ✗ Erro ao gerar plots para {alg_name}: {e}")
                import traceback
                traceback.print_exc()
        
        # print("\n" + "="*60)
        # print(f"PLOTS FINAIS GERADOS: {len(generated_files)} arquivos")
        # print("="*60 + "\n")
        
        return generated_files


# Instância global
pareto_collector = ParetoCollector()