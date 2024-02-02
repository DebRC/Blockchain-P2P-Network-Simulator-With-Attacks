import random
import json

def generate_random_number(distribution, **params):
    """
    Generate a random number based on the specified distribution.

    Parameters:
    - distribution (str): The chosen distribution ('uniform', 'normal', 'exponential', etc.).
    - **params: Additional parameters specific to the chosen distribution.

    Returns:
    - float: The generated random number.
    """
    
    defaultSeed = json.load(open('params.json'))['default-seed']
    generator = random.Random(params.get('seed', defaultSeed))  # Set a seed if provided
    
    if distribution == 'uniform':
        low = params.get('low', 0)
        high = params.get('high', 1)
        return generator.uniform(low, high)
    
    elif distribution == 'normal':
        mean = params.get('mean', 0)
        std = params.get('std', 1)
        return generator.gauss(mean, std)
    
    elif distribution == 'exponential':
        scale = params.get('scale', 1)
        return generator.expovariate(1/scale)

    else:
        raise ValueError(f"Unsupported distribution: {distribution}")