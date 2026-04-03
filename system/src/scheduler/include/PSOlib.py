import random

class Particle:
    def __init__(self, tasks):
        self.tasks = tasks
        self.position = random.sample(tasks, len(tasks))  # Inicializa com uma permutação aleatória das tarefas
        self.velocity = [random.uniform(-1, 1) for _ in range(len(tasks))]
        self.best_position = list(self.position)
        self.best_fitness = float('-inf')

class PSO:
    def __init__(self, tasks, fitness_func, num_particles=30, max_iter=100):
        self.tasks = tasks
        self.task_indices = {task: i for i, task in enumerate(tasks)}  # Mapeamento de tarefas para índices
        self.fitness_func = fitness_func
        self.num_particles = num_particles
        self.max_iter = max_iter
        self.swarm = [Particle(tasks) for _ in range(num_particles)]
        self.global_best_position = None
        self.global_best_fitness = float('-inf')

    def run(self):
        for _ in range(self.max_iter):
            for particle in self.swarm:
                fitness = self.fitness_func(particle.position)
                if fitness > particle.best_fitness:
                    particle.best_fitness = fitness
                    particle.best_position = list(particle.position)
                if fitness > self.global_best_fitness:
                    self.global_best_fitness = fitness
                    self.global_best_position = list(particle.position)

            for particle in self.swarm:
                self.update_velocity(particle)
                self.update_position(particle)

        return self.global_best_position

    def update_velocity(self, particle):
        w = 0.5  # Inércia
        c1 = 1  # Constante cognitiva
        c2 = 2  # Constante social

        for i in range(len(particle.velocity)):
            r1 = random.random()
            r2 = random.random()
            cognitive = c1 * r1 * (self.task_indices[particle.best_position[i]] - self.task_indices[particle.position[i]])
            social = c2 * r2 * (self.task_indices[self.global_best_position[i]] - self.task_indices[particle.position[i]])
            particle.velocity[i] = w * particle.velocity[i] + cognitive + social

    def update_position(self, particle):
        for i in range(len(particle.position)):
            particle.velocity[i] = int(particle.velocity[i])  # Converte a velocidade para um índice inteiro
            new_index = self.task_indices[particle.position[i]] + particle.velocity[i]
            new_index = max(0, min(new_index, len(self.tasks) - 1))  # Garante que o índice esteja dentro dos limites
            particle.position[i] = self.tasks[new_index]

        # Remove duplicatas e mantém a permutação única
        seen = set()
        particle.position = [x for x in particle.position if not (x in seen or seen.add(x))]
        missing = set(self.tasks) - set(particle.position)
        particle.position.extend(missing)
