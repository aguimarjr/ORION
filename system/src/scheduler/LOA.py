#!/usr/bin/python3
# title: LOA.py
# author: Matheus Ramos Esteves
# date: 17.11.2025

import utils.general_management as management
from .include import LOA as Lions

def run(queue, clouds, tasks):
    # print("executando LOA....")

    result = {}
    local_tasks = {}
    local_values = {}
    tasks_algo = {}

    for item in queue.get_queue():
        if queue.task_queue_control[item]['status'] == 'PENDING':
            local_tasks[item] = queue.task_queue_control[item]['size']
            local_values[item] = queue.task_queue_control[item]['value']
            tasks_algo[item] = [queue.task_queue_control[item]['size'], queue.task_queue_control[item]['deadline']]

    sorted_clouds = []
    local_clouds = {}
    for i in clouds.clouds:
        local_clouds[i] = clouds.clouds[i]['mips']
        sorted_clouds.append(i)

    resource_splited = {}

    for cloud in range(len(sorted_clouds)):
        if len(local_tasks) > 0:
            id_nuvem = sorted_clouds[cloud]
            result[id_nuvem] = {}

            cloud_capacity = sorted_clouds[cloud]
            local_result = {}

            min_task_size = min(local_tasks, key=local_tasks.get)
            if local_tasks[min_task_size] > local_clouds[id_nuvem]:
                break

            while cloud_capacity > 0:
                temporary_result = Lions.loa_solution(cloud_capacity, tasks_algo)

                if temporary_result is None:
                    break

                id_task_now = temporary_result[0]
                if local_tasks[id_task_now] <= cloud_capacity:
                    local_result[id_task_now] = -1
                    cloud_capacity -= local_tasks[id_task_now]

                    if len(local_tasks) == 0:
                        break
                else:
                    break

            if len(local_result) > 0:
                processing = management.get_processing_time(local_clouds[id_nuvem], tasks, local_result)
                for task in processing:
                    local_result[task] = processing[task]

                resource_splited[id_nuvem] = management.split_resource(local_result, clouds.clouds[id_nuvem], local_tasks)

                for i in list(local_result.keys()):
                    del local_tasks[i]
                    del tasks_algo[i]

                result[id_nuvem] = local_result
        else:
            break

    # print(" ** ", result)
    return result, resource_splited
