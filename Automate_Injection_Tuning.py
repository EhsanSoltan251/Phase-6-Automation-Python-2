from epics import caget, caput, cainfo, ca
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

latest_injection_efficiency = 0

#whether we've gotten a new injection efficiency value
got_new_injection_efficiency = False

#function to be called on injection efficiency PV change
def onChange(pvname=stage_2_injection_efficiency_pv, value=None, **kw):
    global latest_injection_efficiency
    global got_new_injection_efficiency

    latest_injection_efficiency = value
    got_new_injection_efficiency = True


''' 
    This function determines the desirability of our output. Since we are just trying
    to maximize the injection efficiency, we just return it without modification
'''
def objectiveFunction():
    global got_new_injection_efficiency
    global latest_injection_efficiency

    #wait until we get a new injection efficiency
    while not got_new_injection_efficiency:
        time.sleep(0.01)
    
    got_new_injection_efficiency = False #since we just used it, this value becomes stale
    return latest_injection_efficiency


def optimizeSteeringMagnet(pv_name, step, max_iterations):
    
    global latest_injection_efficiency

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
                return
        else:
            val = new_val
            fitness = new_fitness
        
        iteration += 1
        if iteration > max_iterations:
            return
    
        print("Done tuning " + str(pv_name))


'''
    Tunes each magnet one by one
    Params:
        steering_magnet_pvs - a list containing the pv names of each steering magnet to tune in order
        step_sizes - the step sizes to adjust each magnet (must be same order as steering_magnet_pvs)
'''
def performInjectionTuning(steering_magnet_pvs, step_sizes):

    #subscribe to the injection efficiency PV. every time it changes we call the above OnChange() function
    injection_efficiency_channel = ca.create_channel(stage_2_injection_efficiency_pv)
    eventID = ca.create_subscription(injection_efficiency_channel, callback=onChange)

    for i in range(len(steering_magnet_pvs)):
        optimizeSteeringMagnet(steering_magnet_pvs[i], step_sizes[i], 100)

    print("Done tuning all steering magnets")
    ca.clear_subscription(injection_efficiency_channel) #unsubscribe from pv