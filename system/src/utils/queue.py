#!/usr/bin/python3
# title: queue.py
# author: Joahannes Costa <joahannes@lrc.ic.unicamp.br
# date: 29.10.2021

from prettytable import PrettyTable

class Queue():

	def __init__(self):
		self.task_queue = []
		self.task_queue_control = {}
		self.final_queue = {}

		# test
		header = ["task_id", "size", "value", "cpu", "deadline", "insert_time", "start_time", "finish_time", "remove_time", "waiting_time", "cost", "status"]
		self.task_table = PrettyTable(header)

	def enqueue(self, task_id, tasks_set, step):
		"""
		Enqueue method adds a task to a task queue, where each task is stored as a dictionary
		containing its attributes such as size, value, cpu usage, deadline, and status.
		The task is also added to a priority queue using heapq.heappush based on its deadline.
		The method also saves the task's information in two dictionaries, task_queue_control and
		final_queue, to preserve the original task information. 
		"""

		self.insert_time = float(step) # time.time()
		# print("Adding task %s in instant %.1fs" % (task_id, self.insert_time))
		
		self.local_task								= {}
		self.local_task[task_id]					= {}
		self.local_task[task_id]['size']			= tasks_set[task_id]['size']
		self.local_task[task_id]['value']			= tasks_set[task_id]['value']
		self.local_task[task_id]['cpu']				= tasks_set[task_id]['cpu']
		self.local_task[task_id]['deadline']		= tasks_set[task_id]['deadline']
		self.local_task[task_id]['insert_time']		= self.insert_time
		self.local_task[task_id]['start_time']		= None #TALVEZ NAO PRECISE
		self.local_task[task_id]['finish_time']		= None #TALVEZ NAO PRECISE
		self.local_task[task_id]['remove_time']		= self.insert_time + tasks_set[task_id]['deadline'] # TODAS COMECAM NO PIOR CASO, PASSAR O PERIODO INTEIRO NA FILA
		self.local_task[task_id]['waiting_time']	= self.insert_time + tasks_set[task_id]['deadline']
		self.local_task[task_id]['cost']			= None
		self.local_task[task_id]['status']			= 'PENDING'

		# queue = [size, deadline, task_id]
		self.task_queue.append(task_id)

		self.task_queue_control[task_id] = self.local_task[task_id]
		self.final_queue[task_id] = self.local_task[task_id].copy() # COPY TO PRESERVE INITIAL VALUES

		# add in pretty table
		# self.insert_row(task_id, self.local_task[task_id])
		# print(self.task_table)

	def update(self, step, schedule, step_lenght):
		"""Update"""

		self.deadline_control = []
		for task in self.task_queue:
			# Decrement the deadline of each task
			# TODO: COMPUTAR STEP LENGHT
			self.task_queue_control[task]['deadline'] -= step_lenght
			task_deadline = self.task_queue_control[task]['deadline']

			# If the task's deadline has expired
			if task_deadline <= 0:
				# print(task, "needs to be removed from the queue!")
				# Add the task to the deadline control list
				self.deadline_control.append(task)

		# If there are tasks in the deadline control list
		if len(self.deadline_control) > 0:
			# Update the status and removal time of expired tasks in the final queue and task queue control
			for task in self.deadline_control:
				self.task_queue_control[task]['status'] = 'EXPIRED'
				self.final_queue[task]['status'] = 'EXPIRED'

				remove_time = float(step)
				self.task_queue_control[task]['remove_time'] = remove_time
				self.final_queue[task]['remove_time'] = remove_time

				# Remove the expired task from the task queue
				self.task_queue.remove(task)

				# Update the status of the expired task in the scheduling object
				for expired in schedule.escalonamento:
					if task in schedule.escalonamento[expired]:
						schedule.escalonamento[expired][task]['status'] = 'EXPIRED'

		# TODO: Update task table with task updates

		# Clear the rows of the task table
		self.task_table.clear_rows()

		for task in self.final_queue:
			# Insert a row for each task in the task table
			self.insert_row(task, self.final_queue[task])


	def get_queue(self):
		return self.task_queue
	
	def size_queue(self):
		return len(self.task_queue)
	
	# insere tarefa na tabela para melhor visualizacao
	def insert_row(self, key, row):
		# dictionary = {key : {row}}
		self.temp = []
		self.temp.append(key)
		for item in row:
			self.temp.append(row[item])
		self.task_table.add_row(self.temp)