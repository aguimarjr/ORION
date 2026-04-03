#!/usr/bin/env python
# title: task_manager.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 30.03.2021

import utils.constants as CONSTANTS

class Task():
	"""
    A class to manage task loading and control from external files.

    The `Task` class maintains a set of tasks (`task_set`) and a control set of tasks (`task_set_control`),
    storing information such as size, value, CPU usage, and deadline of each task.

    Methods:
        - __init__(): Initializes the task sets and the task number list.
        - number_of_tasks(rate, seed): Loads the number of tasks from an input file based on the given rate and seed.
        - load_task_file(size_n, cycles_n, seed_n, deadline_n): Loads task details from a file and stores them in the task sets.
        - get_task(task_id, field): Retrieves a specific field value of a task stored in the control set.

    Attributes:
        - task_set (dict): Dictionary storing the loaded tasks.
        - task_set_control (dict): Control dictionary maintaining a copy of the loaded tasks.
        - tasks_number (list): List containing the number of tasks loaded from the file.
    """

	def __init__(self):
		"""
		Initializes the `Task` class attributes, creating dictionaries to store tasks
		and a list to store the number of tasks.
		"""
		self.task_set = {}
		self.task_set_control = {}
		self.tasks_number = []

	def number_of_tasks(self, rate, seed):
		"""
		Loads the number of tasks from a file based on the given rate and seed.

		The file follows the format 'task_seed_<seed>_rate_<rate>.txt' and contains a list of task numbers.

		Args:
			rate (int): Task arrival rate.
			seed (int): Seed value for experiment replication.

		Side Effects:
			- Updates the `tasks_number` list with the task numbers read from the file.
		"""
		print(" > Loading number of tasks...")
		self.number_tasks_file = CONSTANTS.PATH + CONSTANTS.INPUT_FOLDER + 'tasks/task_seed_' + str(seed) + '_rate_'  + str(rate) + '.txt'
		for i in open(self.number_tasks_file):
			self.tasks_number.append(int(i.split()[0]))
	
	def load_task_file(self, size_n, cycles_n, seed_n, deadline_n):
		"""
		Loads a set of tasks from a file and stores their details.

		The file follows the format 'TASKS_SIZE_<size_n>_CPU_<cycles_n>_SEED_<seed_n>.txt' inside the deadline folder.
		Each line in the file contains information about a task, including its size, value, CPU usage, and deadline.

		Args:
			size_n (int): Task size.
			cycles_n (int): Number of CPU cycles required to execute the task.
			seed_n (int): Seed value used for task generation.
			deadline_n (int): Deadline associated with the tasks.

		Side Effects:
			- Updates the `task_set` and `task_set_control` dictionaries with the loaded task details.
		"""
		print(" > Loading tasks...")
		self.tasks_file = CONSTANTS.PATH + CONSTANTS.INPUT_FOLDER + 'tasks/deadline/' + str(deadline_n) + '/TASKS_SIZE_' + str(size_n) + '_CPU_' + str(cycles_n) + '_SEED_' + str(seed_n) + '.txt'
		for i in open(self.tasks_file):
			self.task_set[i.split()[0]]				= {}
			self.task_set[i.split()[0]]['size']		= int(i.split()[1])
			self.task_set[i.split()[0]]['value']	= int(i.split()[2])
			self.task_set[i.split()[0]]['cpu']		= int(i.split()[3])
			self.task_set[i.split()[0]]['deadline'] = float(i.split()[4])

			self.task_set_control[i.split()[0]]				= {}
			self.task_set_control[i.split()[0]]['size']		= int(i.split()[1])
			self.task_set_control[i.split()[0]]['value']	= int(i.split()[2])
			self.task_set_control[i.split()[0]]['cpu']		= int(i.split()[3])
			self.task_set_control[i.split()[0]]['deadline'] = float(i.split()[4])

	def get_task(self, task_id, field):
		"""
		Retrieves a specific field value of a task stored in the control set.

		Args:
			task_id (str): Task identifier.
			field (str): Name of the requested field (e.g., 'size', 'value', 'cpu', 'deadline').

		Returns:
			int | float: The value corresponding to the requested field.

		Raises:
			KeyError: If the task or the requested field does not exist.

		Side Effects:
			- Prints the details of the task stored in `task_set_control` to the console.
		"""
		print(self.task_set_control[task_id])
		return self.task_set_control[task_id][field]
