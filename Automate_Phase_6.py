from epics import caget, caput, cainfo, ca
import sys
import time
import math

shot_rate_pv = "PCT1402-01:mAChange"
knob_pv = "PHS1032-06:degree"

last_shot_rate = -1
fresh_shot_rate = False

all_shot_rates = []


#function to be called on shot rate PV change
def onChange(pvname=shot_rate_pv, value=None, **kw):
    global last_shot_rate
    global fresh_shot_rate

    if last_shot_rate > 0:
        last_shot_rate = value
        fresh_shot_rate = True
        
	
'''A test objective function instead of reading the shot rate from EPICS'''
def testObjectiveFunction(solution):
    global last_shot_rate

    #a function to rather crudely simulate the shot rate
    last_shot_rate = -1.0/4 * (solution - 117.25) ** 2.0 + 0.6

    #shot rate is now positive
    last_positive_shot_rate = last_shot_rate
    all_shot_rates.append(last_positive_shot_rate)
    last_shot_rate = -1 #set it back to -1 because we want to use a new one each time
    
    #output is just a parabola with maximum (1) at x = 0.6 ideally shot rate is 0.6 but 0.4-0.8 are acceptable
    y = -4 * (last_positive_shot_rate - 0.6) ** 2 + 1
    return y


''' the optimizer uses this to determine the desirability of each solution
'''
def objectiveFunction():
    global last_shot_rate
    global fresh_shot_rate
    global all_shot_rates

    #wait until the next positive shot rate
    while not fresh_shot_rate: 
          time.sleep(0.01)

    #got fresh shot rate
    all_shot_rates.append(last_shot_rate)
    fresh_shot_rate = False
    
    '''output is just a parabola with max (1) at x = 0.6
    ideally shot rate is 0.6 but 0.4-0.8 are acceptable'''
    y = -4 * (last_shot_rate - 0.6) ** 2 + 1
    return y



'''
    Takes a list of solutions and picks the best one based on the objective function
''' 
def pickBestSolution(solutions):
    best = solutions[0]

    for solution in solutions:
        if testObjectiveFunction(solution) > testObjectiveFunction(best):
            best = solution
    
    return best

'''
    Takes low and high bounds of interval, and returns a list containing num_values # of evenly distributed values within range
'''
def getValuesInRange(low, high, num_values):

    values = []
    interval = (high - low) / (num_values + 1)
    current_value = low

    for i in range(num_values):
        current_value += interval
        values.append(current_value)
    
    return values

'''
    The first optimization method, which essentially mimics what an operator would do manually
    Parameters:
        step - the step size to adjust the knob pv
        goal_shot_rate_min - the minimum acceptable shot rate
        goal_shot_rate_max - the maximum acceptable shot rate
        max_iterations - the maximum number of adjustments to perform before terminating the function
'''
def optimizePV(step, goal_shot_rate_min, goal_shot_rate_max, max_iterations):

    #subscribe to the shot rate PV. every time it changes we call the above OnChange() function
    shot_rate_channel = ca.create_channel(shot_rate_pv)
    eventID = ca.create_subscription(shot_rate_channel, callback=onChange)
    
    done = False
    val = caget(knob_pv)
    iteration = 0
    direction = -1

    while not done:
        caput(knob_pv, val, wait=True)
        fitness = objectiveFunction()

        new_val = val + step * direction
        caput(knob_pv, new_val, wait=True)
        new_fitness = objectiveFunction()

        if new_fitness < fitness:
            direction = direction * -1
            caput(knob_pv, val, wait=True)
        else:
            val = new_val
        
        if len(all_shot_rates) >= 3:
            last_three_in_range = True
            for shot in all_shot_rates[-3:]:
                if shot < goal_shot_rate_min or shot > goal_shot_rate_max:
                    last_three_in_range = False
            if last_three_in_range:
                return
        
        iteration += 1
        if iteration > max_iterations:
            return
    
        ca.clear_subscription(shot_rate_channel)
        print("done")

def optimizePV2(goal_shot_rate_min, goal_shot_rate_max, max_iterations):

    max_step = 2.0
    min_step = 0.5
    step = max_step

    #subscribe to the shot rate PV. every time it changes we call the above OnChange() function
    shot_rate_channel = ca.create_channel(shot_rate_pv)
    eventID = ca.create_subscription(shot_rate_channel, callback=onChange)
    
    done = False
    val = caget(knob_pv)
    iteration = 0

    direction = -1

    while not done:

        caput(knob_pv, val, wait=True)
        fitness = objectiveFunction()

        new_val = val + step * direction
        caput(knob_pv, new_val, wait=True)
        new_fitness = objectiveFunction()

        if new_fitness < fitness:
            direction = direction * -1
            caput(knob_pv, val, wait=True)
            if iteration != 0 and step_size > min_step:
                step_size -= 0.5
        else:
            val = new_val
        
        if len(all_shot_rates) >= 3:
            last_three_in_range = True
            for shot in all_shot_rates[-3:]:
                if shot < goal_shot_rate_min or shot > goal_shot_rate_max:
                    last_three_in_range = False
            if last_three_in_range:
                return


        iteration += 1
        if iteration > max_iterations:
            return
        
    ca.clear_subscription(shot_rate_channel)
    print("done")






#optimizePV(0.05, 0.4, 0.8, 200)
        
        







