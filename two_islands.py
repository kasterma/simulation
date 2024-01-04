import random
from collections import Counter

probs_unnormalized = [1, 5]
probs = [v/sum(probs_unnormalized) for v in probs_unnormalized]
P_01 = 0.01
P_10 = probs[0]/probs[1] * P_01

print(P_01, P_10)

def walk(k=100):
    locs = [0]
    for _ in range(k):
        if locs[-1] == 0:
            next_loc = 1 if random.random() < P_01 else 0
        else:
            next_loc = 0 if random.random() < P_10 else 1
        locs.append(next_loc)
    return locs

def norm(cts):
    tot = sum(cts.values())
    return {k:v/tot for k,v in cts.items()}

# Note: always converges to the right probabilities, but much quicker
# if high transition probabilities.

print(norm(Counter(walk(1_000))))  # try different P_01, and different walk lengths
