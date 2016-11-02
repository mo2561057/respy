""" This module contains the functions for the generation of random requests.
"""
import numpy as np

from respy.python.shared.shared_auxiliary import generate_optimizer_options
from respy.python.shared.shared_auxiliary import print_init_dict
from respy.python.shared.shared_constants import OPT_EST_FORT
from respy.python.shared.shared_constants import OPT_EST_PYTH
from respy.python.shared.shared_constants import OPT_AMB_FORT
from respy.python.shared.shared_constants import OPT_AMB_PYTH
from respy.python.shared.shared_constants import IS_PARALLEL
from respy.python.shared.shared_constants import IS_FORTRAN

# module-wide variables
OPTIMIZERS_EST = OPT_EST_FORT + OPT_EST_PYTH
OPTIMIZERS_AMB = OPT_AMB_FORT + OPT_AMB_PYTH

MAX_AGENTS = 1000
MAX_DRAWS = 100
MAX_PERIODS = 5


def generate_init(constraints=None):
    """ Get a random initialization file.
    """
    # Antibugging. This interface is using a sentinel value.
    if constraints is not None:
        assert (isinstance(constraints, dict))

    dict_ = generate_random_dict(constraints)

    print_init_dict(dict_)

    # Finishing.
    return dict_


def generate_random_dict(constraints=None):
    """ Draw random dictionary instance that can be processed into an
        initialization file.
    """
    # Antibugging. This interface is using a sentinal value.
    if constraints is not None:
        assert (isinstance(constraints, dict))
    else:
        constraints = dict()

    # Initialize container
    dict_ = dict()

    # We now draw all parameter values. This is necessarily done here as we
    # subsequently determine a set of valid bounds.
    paras_values = []
    for i in range(27):
        if i in [0]:
            value = get_valid_values('amb')
        elif i in range(1, 17):
            value = get_valid_values('coeff')
        elif i in [17, 21, 24, 26]:
            value = get_valid_values('cov')
        else:
            value = 0.0

        paras_values += [value]

    # Construct a set of valid bounds. Note that there are now bounds for the
    # coefficients of the covariance matrix. It is not clear how to enforce
    # these during an estimation on the Cholesky factors. Same problem occurs
    # for the set of fixed parameters.
    paras_bounds = []
    for i, value in enumerate(paras_values):
        if i in [0]:
            bounds = get_valid_bounds('amb', value)
        elif i in range(17, 27):
            bounds = get_valid_bounds('cov', value)
        else:
            bounds = get_valid_bounds('coeff', value)

        paras_bounds += [bounds]

    # The dictionary also contains the information whether parameters are
    # fixed during an estimation. We need to ensure that at least one
    # parameter is always free. At this point we also want to ensure that
    # either all shock coefficients are fixed or none. It is not clear how to
    # ensure other constraints on the Cholesky factors.
    paras_fixed = np.random.choice([True, False], 17).tolist()
    if sum(paras_fixed) == 17:
        paras_fixed[np.random.randint(0, 17)] = True
    paras_fixed += [np.random.choice([True, False]).tolist()] * 10

    # Sampling number of agents for the simulation. This is then used as the
    # upper bound for the dataset used in the estimation.
    num_agents_sim = np.random.randint(3, MAX_AGENTS)

    # Basics
    dict_['BASICS'] = dict()
    dict_['BASICS']['periods'] = np.random.randint(1, MAX_PERIODS)
    dict_['BASICS']['delta'] = np.random.random()

    # Home
    dict_['HOME'] = dict()
    dict_['HOME']['coeffs'] = paras_values[16:17]
    dict_['HOME']['bounds'] = paras_bounds[16:17]
    dict_['HOME']['fixed'] = paras_fixed[16:17]

    # Occupation A
    dict_['OCCUPATION A'] = dict()
    dict_['OCCUPATION A']['coeffs'] = paras_values[1:7]
    dict_['OCCUPATION A']['bounds'] = paras_bounds[1:7]
    dict_['OCCUPATION A']['fixed'] = paras_fixed[1:7]

    # Occupation B
    dict_['OCCUPATION B'] = dict()
    dict_['OCCUPATION B']['coeffs'] = paras_values[7:13]
    dict_['OCCUPATION B']['bounds'] = paras_bounds[7:13]
    dict_['OCCUPATION B']['fixed'] = paras_fixed[7:13]

    # Education
    dict_['EDUCATION'] = dict()
    dict_['EDUCATION']['coeffs'] = paras_values[13:16]
    dict_['EDUCATION']['bounds'] = paras_bounds[13:16]
    dict_['EDUCATION']['fixed'] = paras_fixed[13:16]

    dict_['EDUCATION']['start'] = np.random.randint(1, 10)
    dict_['EDUCATION']['max'] = np.random.randint(
        dict_['EDUCATION']['start'] + 1, 20)

    # SOLUTION
    dict_['SOLUTION'] = dict()
    dict_['SOLUTION']['draws'] = np.random.randint(1, MAX_DRAWS)
    dict_['SOLUTION']['seed'] = np.random.randint(1, 10000)
    dict_['SOLUTION']['store'] = np.random.choice(['True', 'False'])

    # AMBIGUITY
    dict_['AMBIGUITY'] = dict()
    dict_['AMBIGUITY']['measure'] = np.random.choice(['abs', 'kl'])
    dict_['AMBIGUITY']['coeffs'] = paras_values[0:1]
    dict_['AMBIGUITY']['bounds'] = paras_bounds[0:1]
    dict_['AMBIGUITY']['fixed'] = paras_fixed[0:1]

    # ESTIMATION
    dict_['ESTIMATION'] = dict()
    dict_['ESTIMATION']['agents'] = np.random.randint(1, num_agents_sim)
    dict_['ESTIMATION']['draws'] = np.random.randint(1, MAX_DRAWS)
    dict_['ESTIMATION']['seed'] = np.random.randint(1, 10000)
    dict_['ESTIMATION']['file'] = 'data.respy.dat'
    dict_['ESTIMATION']['optimizer'] = np.random.choice(OPTIMIZERS_EST)
    dict_['ESTIMATION']['maxfun'] = np.random.randint(1, 10000)
    dict_['ESTIMATION']['tau'] = np.random.uniform(100, 500)

    # DERIVATIVES
    dict_['DERIVATIVES'] = dict()
    dict_['DERIVATIVES']['version'] = 'FORWARD-DIFFERENCES'

    # PRECONDITIONING
    dict_['PRECONDITIONING'] = dict()
    dict_['PRECONDITIONING']['minimum'] = np.random.uniform(0.0000001, 0.1)
    dict_['PRECONDITIONING']['type'] = np.random.choice(['gradient',
                                                         'identity'])
    dict_['PRECONDITIONING']['eps'] = np.random.uniform(0.0000001, 0.1)

    # PROGRAM
    dict_['PROGRAM'] = dict()
    if IS_PARALLEL:
        dict_['PROGRAM']['procs'] = np.random.randint(1, 5)
    else:
        dict_['PROGRAM']['procs'] = 1

    versions = ['FORTRAN', 'PYTHON']
    if dict_['PROGRAM']['procs'] > 1:
        versions = ['FORTRAN']

    if not IS_FORTRAN:
        versions = ['PYTHON']

    dict_['PROGRAM']['debug'] = 'True'
    dict_['PROGRAM']['version'] = np.random.choice(versions)

    # The optimizer has to align with the Program version.
    if dict_['PROGRAM']['version'] == 'FORTRAN':
        dict_['ESTIMATION']['optimizer'] = np.random.choice(OPT_EST_FORT)
    else:
        dict_['ESTIMATION']['optimizer'] = np.random.choice(OPT_EST_PYTH)

    # SIMULATION
    dict_['SIMULATION'] = dict()
    dict_['SIMULATION']['seed'] = np.random.randint(1, 10000)
    dict_['SIMULATION']['agents'] = num_agents_sim
    dict_['SIMULATION']['file'] = 'data'

    # SHOCKS
    dict_['SHOCKS'] = dict()
    dict_['SHOCKS']['coeffs'] = paras_values[17:]
    dict_['SHOCKS']['bounds'] = paras_bounds[17:]
    dict_['SHOCKS']['fixed'] = paras_fixed[17:]

    # INTERPOLATION
    dict_['INTERPOLATION'] = dict()
    dict_['INTERPOLATION']['flag'] = np.random.choice(['True', 'False'])
    dict_['INTERPOLATION']['points'] = np.random.randint(10, 100)

    for optimizer in OPTIMIZERS_EST + OPTIMIZERS_AMB:
        dict_[optimizer] = generate_optimizer_options(optimizer, paras_fixed)

    # The options for the optimizers across the program versions are
    # identical. Otherwise it is not possible to simply run the solution of a
    # model with just changing the program version.
    dict_['FORT-SLSQP'] = dict_['SCIPY-SLSQP']

    """ We now impose selected constraints on the final model specification.
    These constraints can be very useful in the generation of test cases. """

    # Address incompatibility issues
    keys = constraints.keys()
    if 'is_myopic' in keys:
        assert 'delta' not in keys

    if 'is_estimation' in keys:
        assert 'maxfun' not in keys
        assert 'flag_precond' not in keys

    if 'flag_ambiguity' in keys:
        assert 'level' not in keys

    if 'agents' in keys:
        assert 'max_draws' not in keys

    if ('flag_parallelism' in keys) and ('version' in keys) and constraints[
        'flag_parallelism']:
            assert constraints['version'] == 'FORTRAN'

    # Replace path to dataset used for estimation
    if 'file_est' in constraints.keys():
        # Checks
        assert isinstance(constraints['file_est'], str)
        # Replace in initialization files
        dict_['ESTIMATION']['file'] = constraints['file_est']

    # Replace interpolation
    if 'flag_interpolation' in constraints.keys():
        # Checks
        assert (constraints['flag_interpolation'] in [True, False])
        # Replace in initialization files
        dict_['INTERPOLATION']['flag'] = constraints['flag_interpolation']

    # Replace number of periods
    if 'points' in constraints.keys():
        # Extract objects
        points = constraints['points']
        # Checks
        assert (isinstance(points, int))
        assert (points > 0)
        # Replace in initialization files
        dict_['INTERPOLATION']['points'] = points

    # Replace number of iterations
    if 'maxfun' in constraints.keys():
        # Extract objects
        maxfun = constraints['maxfun']
        # Checks
        assert (isinstance(maxfun, int))
        assert (maxfun >= 0)
        # Replace in initialization files
        dict_['ESTIMATION']['maxfun'] = maxfun

    # Replace education
    if 'edu' in constraints.keys():
        # Extract objects
        start, max_ = constraints['edu']
        # Checks
        assert (isinstance(start, int))
        assert (start > 0)
        assert (isinstance(max_, int))
        assert (max_ > start)
        # Replace in initialization file
        dict_['EDUCATION']['start'] = start
        dict_['EDUCATION']['max'] = max_

    # Replace measure of ambiguity
    if 'measure' in constraints.keys():
        # Extract object
        measure = constraints['measure']
        # Checks
        assert measure in ['kl', 'abs']
        # Replace in initialization file
        dict_['AMBIGUITY']['measure'] = measure

    # Replace level of ambiguity
    if 'level' in constraints.keys():
        # Extract object
        level = constraints['level']
        # Checks
        assert isinstance(level, float)
        assert level >= 0.0
        # Replace in initialization file
        dict_['AMBIGUITY']['coeffs'] = [level]
        dict_['AMBIGUITY']['bounds'] = [get_valid_bounds('amb', level)]

    # Treat level of ambiguity as fixed in an estimation
    if 'flag_ambiguity' in constraints.keys():
        # Checks
        assert (constraints['flag_ambiguity'] in [True, False])
        # Replace in initialization files
        if constraints['flag_ambiguity']:
            value = np.random.uniform(0.01, 1.0)
            dict_['AMBIGUITY']['coeffs'] = [value]
            dict_['AMBIGUITY']['bounds'] = [get_valid_bounds('amb', value)]
        else:
            dict_['AMBIGUITY']['coeffs'] = [0.00]
            dict_['AMBIGUITY']['bounds'] = [get_valid_bounds('amb', 0.00)]

    # Treat level of ambiguity as fixed in an estimation
    if 'fixed_ambiguity' in constraints.keys():
        # Checks
        assert (constraints['fixed_ambiguity'] in [True, False])
        # Replace in initialization files
        dict_['AMBIGUITY']['fixed'] = [constraints['fixed_ambiguity']]

    # Replace version
    if 'version' in constraints.keys():
        # Extract objects
        version = constraints['version']
        # Checks
        assert (version in ['PYTHON', 'FORTRAN'])
        # Replace in initialization file
        dict_['PROGRAM']['version'] = version
        # Ensure that the constraints are met
        if version != 'FORTRAN':
            dict_['PROGRAM']['procs'] = 1
        if version == 'FORTRAN':
            dict_['ESTIMATION']['optimizer'] = np.random.choice(OPT_EST_FORT)
        else:
            dict_['ESTIMATION']['optimizer'] = np.random.choice(OPT_EST_PYTH)

    # Ensure that random deviates do not exceed a certain number. This is
    # useful when aligning the randomness across implementations.
    if 'max_draws' in constraints.keys():
        # Extract objects
        max_draws = constraints['max_draws']
        # Checks
        assert (isinstance(max_draws, int))
        assert (max_draws > 2)
        # Replace in initialization file
        num_agents_sim = np.random.randint(2, max_draws)
        dict_['SIMULATION']['agents'] = num_agents_sim
        dict_['ESTIMATION']['agents'] = np.random.randint(1, num_agents_sim)
        dict_['ESTIMATION']['draws'] = np.random.randint(1, max_draws)
        dict_['SOLUTION']['draws'] = np.random.randint(1, max_draws)

    # Replace parallelism ...
    if 'flag_parallelism' in constraints.keys():
        # Extract objects
        flag_parallelism = constraints['flag_parallelism']
        # Checks
        assert (flag_parallelism in [True, False])
        # Replace in initialization file
        if flag_parallelism:
            dict_['PROGRAM']['procs'] = np.random.randint(2, 5)
        else:
            dict_['PROGRAM']['procs'] = 1
        # Ensure that the constraints are met
        if dict_['PROGRAM']['procs'] > 1:
            dict_['PROGRAM']['version'] = 'FORTRAN'

    if 'flag_precond' in constraints.keys():
        # Extract objects
        flag_precond = constraints['flag_precond']
        # Checks
        assert (flag_precond in [True, False])
        # Replace in initialization file
        if flag_precond:
            dict_['PRECONDITIONING']['type'] = 'gradient'
        else:
            dict_['PRECONDITIONING']['type'] = 'identity'

    # Replace store attribute
    if 'is_store' in constraints.keys():
        # Extract objects
        is_store = constraints['is_store']
        # Checks
        assert (is_store in [True, False])
        # Replace in initialization file
        dict_['SOLUTION']['store'] = str(is_store)

    # Replace number of periods
    if 'periods' in constraints.keys():
        # Extract objects
        periods = constraints['periods']
        # Checks
        assert (isinstance(periods, int))
        assert (periods > 0)
        # Replace in initialization files
        dict_['BASICS']['periods'] = periods

    # Replace discount factor
    if 'is_myopic' in constraints.keys():
        # Extract object
        assert ('delta' not in constraints.keys())
        assert (constraints['is_myopic'] in [True, False])
        # Replace in initialization files
        if constraints['is_myopic']:
            dict_['BASICS']['delta'] = 0.0
        else:
            dict_['BASICS']['delta'] = np.random.uniform(0.1, 1.0)

    # Replace discount factor. This is option is needed in addition to
    # is_myopic the code is run for very small levels of delta and compared
    # against the myopic version.
    if 'delta' in constraints.keys():
        # Extract objects
        delta = constraints['delta']
        # Checks
        assert ('is_myopic' not in constraints.keys())
        assert (np.isfinite(delta))
        assert (delta >= 0.0)
        assert (isinstance(delta, float))
        # Replace in initialization file
        dict_['BASICS']['delta'] = delta

    # No random component to rewards
    if 'is_deterministic' in constraints.keys():
        # Checks
        assert (constraints['is_deterministic'] in [True, False])
        # Replace in initialization files
        if constraints['is_deterministic']:
            dict_['SHOCKS']['coeffs'] = [0.0] * 10

    # Number of agents
    if 'agents' in constraints.keys():
        # Extract object
        num_agents = constraints['agents']
        # Checks
        assert (num_agents > 0)
        assert (isinstance(num_agents, int))
        assert (np.isfinite(num_agents))
        # Replace in initialization files
        dict_['SIMULATION']['agents'] = num_agents
        if num_agents == 1:
            dict_['ESTIMATION']['agents'] = 1
        else:
            dict_['ESTIMATION']['agents'] = np.random.randint(1, num_agents)

    # Estimation task, but very small. A host of other constraints need to be
    # honored as well.
    if 'is_estimation' in constraints.keys():
        # Checks
        assert (constraints['is_estimation'] in [True, False])
        # Replace in initialization files
        if constraints['is_estimation']:
            dict_['is_store'] = False
            dict_['ESTIMATION']['maxfun'] = int(np.random.choice(range(6),
                p=[0.5, 0.1, 0.1, 0.1, 0.1, 0.1]))
            dict_['PRECONDITIONING']['type'] = \
                np.random.choice(['gradient', 'identity'], p=[0.1, 0.9])

            # Ensure that a valid estimator is selected in the case that a
            # free parameter has bounds.
            for i in range(27):
                if paras_fixed[i]:
                    continue
                if any(item is not None for item in paras_bounds[i]):
                    if dict_['PROGRAM']['version'] == 'FORTRAN':
                        dict_['ESTIMATION']['optimizer'] = 'FORT-BOBYQA'
                    else:
                        dict_['ESTIMATION']['optimizer'] = 'SCIPY-LBFGSB'
                    break
    # Finishing
    return dict_


def get_valid_values(which):
    """ Simply get a valid value.
    """
    assert which in ['amb', 'cov', 'coeff']

    if which in ['amb']:
        value = np.random.choice([0.0, np.random.uniform()])
    elif which in ['coeff']:
        value = np.random.uniform(-0.05, 0.05)
    elif which in ['cov']:
        value = np.random.uniform(0.05, 1)

    return value


def get_valid_bounds(which, value):
    """ Simply get a valid set of bounds.
    """
    assert which in ['amb', 'cov', 'coeff']

    # The bounds cannot be too tight as otherwise the BOBYQA might not start
    # properly.
    if which in ['amb']:
        upper = np.random.choice([None, value + np.random.uniform(low=0.1)])
        bounds = [max(0.0, value - np.random.uniform(low=0.1)), upper]
    elif which in ['coeff']:
        upper = np.random.choice([None, value + np.random.uniform(low=0.1)])
        lower = np.random.choice([None, value - np.random.uniform(low=0.1)])
        bounds = [lower, upper]
    elif which in ['cov']:
        bounds = [None, None]

    return bounds


