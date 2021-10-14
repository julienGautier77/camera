#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  9 11:06:21 2020

@author: juliengautier
Copy from : 

https://github.com/DEAP/deap/blob/bc77eface9f43ec1e1575f8e45df8fb375cb08d8/examples/ga/onemax.py


"""
import random
import numpy as np
from deap import base
from deap import creator
from deap import tools

creator.create("FitnessMax", base.Fitness, weights=(1.0,))

creator.create("Individual", list, fitness=creator.FitnessMax)


toolbox = base.Toolbox()
# Attribute generator 
toolbox.register("attr_bool", random.randint, 0, 10) # nombre entier entre 0 et 10
# Structure initializers
toolbox.register("individual", tools.initRepeat, creator.Individual, 
    toolbox.attr_bool, 100) # =nombre de genes de l'individu
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def evalOneMax(individual): # fonction qui evalue notre individu fonction qui va etre maximiser
    #print('eval',sum(individual))
    ### Appliquer tension au deformable
    ### Faire acquisition camera (n fois)
    ### Trouver le max ou integrer ... 
    ### return 
    print ('indv0',individual[0],individual[10])
    return sum(individual),


toolbox.register("evaluate", evalOneMax)
toolbox.register("mate", tools.cxTwoPoint) #crossOver operatuer 
toolbox.register("mutate", tools.mutFlipBit, indpb=0.05) # mutation 

# operator for selecting individuals for breeding the next
# generation: each individual of the current generation
# is replaced by the 'fittest' (best) of three individuals
# drawn randomly from the current generation :
toolbox.register("select", tools.selTournament, tournsize=3)

def main():
    pop = toolbox.population(n=50) #Generation d'une population de n individu  
    
    # Evaluation de la population initiale : 
    fitnesses = list(map(toolbox.evaluate, pop))
    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        
        #print('Value for individu',ind,':',fit)
    
    print("  Evaluated %i individuals" % len(pop))
    
    # CXPB  is the probability with which two individuals
    #       are crossed
    #
    # MUTPB is the probability for mutating an individual
    CXPB, MUTPB = 0.5, 0.2
    
    # Extracting all the fitnesses of 
    fits = [ind.fitness.values[0] for ind in pop]
    print('value find',fits)
    
    
    # Variable keeping track of the number of generations
    g = 0
    
    # Begin the evolution
    while max(fits) < 10000 and g < 10000:
        # condition de convergence et nobre max de generation
        
        
        # A new generation
        g = g + 1
        print("-- Generation %i --" % g)
        
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))
        #print(offspring)
    
    # Apply crossover (mating) and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):

            # cross two individuals with probability CXPB
            if random.random() < CXPB:
                toolbox.mate(child1, child2)

                # fitness values of the children
                # must be recalculated later
                #The del statement will invalidate the fitness of the modified offspring.
                del child1.fitness.values
                del child2.fitness.values

        for mutant in offspring:

            # mutate an individual with probability MUTPB
            if random.random() < MUTPB:
                toolbox.mutate(mutant)
                del mutant.fitness.values   # set invalid to  fitness value
                
           
    #The crossover (or mating) and mutation operators, provided within DEAP, 
    #usually take respectively 2 or 1 individual(s) as input and return 2 or 1 modified individual(s). 
    #In addition they modify those individuals within the toolbox container and we do not need to reassign their results.
#Since the content of some of our offspring changed during the last step, 
#we now need to re-evaluate their fitnesses. 
#To save time and resources, we just map those offspring which fitnesses were marked invalid.     
        
        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
    
        
    #
    #we replace the old population by the offspring.
    
        pop[:] = offspring
        fits = [ind.fitness.values[0] for ind in pop]
        print("max",max(fits))
        
        
    print("-- End of (successful) evolution --")
    
    best_ind = tools.selBest(pop, 1)[0]
    print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))

if __name__ == "__main__":
    main()
        
    