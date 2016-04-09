""" This module contains the interface to simulate a dataset and write the
information to disk.

    Structure of Dataset:

        0   Identifier of Agent
        1   Time Period
        2   Choice (1 = Work A, 2 = Work B, 3 = Education, 4 = Home)
        3   Earnings (missing value if not working)
        4   Work Experience A
        5   Work Experience B
        6   Schooling
        7   Lagged Schooling

"""

# standard library
import pandas as pd
import numpy as np

import logging

# project library
from robupy.python.simulate.simulate_auxiliary import start_logging
from robupy.python.simulate.simulate_auxiliary import stop_logging
from robupy.python.simulate.simulate_auxiliary import check_input
from robupy.python.simulate.simulate_auxiliary import write_info
from robupy.python.simulate.simulate_auxiliary import write_out

from robupy.python.shared.shared_auxiliary import dist_class_attributes
from robupy.python.shared.shared_auxiliary import dist_model_paras
from robupy.python.shared.shared_auxiliary import replace_missing_values
from robupy.python.shared.shared_auxiliary import check_dataset
from robupy.python.shared.shared_auxiliary import create_draws

from robupy.fortran.f2py_library import f2py_simulate

from robupy.solve import solve

# Logging
from robupy.python.simulate.simulate_python import pyth_simulate

logger = logging.getLogger('ROBUPY_SIMULATE')

''' Main function
'''


def simulate(robupy_obj):
    """ Simulate dataset from model. To keep the different tasks as separate
    as possible, this requires to pass in a solved robupy_obj.
    """
    # Checks
    assert check_input(robupy_obj)

    # Solve the requested economy
    solve(robupy_obj)

    # Fire up the logging for the simulation. The logging of the solution
    # step is handled within the solution routines.
    start_logging()

    # Distribute class attributes
    periods_payoffs_systematic, mapping_state_idx, periods_emax, model_paras, \
        num_periods, num_agents, states_all, edu_start, seed_data, is_debug, \
        file_sim, edu_max, delta, version = \
            dist_class_attributes(robupy_obj,
                'periods_payoffs_systematic', 'mapping_state_idx',
                'periods_emax', 'model_paras', 'num_periods', 'num_agents',
                'states_all', 'edu_start', 'seed_data', 'is_debug',
                'file_sim', 'edu_max', 'delta', 'version')

    # Auxiliary objects
    shocks_cholesky = dist_model_paras(model_paras, is_debug)[5]

    # Draw draws for the simulation.
    periods_draws_sims = create_draws(num_periods, num_agents, seed_data,
        is_debug)

    # Simulate a dataset with the results from the solution and write out the
    # dataset to a text file. In addition a file summarizing the dataset is
    # produced.
    logger.info('Starting simulation of model for ' + str(num_agents) +
        ' agents with seed ' + str(seed_data))

    # Collect arguments to pass in different implementations of the simulation.
    args = (periods_payoffs_systematic, mapping_state_idx, periods_emax,
        num_periods, states_all, num_agents, edu_start, edu_max, delta,
        periods_draws_sims, shocks_cholesky)

    # Select appropriate interface
    if version == 'PYTHON':
        data_array = pyth_simulate(*args)
    elif version in ['FORTRAN', 'F2PY']:
        data_array = f2py_simulate(*args)
    else:
        raise NotImplementedError

    # Create pandas data frame with missing values.
    data_frame = pd.DataFrame(replace_missing_values(data_array))

    # Wrapping up by running some checks on the dataset and then writing out
    # the file and some basic information.
    if is_debug:
        check_dataset(data_frame, robupy_obj)

    write_out(robupy_obj, data_frame)

    write_info(robupy_obj, data_frame)

    logger.info('... finished \n')

    stop_logging()

    # Finishing
    return data_frame


