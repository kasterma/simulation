import random
from collections import Counter

N = 7  # number of islands

def prior(theta):
    """Unnormalized prior of island population"""
    if theta < 1 or theta > N:
        return 0
    return theta

def next(location):
    # if at the ends always propose existing island, don't get the right distribution
    #if 1 < location < N:
    #    proposed = location + random.choice([-1, 1])
    #elif location == 1:
    #    proposed = 2
    #else:
    #    proposed = N - 1

    proposed = location + random.choice([-1, 1])   # this one works

    # make the islands circular
    #    after island N we have island 1
    #    before island 1 we have island N
    # this change does get the right distribution
    #if proposed == 0:
    #    proposed = N
    #if proposed == N + 1:
    #    proposed = 1

    if random.random() < prior(proposed) / prior(location):
        return proposed
    else:
        return location

def walk(k = 100):
    start = random.randint(1, N)
    locs = [start]
    for _ in range(k):
        locs.append(next(locs[-1]))
    return locs

def normalize(cts):
    total = sum(cts.values())
    return {k: v/total for k,v in cts.items()}

def run_display(k=100):
    distribution_true = normalize({i:i for i in range(1,N+1)})
    distribution_simulated = normalize(Counter(walk(k)))
    for i in range(1, N+1):
        print(f"{i}, {distribution_true.get(i, 0):.3f}, {distribution_simulated.get(i, 0):.3f}")
