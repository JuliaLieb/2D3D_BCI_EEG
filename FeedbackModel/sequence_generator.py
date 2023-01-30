"""
Creates sequences with tasks repeated randomly and saves them as text file.
"""

import os
import random


def create_sequence(trials, my_tasks):
    """Creates a sequence with tasks repeated randomly.

    Parameters
    ----------
    trials: `int`
        The number of trials for each task.
    my_tasks: `list`
        The list of tasks.

    Returns
    -------
    my_sequence: `list`
        A list with the tasks repeated in random order.
    """
    my_sequence = []

    for t in range(trials):
        for i in range(len(my_tasks)):
            my_sequence.append(my_tasks[i])

    random.shuffle(my_sequence)
    return my_sequence


def sequence_generator(N_trials, N_runs):
    tasks = ["r", "l"]  # left and right hand

    directory = "FeedbackModel/data/sequences/"

    if not os.path.exists(directory):
        os.makedirs(directory)

    for r in range(N_runs):
        sequence = create_sequence(N_trials, tasks)

        file_object = open(directory + "run_" + str(r + 1) + ".txt", "w")
        for trial in sequence:
            file_object.write(trial + "\n")
