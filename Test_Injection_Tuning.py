import time
import random
import math
import sys

stage_2_injection_efficiency_pv = "ICT1400-01:PCT1402-01:InjEff:fbk"

stv1 = "STV1400-01:adc"
stv2 = "STV1400-02:adc"
stv3 = "STV1400-03:adc"
sth1 = "STH1400-01:adc"
sth2 = "STH1400-02:adc"
sth3 = "STH1400-03:adc"

stv1_increment = 10000
stv2_increment = 20000
stv3_increment = 20000
sth1_increment = 100000
sth2_increment = 50000
sth3_increment = 50000

steering_magnets = [stv1, stv2, stv3, sth1, sth2, sth3]
steering_magnet_increments = [stv1_increment, stv2_increment, stv3_increment, sth1_increment, sth2_increment, sth3_increment]

magnet_to_increment = {stv1: stv1_increment, stv2: stv2_increment, stv3: stv3_increment,
                       sth1: sth1_increment, sth2: sth2_increment, sth3: sth3_increment}

pretend_steering_magnet_vals = [1250000, 200000, 300000, 2000000, 300000, 600000]

current_steering_magnet = stv1


def caget(pv):
    global steering_magnets
    global steering_magnet_increments

    if pv in steering_magnets:
        return pretend_steering_magnet_vals[steering_magnets.index(pv)]


def caput(pv, val, wait=True):
    global steering_magnets
    global pretend_steering_magnet_vals

    if pv in steering_magnets:
        pretend_steering_magnet_vals[steering_magnets.index(pv)] = val


''' 
    NOTE: JUST FOR TESTING STV1400-01
    This function determines the desirability of our output. Since we are just trying
    to maximize the injection efficiency, we just return it without modification
'''
def objectiveFunction():

    #center of flat top stv1-1400 = 1350000 with inj_eff = 97
    #flat top extends 2 notches to left and right from the center
    magnet_to_inj_eff = {1230000: 0, 1240000: 20, 1250000: 40, 1260000: 60, 1270000: 70, 1280000: 80, 1290000: 90,  
                         1300000: 96, 1310000: 97, 1320000: 97, 1330000: 97, 1340000: 97, 1350000: 97, 1360000: 96, 
                         1370000: 90, 1380000: 80, 1390000: 70, 1400000: 60, 1410000: 40, 1420000: 20, 1430000: 0  }
    
    return magnet_to_inj_eff[pretend_steering_magnet_vals[0]] + random.randint(0, 5)



def optimizeSteeringMagnetVariation1(pv_name, step, max_iterations):

   
    
    global latest_injection_efficiency

    done = False

    magnet_val = caget(pv_name)
    initial_magnet_val = magnet_val

    magnet_val_and_inj_eff = []


    iteration = 0
    direction = 1

    injection_efficiency = objectiveFunction()
    max_injection_efficiency = injection_efficiency

    while not done:

        magnet_val = magnet_val + step * direction
        caput(pv_name, magnet_val, wait=True)

        injection_efficiency = objectiveFunction()
        if injection_efficiency > max_injection_efficiency:
            max_injection_efficiency = injection_efficiency

        if direction == 1:          # if we are going to the right
            magnet_val_and_inj_eff.append((magnet_val, injection_efficiency))
        elif direction == -1:       # if we are going to the left
            magnet_val_and_inj_eff.insert(0, (magnet_val, injection_efficiency))

        if injection_efficiency <= max_injection_efficiency * 0.8:
            if direction == 1:
                direction = -1
                magnet_val = initial_magnet_val
                caput(pv_name, initial_magnet_val, wait=True)
            else:
                done = True

        iteration += 1
        if iteration > max_iterations:      # just terminate the algorithm if we go past max iterations
            print("Reached max iteration - terminating algorithm")
            return
        
    
    done_clipping = False
    worst_magnet = "left"
    if magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1][1] < magnet_val_and_inj_eff[0][1]:
        worst_magnet = "right"

    while not done_clipping:

        if worst_magnet == "left":
            magnet_val_and_inj_eff = magnet_val_and_inj_eff[1:]
        elif worst_magnet == "right":
            magnet_val_and_inj_eff = magnet_val_and_inj_eff[0:len(magnet_val_and_inj_eff) - 1]

        new_worst_magnet = "left"
        if magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1][1] < magnet_val_and_inj_eff[0][1]:
            new_worst_magnet = "right"
        
        if new_worst_magnet != worst_magnet:
            done_clipping = True
  

    best_magnet_val = magnet_val_and_inj_eff[math.floor(len(magnet_val_and_inj_eff)/2)][0]
    caput(pv_name, best_magnet_val, wait=True)
        
    
  
    print("Done tuning " + str(pv_name) + ", final magnet value: " + str(best_magnet_val))


