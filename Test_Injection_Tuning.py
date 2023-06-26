import time

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
steering_magnet_increments = [stv1_increment, stv2_increment, stv3_increment,
                              sth1_increment, sth2_increment, sth3_increment]

pretend_steering_magnet_vals = [100000, 200000, 300000, 2000000, 300000, 600000]

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
    This function determines the desirability of our output. Since we are just trying
    to maximize the injection efficiency, we just return it without modification
'''
def objectiveFunction():

    total = 0
    for val in pretend_steering_magnet_vals:
        total += val / 100000
    
    return total


def optimizeSteeringMagnet(pv_name, step, max_iterations):
    
    global current_steering_magnet
    current_steering_magnet = pv_name

    done = False
    val = caget(pv_name)
    iteration = 0
    direction = -1

    fitness = objectiveFunction()

    while not done:

        new_val = val + step * direction
        caput(pv_name, new_val, wait=True)
        new_fitness = objectiveFunction()

        if new_fitness < fitness:
            direction = direction * -1
            caput(pv_name, val, wait=True)

            #if it's not the first iteration and the injection efficiency got worse, then we know we stepped over the maximum
            if iteration != 0:
                print("Done tuning ", pv_name)
                return
        else:
            val = new_val
            fitness = new_fitness

        print("magnet val: ", val, " direction ", direction)
        
        iteration += 1
        if iteration > max_iterations:
            print("Done tuning ", pv_name)
            return
    
'''
    Tunes each magnet one by one
    Params:
        steering_magnet_pvs - a list containing the pv names of each steering magnet to tune in order
        step_sizes - the step sizes to adjust each magnet (must be same order as steering_magnet_pvs)
'''
def performInjectionTuning(steering_magnet_pvs, step_sizes):

    for i in range(len(steering_magnet_pvs)):
        optimizeSteeringMagnet(steering_magnet_pvs[i], step_sizes[i], 10)
        print("Pretend injection efficiency: ", objectiveFunction())

    print("Done tuning all steering magnets")

performInjectionTuning(steering_magnets, steering_magnet_increments)