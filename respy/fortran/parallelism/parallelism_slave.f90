!******************************************************************************
!******************************************************************************
PROGRAM resfort_parallel_slave

    !/* external modules        */

    USE parallelism_constants

    USE parallelism_auxiliary

    USE recording_solution

    USE resfort_library

    USE mpi

    !/* setup                   */

    IMPLICIT NONE

    !/* objects                 */

    INTEGER(our_int), ALLOCATABLE   :: num_states_slaves(:, :)
    INTEGER(our_int), ALLOCATABLE   :: num_obs_slaves(:)
    INTEGER(our_int), ALLOCATABLE   :: displs(:)

    INTEGER(our_int)                :: lower_bound
    INTEGER(our_int)                :: upper_bound
    INTEGER(our_int)                :: task

    REAL(our_dble), ALLOCATABLE     :: data_slave(:, :)
    REAL(our_dble), ALLOCATABLE     :: contribs(:)

    REAL(our_dble)                  :: shocks_cholesky(4, 4)
    REAL(our_dble)                  :: scaled_minimum
    REAL(our_dble)                  :: coeffs_home(1)
    REAL(our_dble)                  :: coeffs_edu(3)
    REAL(our_dble)                  :: coeffs_a(6)
    REAL(our_dble)                  :: coeffs_b(6)
    REAL(our_dble)                  :: level(1)

    LOGICAL                         :: STAY_AVAILABLE = .TRUE.
    LOGICAL                         :: is_scaled

    INTEGER(our_int)                :: num_procs
    INTEGER(our_int)                :: seed_prob
    INTEGER(our_int)                :: seed_emax
    INTEGER(our_int)                :: seed_sim
    INTEGER(our_int)                :: i

    CHARACTER(225)                  :: optimizer_used
    CHARACTER(225)                  :: exec_dir
    CHARACTER(10)                   :: request

!------------------------------------------------------------------------------
! Algorithm
!------------------------------------------------------------------------------

    CALL MPI_INIT(ierr)

    CALL MPI_COMM_RANK(MPI_COMM_WORLD, rank, ierr)

    CALL MPI_COMM_GET_PARENT(PARENTCOMM, ierr)


    CALL read_specification(coeffs_a, coeffs_b, coeffs_edu, coeffs_home, shocks_cholesky, edu_start, edu_max, delta, tau, seed_sim, seed_emax, seed_prob, num_procs, num_slaves, is_debug, is_interpolated, num_points_interp, is_myopic, request, exec_dir, maxfun, paras_fixed, num_free, is_scaled, scaled_minimum, is_ambiguity, measure, level, optimizer_used, dfunc_eps, optimizer_options)

    CALL fort_create_state_space(states_all, states_number_period, mapping_state_idx, num_periods, edu_start, edu_max, min_idx)


    CALL distribute_workload(num_states_slaves, num_obs_slaves)

    CALL create_draws(periods_draws_emax, num_draws_emax, seed_emax, is_debug)


    DO WHILE (STAY_AVAILABLE)


        CALL MPI_Bcast(task, 1, MPI_INT, 0, PARENTCOMM, ierr)

        IF (task == 1) THEN
            CALL MPI_FINALIZE(ierr)
            STAY_AVAILABLE = .FALSE.
            CYCLE
        END IF


        CALL MPI_Bcast(x_all_current, 26, MPI_DOUBLE, 0, PARENTCOMM, ierr)

        CALL dist_optim_paras(level, coeffs_a, coeffs_b, coeffs_edu, coeffs_home, shocks_cholesky, x_all_current)



        IF(task == 2) THEN


            ! This is required to keep the logging aligned between the scalar and the parallel implementations. We cannot have the master write the log for the state space creation as this interferes with other write requests for the slaves leading to an unreadable file.
            IF (rank == zero_int) THEN
                CALL record_solution(1)
                CALL record_solution(-1)
            END IF

            IF (rank == zero_int) CALL record_solution(2)

            CALL fort_calculate_rewards_systematic(periods_rewards_systematic, num_periods, states_number_period, states_all, edu_start, coeffs_a, coeffs_b, coeffs_edu, coeffs_home, max_states_period)

            IF (rank == zero_int) CALL record_solution(-1)

            IF (rank == zero_int) CALL record_solution(3)

            CALL fort_backward_induction_slave(periods_emax, num_periods, periods_draws_emax, states_number_period, periods_rewards_systematic, mapping_state_idx, states_all, shocks_cholesky, delta, is_debug, is_interpolated, num_points_interp, is_myopic, edu_start, edu_max, is_ambiguity, measure, level, optimizer_options, num_states_slaves, .True.)

            IF (rank == zero_int .AND. .NOT. is_myopic) THEN
                CALL record_solution(-1)
            ELSEIF (rank == zero_int) THEN
                CALL record_solution(-2)
            END IF

        ELSEIF (task == 3) THEN

            IF (.NOT. ALLOCATED(data_est)) THEN

                CALL read_dataset(data_est, num_agents_est)

                CALL create_draws(periods_draws_prob, num_draws_prob, seed_prob, is_debug)

                ALLOCATE(contribs(num_agents_est * num_periods))

                ALLOCATE(data_slave(num_obs_slaves(rank + 1), 8))

                ALLOCATE(displs(num_slaves))

                lower_bound = SUM(num_obs_slaves(:rank)) + 1
                upper_bound = SUM(num_obs_slaves(:rank + 1))

                data_slave = data_est(lower_bound:upper_bound, :)

                DO i = 1, num_slaves
                    displs(i) = SUM(num_obs_slaves(:i - 1))
                END DO

            END IF

            CALL fort_calculate_rewards_systematic(periods_rewards_systematic, num_periods, states_number_period, states_all, edu_start, coeffs_a, coeffs_b, coeffs_edu, coeffs_home, max_states_period)

            CALL fort_backward_induction_slave(periods_emax, num_periods, periods_draws_emax, states_number_period, periods_rewards_systematic, mapping_state_idx, states_all, shocks_cholesky, delta, is_debug, is_interpolated, num_points_interp, is_myopic, edu_start, edu_max, is_ambiguity, measure, level, optimizer_options, num_states_slaves, .False.)

            CALL fort_contributions(contribs(lower_bound:upper_bound), periods_rewards_systematic, mapping_state_idx, periods_emax, states_all, shocks_cholesky, data_slave, periods_draws_prob, delta, tau, edu_start, edu_max, num_periods, num_draws_prob)

            CALL MPI_GATHERV(contribs(lower_bound:upper_bound), num_obs_slaves(rank + 1), MPI_DOUBLE, contribs, 0, displs, MPI_DOUBLE, 0, PARENTCOMM, ierr)

        END IF

    END DO

END PROGRAM
!******************************************************************************
!******************************************************************************
