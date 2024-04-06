from data_input import *

import sys

import os

import json


class Logger(object):

    def __init__(self, filename="Default.log"):
        self.terminal = sys.stdout

        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)

        self.log.write(message)

    def flush(self):
        pass


path = os.path.abspath(os.path.dirname(__file__))

type = sys.getfilesystemencoding()

sys.stdout = Logger('gurobi_' + str(num_demand) + '_' + str(capacity_station) + '_' + str(num_shift) + '.txt')
