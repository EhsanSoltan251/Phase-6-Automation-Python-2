from epics import caget, caput, cainfo, ca
import time
import sys

shot_rate_pv = "PCT1402-01:mAChange"
knob_pv = "PHS1032-06:degree"

last_shot_rate = -1
fresh_shot_rate = False
all_shot_rates = []

#function to be called on shot rate PV change
def onChange(pvname=shot_rate_pv, value=None, **kw):
    global last_shot_rate
    global fresh_shot_rate

    if value > 0:
        last_shot_rate = value
        fresh_shot_rate = True
        
'''A test objective function instead of reading the shot rate from EPICS'''
def testObjectiveFunction(solution):
    global last_shot_rate
    global fresh_shot_rate

    #a function to rather crudely simulate the shot rate
    last_shot_rate = -1.0/4 * (solution - 117.25) ** 2.0 + 0.6

    #shot rate is now positive
    last_positive_shot_rate = last_shot_rate
    all_shot_rates.append(last_positive_shot_rate)
    fresh_shot_rate = False
    
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
    The first optimization method, which essentially mimics what an operator would do manually
    Parameters:
        step - the step size to adjust the knob pv
        goal_shot_rate_min - the minimum acceptable shot rate
        goal_shot_rate_max - the maximum acceptable shot rate
        max_iterations - the maximum number of adjustments to perform before terminating the function
'''
def optimizePV_Standard(step, goal_shot_rate_min, goal_shot_rate_max, max_iterations):

    global all_shot_rates
    all_shot_rates = []

    #subscribe to the shot rate PV. every time it changes we call the above OnChange() function
    shot_rate_channel = ca.create_channel(shot_rate_pv)
    eventID = ca.create_subscription(shot_rate_channel, callback=onChange)
    
    done = False
    val = caget(knob_pv)
    iteration = 0
    direction = -1


    caput(knob_pv, val, wait=True)
    fitness = objectiveFunction()

    while not done:
        
        new_val = val + step * direction
        caput(knob_pv, new_val, wait=True)
        new_fitness = objectiveFunction()

        if new_fitness < fitness:
            direction = direction * -1
            caput(knob_pv, val, wait=True)
        else:
            val = new_val
            fitness = new_fitness
        
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
        print("Done tuning")

'''
    The same as the first method, but with a relatively large step size that decreases
'''
def optimizePV_DecreasingStep(min_step, max_step, goal_shot_rate_min, goal_shot_rate_max, max_iterations):

    global all_shot_rates
    all_shot_rates = []

    step = max_step

    #subscribe to the shot rate PV. every time it changes we call the above OnChange() function
    shot_rate_channel = ca.create_channel(shot_rate_pv)
    eventID = ca.create_subscription(shot_rate_channel, callback=onChange)
    
    done = False
    val = caget(knob_pv)
    iteration = 0

    direction = -1

    caput(knob_pv, val, wait=True)
    fitness = objectiveFunction()

    while not done:

        new_val = val + step * direction
        caput(knob_pv, new_val, wait=True)
        new_fitness = objectiveFunction()

        if new_fitness < fitness:
            direction = direction * -1
            caput(knob_pv, val, wait=True)
            if iteration != 0 and step > min_step:
                step -= 0.5
        else:
            val = new_val
            fitness = new_fitness
        
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
    print("Done tuning")


'''
    The same as the first method, but takes average of multiple measurements of shot rate to account for fluctuations
    Parameters:
        measurements - how many measurements of the shot rate to take for each adjustment
'''
def optimizePV_MultipleMeasurements(step, goal_shot_rate_min, goal_shot_rate_max, max_iterations, measurements):
    global all_shot_rates
    all_shot_rates = []

     #subscribe to the shot rate PV. every time it changes we call the above OnChange() function
    shot_rate_channel = ca.create_channel(shot_rate_pv)
    eventID = ca.create_subscription(shot_rate_channel, callback=onChange)
    
    done = False
    val = caget(knob_pv)
    iteration = 0
    direction = -1

    caput(knob_pv, val, wait=True)
    sum = 0
    for i in range(measurements):
        sum += objectiveFunction()
    fitness = sum / measurements

    while not done:

        new_val = val + step * direction
        caput(knob_pv, new_val, wait=True)
        sum = 0
        for i in range(measurements):
            sum += objectiveFunction()
        new_fitness = sum / measurements

        if new_fitness < fitness:
            direction = direction * -1
            caput(knob_pv, val, wait=True)
        else:
            val = new_val
            fitness = new_fitness
        
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
    print("Done tuning")


def optimizePV_MultipleMeasureMentsDecreasingStep(min_step, max_step, step_decrease, goal_shot_rate_min, goal_shot_rate_max, max_iterations, measurements):
    global all_shot_rates
    all_shot_rates = []
    step = max_step
    iteration = 0

     #subscribe to the shot rate PV. every time it changes we call the above OnChange() function
    shot_rate_channel = ca.create_channel(shot_rate_pv)
    eventID = ca.create_subscription(shot_rate_channel, callback=onChange)
    
    done = False
    val = caget(knob_pv)
    direction = -1

    caput(knob_pv, val, wait=True)
    sum = 0
    for i in range(measurements):
        sum += objectiveFunction()
    fitness = sum / measurements

    while not done:

        new_val = val + step * direction
        caput(knob_pv, new_val, wait=True)
        sum = 0
        for i in range(measurements):
            sum += objectiveFunction()
        new_fitness = sum / measurements

        if new_fitness < fitness:
            direction = direction * -1
            if step > min_step:
                step -= step_decrease

            caput(knob_pv, val, wait=True)
        else:
            val = new_val
            fitness = new_fitness
        
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
    print("Done tuning")




arg = int(sys.argv[1])

if arg == 1:
    print("Starting standard tuning algorithm")
    optimizePV_Standard(0.5, 0.55, 0.65, 100)
if arg == 2:
    print("Starting tuning algorithm with multiple measurements")
    optimizePV_MultipleMeasurements(0.5, 0.55, 0.65, 300, 3)
if arg == 3:
    print("Starting tuning algorithm with decreasing step")
    optimizePV_DecreasingStep(0.5, 2.0, 0.55, 0.65, 100)
if arg == 4:
    optimizePV_MultipleMeasureMentsDecreasingStep(0.5, 1.5, 0.5, 0.55, 0.65, 200, 3)

print("Tuning complete")
        
        







