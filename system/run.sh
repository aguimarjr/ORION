#!/bin/bash
# Autor: Joahannes B. D. da Costa <joahannes.costa@unifesp.br>
# Data: 31.10.2025
# Descricao: Script para executar simulações VEC em paralelo com diferentes algoritmos de alocação de tarefas.

scenario="cologne"

interval=5

begin=100
start_process=100
simulation_time=500

step_lenght=0.1

resources=1

total_seeds="1 2 3 4 5"

seed_sumo=2

task_rate="5 15 30"

task_size=10

cpu_cycle=30

algorithms="FCFS LOA MAB TEMIS NSGA3 PSO ORION"

deadlines="0.5 1 5 7"

function RUN()
{
    parallel --bar -j $cores "python3 simulation.py \
    --scenario {1} \
    --interval {2} \
    --tasks 10 \
    --begin $begin \
    --end $simulation_time \
    --radius 2000 \
    --resources {3} \
    --weight {4} \
    --taskrate {5} \
    --cpucycle {6} \
    --algorithm {7} \
    --seed_sumo {8} \
    --seed_task {9} \
    --deadline {10} \
    --startprocess {11} \
    --steplenght {12}" ::: $scenario ::: $interval ::: $resources ::: \
    $task_size ::: $task_rate ::: $cpu_cycle ::: \
    $algorithms ::: $seed_sumo ::: $total_seeds ::: $deadlines ::: $start_process ::: $step_lenght
}

if [ -z $1 ]
then
    echo "Verifique os parametros!"
    echo "$ bash run n_cores"
    exit 1
elif [[ "$1" =~ ^-?[0-9]+$ ]]
then
    cores=$1
    RUN;
else
    echo "Parâmetro inválido! Use um número inteiro para definir os núcleos."
    exit 1
fi