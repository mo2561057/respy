# project library
from respy.python.solve.solve_auxiliary import check_input

from respy.python.shared.shared_auxiliary import dist_class_attributes
from respy.python.shared.shared_auxiliary import dist_model_paras
from respy.python.shared.shared_auxiliary import add_solution
from respy.python.shared.shared_auxiliary import create_draws

from respy.python.solve.solve_python import pyth_solve

from respy.fortran.interface import resfort_interface


def solve(respy_obj):
    """ Solve the model
    """
    # Checks, cleanup, start logger
    assert check_input(respy_obj)

    # Distribute class attributes
    model_paras, num_periods, edu_start, is_debug, edu_max, delta, \
        version, num_draws_emax, seed_emax, is_interpolated, num_points_interp, \
        is_myopic, min_idx, store, tau, is_parallel, num_procs, num_agents_sim\
        = \
            dist_class_attributes(respy_obj,
                'model_paras', 'num_periods', 'edu_start', 'is_debug',
                'edu_max', 'delta', 'version', 'num_draws_emax', 'seed_emax',
                'is_interpolated', 'num_points_interp', 'is_myopic', 'min_idx',
                'store', 'tau', 'is_parallel', 'num_procs', 'num_agents_sim')

    # Distribute model parameters
    coeffs_a, coeffs_b, coeffs_edu, coeffs_home, shocks_cholesky = \
        dist_model_paras(model_paras, is_debug)

    # Get the relevant set of disturbances. These are standard normal draws
    # in the case of an ambiguous world. This function is located outside
    # the actual bare solution algorithm to ease testing across
    # implementations.
    periods_draws_emax = create_draws(num_periods, num_draws_emax, seed_emax,
        is_debug)

    # Collect baseline arguments. These are latter amended to account for
    # each interface.
    base_args = (coeffs_a, coeffs_b, coeffs_edu, coeffs_home, shocks_cholesky,
        is_interpolated, num_draws_emax, num_periods, num_points_interp, is_myopic,
        edu_start, is_debug, edu_max, min_idx, delta)

    # Select appropriate interface.
    if version == 'FORTRAN':
        args = base_args + (seed_emax, tau, is_parallel, num_procs, num_agents_sim)
        solution = resfort_interface(respy_obj, 'solve')
    elif version == 'PYTHON':
        args = base_args + (periods_draws_emax, )
        solution = pyth_solve(*args)
    else:
        raise NotImplementedError

    # Attach solution to class instance
    respy_obj = add_solution(respy_obj, store, *solution)

    # Finishing
    return respy_obj


