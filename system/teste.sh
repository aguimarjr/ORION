#!/bin/bash
# Autor: Joahannes B. D. da Costa <joahannes.costa@unifesp.br>
# Data: 31.10.2025
# Descricao: Script para executar simulações VEC em paralelo com diferentes algoritmos de alocação de tarefas.

SCENARIO="cologne"

INTERVAL=5

BEGIN=100
START_PROCESS=100
SIMULATION_TIME=30

STEP_LENGHT=0.1

RESOURCES_VCS=1

TOTAL_SEEDS="1 2"

SEED_SUMO=2

TASK_RATE="5 15"

TASK_SIZE=10

CPU_CYCLE=30

# SBRC
ALGORITHMS="FCFS ORION"

DEADLINES="0.5 7"

function RUN()
{
    parallel --bar -j $CORES "python3 simulation.py \
    --scenario {1} \
    --interval {2} \
    --tasks 10 \
    --begin $BEGIN \
    --end $SIMULATION_TIME \
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
    --steplenght {12}" ::: $SCENARIO ::: $INTERVAL ::: $RESOURCES_VCS ::: \
    $TASK_SIZE ::: $TASK_RATE ::: $CPU_CYCLE ::: \
    $ALGORITHMS ::: $SEED_SUMO ::: $TOTAL_SEEDS ::: $DEADLINES ::: $START_PROCESS ::: $STEP_LENGHT
}

if [ -z $1 ]
then
    echo "Verifique os parametros!"
    echo "$ bash run n_cores"
    exit 1
elif [[ "$1" =~ ^-?[0-9]+$ ]]
then
    CORES=$1
    RUN;
else
    echo "Parâmetro inválido! Use um número inteiro para definir os núcleos."
    exit 1
fi