'''
    This simple algorithm is the same as variation 1, with the caveat that we take the 
    weighted mean center of the final 'strip chart' rather than just the center
    pv_name - the PV name of the steering magnet to tune
    step - how large of a step to take for each adjustment
    max_iterations - the maximum number of iterations before terminating the algorithm
'''
def optimizeSteeringMagnetVariation2(pv_name, step, max_iterations):

    done = False

    magnet_val = caget(pv_name)
    initial_magnet_val = magnet_val

    magnet_val_and_inj_eff = []


    iteration = 0
    direction = 1

    injection_efficiency = objectiveFunction()
    max_injection_efficiency = injection_efficiency

    while not done:

        magnet_val = magnet_val + step * direction
        caput(pv_name, magnet_val, wait=True)

        injection_efficiency = objectiveFunction()
        if injection_efficiency > max_injection_efficiency:
            max_injection_efficiency = injection_efficiency

        if direction == 1:          # if we are going to the right
            magnet_val_and_inj_eff.append([magnet_val, injection_efficiency])
        elif direction == -1:       # if we are going to the left
            magnet_val_and_inj_eff.insert(0, [magnet_val, injection_efficiency])

        if injection_efficiency <= max_injection_efficiency * 0.8:
            if direction == 1:
                direction = -1
                magnet_val = initial_magnet_val
                caput(pv_name, initial_magnet_val, wait=True)
            else:
                done = True

        iteration += 1
        if iteration > max_iterations:      # just terminate the algorithm if we go past max iterations
            print("Reached max iteration - terminating algorithm")
            return
        
    
    # here we clip the 'tail' so to speak so that we can find the approximate center of the flat top
    done_clipping = False
    worst_magnet = "left"
    if magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1][1] < magnet_val_and_inj_eff[0][1]:
        worst_magnet = "right"

    while not done_clipping:

        if worst_magnet == "left":
            magnet_val_and_inj_eff = magnet_val_and_inj_eff[1:]
        elif worst_magnet == "right":
            magnet_val_and_inj_eff = magnet_val_and_inj_eff[0:len(magnet_val_and_inj_eff) - 1]

        new_worst_magnet = "left"
        if magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1][1] < magnet_val_and_inj_eff[0][1]:
            new_worst_magnet = "right"
        
        if new_worst_magnet != worst_magnet:
            done_clipping = True



    #here we equalize the leftmost and rightmost injection efficiencies
    leftmost_inj_eff = magnet_val_and_inj_eff[0][1]
    rightmost_inj_eff = magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1][1]

    if leftmost_inj_eff < rightmost_inj_eff:
        magnet_val_and_inj_eff[0][1] = rightmost_inj_eff
    elif rightmost_inj_eff < leftmost_inj_eff:
        magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1][1] = leftmost_inj_eff

    
    #duplicate the edges before applying moving average
    magnet_val_and_inj_eff.insert(0, magnet_val_and_inj_eff[0])
    magnet_val_and_inj_eff.append(magnet_val_and_inj_eff[len(magnet_val_and_inj_eff)-1])

    #apply moving average to smooth out noise
    for i in range(1, len(magnet_val_and_inj_eff) - 2):
        
        avg = (magnet_val_and_inj_eff[i-1][1] + magnet_val_and_inj_eff[i][1] + magnet_val_and_inj_eff[i+1][1])/3
        magnet_val_and_inj_eff[i][1] = avg

    #find the weighted mean center
    sum_weights = 0             # sum of all values (weights)
    prod_xweights = 0           # product of all corresponding weights and positions
    weighted_mean_center = 0    # weighted mean center

    for i, val in enumerate(magnet_val_and_inj_eff):
        sum_weights += val[1]
        prod_xweights += (i + 1) * val[1]
    
    weighted_mean_center = int(prod_xweights / sum_weights - 1)
    if weighted_mean_center < 0:
        weighted_mean_center = 0
    
    best_magnet_val = magnet_val_and_inj_eff[weighted_mean_center][0]

    caput(pv_name, best_magnet_val, wait=True)
        
    
    print("Done tuning " + str(pv_name) + ", final magnet value: " + str(best_magnet_val))


    
arg1 = str(sys.argv[1])
arg2 = int(sys.argv[2])

magnet_name = arg1.upper()
if magnet_name[:-4] != ":adc":
    magnet_name += ":adc"

if arg2 == 1:
    optimizeSteeringMagnetVariation1(magnet_name, magnet_to_increment[magnet_name], 100)
if arg2 == 2:
    optimizeSteeringMagnetVariation2(magnet_name, magnet_to_increment[magnet_name], 100)