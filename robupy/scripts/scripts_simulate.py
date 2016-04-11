#!/usr/bin/env python
""" This script serves as a command line tool to ease the simulation of the
model.
"""

# standard library
import argparse
import os

import numpy as np
# project library
from robupy.python.estimate.estimate_auxiliary import dist_optim_paras

from robupy import simulate
from robupy import read

""" Auxiliary function
"""


def dist_input_arguments(parser):
    """ Check input for estimation script.
    """
    # Parse arguments
    args = parser.parse_args()

    # Distribute arguments
    init_file = args.init_file
    file_sim = args.file_sim
    update = args.update

    # Check attributes
    assert (update in [False, True])
    assert (os.path.exists(init_file))

    if update:
        assert (os.path.exists('paras_steps.robupy.log'))

    # Finishing
    return update, init_file, file_sim


""" Main function
"""


def scripts_simulate(update, init_file, file_sim):
    """ Wrapper for the estimation.
    """
    # Read in baseline model specification.
    robupy_obj = read(init_file)

    # Update parametrization of the model if resuming from a previous
    # estimation run.
    if update:
        x0 = np.genfromtxt('paras_steps.robupy.log')
        args = dist_optim_paras(x0, True)
        robupy_obj.update_model_paras(*args)

    # Update file for output.
    if file_sim is not None:
        robupy_obj.unlock()
        robupy_obj.set_attr('file_sim', file_sim)
        robupy_obj.lock()

    # Optimize the criterion function.
    simulate(robupy_obj)


''' Execution of module as script.
'''
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description =
        'Start of simulation with the ROBUPY package.',
        formatter_class = argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--update', action ='store_true',  dest='update',
        default=False, help='update model parametrization')

    parser.add_argument('--init_file', action='store', dest='init_file',
        default='model.robupy.ini', help='initialization file')

    parser.add_argument('--file_sim', action='store', dest='file_sim',
        default=None, help='output file')

    # Process command line arguments
    args = dist_input_arguments(parser)

    # Run simulation
    scripts_simulate(*args)