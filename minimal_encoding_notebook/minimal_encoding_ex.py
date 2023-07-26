from email.generator import DecodedGenerator
from minimal_encoding import *
import warnings

import jijmodeling as jm
import jijmodeling.transpiler as jmt
import openjij as oj

from qiskit.algorithms.optimizers import COBYLA

import numpy as np
import matplotlib.pyplot as plt
import math

"""
This file is for testing the minimal encoding with Knapoack problem amd Traveral Salesman Problem (TSP).
"""

def main():
    # ignore and not displaying all warnings generated by any code
    warnings.filterwarnings('ignore')

    #set basic information
    nc = 8
    nr = math.log2(nc)
    na = 1
    nq = int(nr + na)
    l =  8

    if nr.is_integer() == False:
        print("The number of register qubits should be integer")
        return 0
    else: 
        nr = int(nr)

    #define Knapoack problem
    problem = define_knapsack()

    #create a list for price (v) and weight (w)
    price = [5000, 7000, 2000, 1000, 4000, 3000, 1500, 3200]
    weight = [800, 1000, 600, 400, 500, 300, 200, 700]
    #set the capacity (constrain)
    capacity = 2000
    data = {'v': price, 'w':weight, 'W':capacity}
    # data = knapsack_random_data(nc, 2000, 1000, 10000, 100, 1000)

    compiled_model = jmt.core.compile_model(problem, data, {})
    # Quadratic Unconstraint Binary Optimization (QUBO) model
    pubo_builder = jmt.core.pubo.transpile_to_pubo(compiled_model=compiled_model)

    qubo,const = pubo_builder.get_qubo_dict(multipliers = {'onehot': 1.0})  

    #set sampler 
    sampler = oj.SASampler()

    #solve the problem 
    result = sampler.sample_qubo(qubo)
    print(result.states)
    #decode a result to JijModeling sample set
    sampleset = jmt.core.pubo.decode_from_openjij(result,pubo_builder,compiled_model)

    #extract a solution list from sampleset.
    opt = list(sampleset.record.solution.values())
    opt = opt[0][0][0][0]

    result_price = [data['v'][i] for i in opt]
    result_weight = [data['w'][i] for i in opt]

    print('Price of chosen items: ', result_price)
    print('Weight of chosen items: ', result_weight)
    print('Total price: ', sum(result_price))
    print('Total weight: ', sum(result_weight))
    print('Constrain', data['W'])

    #minimal encoding for Knapoack problem
    parameters, theta = init_parameter(nq, l) 
    circuit = generate_circuit(nr, na, l, parameters)
    progress_history = []
    A = convert_qubo_datatype(qubo, nc)
    A = (A + A.T)/2
    print(A)
    func = init_func(nc, nr, na, circuit,A, progress_history)
    n_eval = 500
    optimizer = COBYLA(maxiter=n_eval, disp=True)
    result = optimizer.minimize(func, list(theta.values()))
    print(f"The total number of function evaluations => {result.nfev}")
    print(circuit)
    decoded_result = decode(result.x, circuit, nr)

    # a = np.array([1, 1, 1, 1, 1, 1, 1, 1])
    # at = a.T

    plt.plot(progress_history)
    plt.xlabel('number of iteration')
    plt.ylabel('value of cost function')
    plt.show()

def define_knapsack():
    # define variables
    v = jm.Placeholder('v', dim=1)
    N = v.shape[0].set_latex('N')
    w = jm.Placeholder('w', shape=(N))
    W = jm.Placeholder('W')
    x = jm.Binary('x', shape=(N))
    i = jm.Element('i', (0, N))

    # set problem
    problem = jm.Problem('Knapsack')
    # set objective function (equation (1))
    obj = - jm.Sum(i, v[i]*x[i])
    problem += obj

    # set total weight constarint (equation (2))
    const = jm.Sum(i, w[i]*x[i])
    problem += jm.Constraint('weight', const<=W)

    return problem

def knapsack_random_data(nc:int, capacity:int, price_min:int, price_max:int, weight_min:int, weight_max:int):
    """
    Function to generate random data for knapsack problem.
    
    Parameters
    ----------
    nc : int
        The number of classical bits.
    price_min : int
        The lower range of price.
    price_max : int
        The upper range of price.
    weight_min : int
        The lower range of weight.
    weight_max : int
        The upper range of weight.
    capacity : int
        The capacity of knapsack.
    
    Returns
    -------
    data : dict
        Random data for knapsack problem.
    """
    price = np.random.randint(price_min,price_max,nc)
    weight = price + np.random.randint(weight_min, weight_max ,nc)
    # set the capacity (constrain)
    capacity = capacity
    data = {'v': price, 'w':weight, 'W':capacity}  

    return data 

def convert_qubo_datatype(qubo:dict , nc:int):
    '''
    This function convert qubo define by dict to qubo define by numpy.ndarray.

    Parameters
    ----------
    qubo : dict
        QUBO define by dict.
    nc : int
        The number of classical bits.
    
    Returns
    -------
    qubo_matrix : numpy.ndarray
        QUBO define by numpy.ndarray.
    '''

    qubo_matrix = np.zeros((nc, nc))
    for key, value in qubo.items():
        qubo_matrix[key[0], key[1]] = value 
    
    return qubo_matrix


if __name__ == "__main__":
    main()