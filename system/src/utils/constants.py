#!/usr/bin/env python
# title: constants.py
# author: Joahannes Costa <joahannes.costa@ic.unicamp.br>
# date: 25.07.2024

"""
This file contains the main constants used in the project.
"""

# Path to the main project directory
PATH                = '/home/joahannes/project/ORION/system/'

# Folder name for input files
INPUT_FOLDER        = 'input/'

# Flag to determine if dataset creation is enabled or not
CREATE_DATASET      = False

# Path to the dataset file
DATASET_FILE        = PATH + INPUT_FOLDER + 'test/'

# Name of the experiment
EXPERIMENTS         = 'temp'

# File path to the list of base station positions
BS_POSITION_FILE    = PATH + INPUT_FOLDER + 'bs_center_list.txt'

# File path to the base station files
BS_FILE             = PATH + INPUT_FOLDER + EXPERIMENTS + '/'

# CPU capacity of the base station
BS_CPU              = 15

# Memory capacity of the base station
BS_MEMORY           = 15

# Window size for prediction
PREDICTION_WINDOW   = 5