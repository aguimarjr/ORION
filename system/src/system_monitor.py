#!/usr/bin/env python
# title: monitor.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 04.11.2021

import random
import logging

class SchedulingMonitor():

	def get_status(self, step, schedule, task, cloud, queue, step_lenght):

		self.current_time = step

		# UPDATE TASK QUEUE
		queue.update(step, schedule, step_lenght)

		self.remove_now = []
			
		for cloud_i, tasks_j in schedule.escalonamento.items():
			
			for item in tasks_j:

				if float(self.current_time) >= float(queue.task_queue_control[item]['finish_time']):
					
					if queue.task_queue_control[item]['status'] == 'SUBMITTED':
						# print(item + " concluiu seu processamento!")
						logging.debug("%s concluiu seu processamento!" % item)

						# task_remove_time = float(self.current_time) + round(random.random(), 4)
						task_remove_time = round(queue.task_queue_control[item]['finish_time'] + random.uniform(0.1, 0.5), 4)
						queue.task_queue_control[item]['remove_time'] = task_remove_time
						queue.task_queue_control[item]['status'] = 'COMPLETED'
						queue.final_queue[item]['remove_time'] = task_remove_time
						queue.final_queue[item]['status'] = 'COMPLETED'
						
						# remove task queued
						queue.task_queue.remove(item)

						# READICIONA RECURSO NA VC CORRESPONDENTE
						task_info_resource = schedule.resource_usage[cloud_i][item]
						# print(task_info_resource)

						# compute cost
						local_cost = self.resource_price(task_info_resource)
						queue.final_queue[item]['cost'] = local_cost

						cloud.update(cloud_i, task_info_resource, 'complete')
						del schedule.resource_usage[cloud_i][item]
						self.remove_now.append([cloud_i, item])
				
					elif queue.task_queue_control[item]['status'] == 'EXPIRED':

						task_info_resource = schedule.resource_usage[cloud_i][item]
						
						# compute cost
						local_cost = self.resource_price(task_info_resource)
						queue.final_queue[item]['cost'] = local_cost
						
						cloud.update(cloud_i, task_info_resource, 'complete')
						del schedule.resource_usage[cloud_i][item]
						self.remove_now.append([cloud_i, item])

		# REMOVE TAREFAS CONCLUIDAS DA ESTRUTURA DE ESCALONAMENTO
		for remove_id in self.remove_now:
			del schedule.escalonamento[remove_id[0]][remove_id[1]]

	def check_vehicular_cloud(self, cloud, queue):
		"Check resources in each vehicular clouds."
		return 0

	def resource_price(self, uso_recursos):
		"Define monetary cost based on resource used."
		# print(uso_recursos)
		total_price = 0
		time_using = uso_recursos['processing_time']
		
		vehicle_price = 5.17296 # c8a.metal-24xl
		bs_price = 10.34592 # c8a.48xlarge

		vehicle_total_cost = (vehicle_price * uso_recursos['vehicle']) * time_using
		bs_total_cost = (bs_price * uso_recursos['bs']) * time_using

		total_price = round(vehicle_total_cost + bs_total_cost, 3)

		return total_price
