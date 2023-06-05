from epics import caget, caput, cainfo, ca
import sys
import time
import math

shot_rate_pv = "PCT1402-01:mAChange"
knob_pv = "PHS1032-06:degree"

last_shot_rate = -1
fresh_shot_rate = False

all_positive_shot_rates = []


#function to be called on shot rate PV change
def onChange(pvname=shot_rate_pv, value=None, **kw):
    global last_shot_rate
    global fresh_shot_rate

    if last_shot_rate > 0:
        last_shot_rate = value
        fresh_shot_rate = True


''' the optimizer uses this to determine the desirability of each solution
'''
def objectiveFunction():
    global last_shot_rate
    global fresh_shot_rate
    global all_positive_shot_rates

    #wait until the next positive shot rate
    while not fresh_shot_rate: 
          time.sleep(0.01)

    #got fresh shot rate
    all_positive_shot_rates.append(last_shot_rate)
    fresh_shot_rate = False
    
    '''output is just a parabola with max (1) at x = 0.6
    ideally shot rate is 0.6 but 0.4-0.8 are acceptable'''
    y = -4 * (last_shot_rate - 0.6) ** 2 + 1
    return y

def optimizePV(step, goal_shot_rate_min, goal_shot_rate_max, max_iterations):
    
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
        
        if len(all_positive_shot_rates) >= 3:
            last_three_in_range = True
            for shot in all_positive_shot_rates[-3:]:
                if shot < goal_shot_rate_min or shot > goal_shot_rate_max:
                    last_three_in_range = False
            if last_three_in_range:
                return
        
        iteration += 1
        if iteration > max_iterations:
            return
    
        print("Done")


#optimizePV(0.05, 0.4, 0.8, 200)
        
        







