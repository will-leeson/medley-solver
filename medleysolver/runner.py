import numpy as np, csv, tqdm
import time
from collections import OrderedDict
from medleysolver.compute_features import get_features
from medleysolver.constants import SOLVERS, Result, Solved_Problem, SAT_RESULT, UNSAT_RESULT, is_solved, is_error
from medleysolver.distributions import ExponentialDist
from medleysolver.dispatch import run_problem, simulate_problem

def execute(problems, output, classifier, time_manager, timeout, feature_setting, extra_time_to_first, reward):
    mean = 0
    writer = csv.writer(open(output, 'w'))
    writer.writerow(['problem',
    'datapoint',
    'solve_method',
    'time',
    'result',
    'order',
    'time_spent'])

    for c, prob in tqdm.tqdm(enumerate(problems, 1)): 
        # start = time.time()
        try:
            point = np.array(get_features(prob, feature_setting))
        except:    
            continue
        #normalizing point
        mean = (c - 1) / c * mean + 1 / c * point
        point = point / (mean+1e-9)

        order = classifier.get_ordering(point, c, prob)
        times = classifier.get_nearby_times(point, c)
        # end = time.time()

        # solver, elapsed, result, rewards, time_spent = apply_ordering(prob, order, timeout - (end - start), time_manager, extra_time_to_first, times, reward, point)
        # solved_prob = Solved_Problem(prob, point, solver, elapsed + (end - start), result, order, time_spent)

        solver, elapsed, result, rewards, time_spent = apply_ordering(prob, order, timeout, time_manager, extra_time_to_first, times, reward, point)
        solved_prob = Solved_Problem(prob, point, solver, elapsed, result, order, time_spent)

        classifier.update(solved_prob, rewards)

        writer.writerow(solved_prob)


def apply_ordering(problem, order, timeout, time_manager, extra_time_to_first, times, reward, point):
    elapsed = 0
    rewards = [-1 for _ in SOLVERS] # negative rewards should be ignored. 
    time_spent = []
    timeout = int(timeout)

    budgets = [int(time_manager.get_timeout(solver, times, problem, point))+1 for solver in order]

    for i in range(len(budgets)):
        budgets[i] = min(budgets[i], max(0, int(timeout - sum(budgets[:i]))))

    if sum(budgets) < timeout:
        if extra_time_to_first:
            budgets[0] = budgets[0] + (timeout - sum(budgets))
        else:
            budgets[-1] = budgets[-1] + (timeout - sum(budgets))

    assert(timeout == sum(budgets))

    order = [order[i] for i in range(len(order)) if budgets[i] > 0]

    for i in range(len(order)):
        solver = order[i]
        time_for_solver = int(timeout - elapsed) + 1 if i == len(order) - 1 else budgets[i]
        # res = run_problem(solver, SOLVERS[solver], problem, time_for_solver)
        res = simulate_problem(solver, SOLVERS[solver], problem, time_for_solver)
        if reward == "binary":
            reward = 1 if is_solved(res.result) else 0
        elif reward == "bump":
            reward = 1 + ((1 - res.elapsed / timeout) ** 4) if is_solved(res.result) else 0
        elif reward == "exp":
            reward = (1 - res.elapsed / timeout) ** 4 if is_solved(res.result) else 0

        rewards[list(SOLVERS.keys()).index(solver)] = reward
        time_spent.append(res.elapsed)

        elapsed += res.elapsed
        time_manager.update(solver, res.elapsed, timeout, is_solved(res.result), is_error(res.result), point)
        if elapsed >= timeout or is_solved(res.result) or i == len(order) - 1:
            return solver, elapsed, res.result, rewards, time_spent
