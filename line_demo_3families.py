#!python3

"""
Demonstration of the line-allocation protocol for three families.

See: https://arxiv.org/abs/1709.02564 Theorem 5.8 for details.
"""

import line_protocol, logging
from agents import *
from families import Family
from utils import demo
import fairness_criteria


line_protocol.logger.setLevel(logging.INFO)

# Define fairness criteria:
goods = "uvwxyz"
u='u'; v='v'; w='w'; x='x'; y='y'; z='z'
k = 3 # num of families
PropStar =  fairness_criteria.ProportionalExceptC(num_of_agents=k, c=k-1)
family1 = Family([
    AdditiveAgent({u:1, v:1,w:2,x:4,y:8,z:16}, 7),
    AdditiveAgent({u:16, v:16,w:8,x:4,y:2,z:1}, 2)],
    PropStar, name="Group 1")
family2 = Family([
    AdditiveAgent({u:1, v:1,w:1,x:3,y:3,z:4}, 5),
    AdditiveAgent({u:4, v:4,w:3,x:1,y:3,z:1}, 1)],
    PropStar, name="Group 2")
family3 = Family([
    AdditiveAgent({u:1, v:1,w:1,x:2,y:3,z:3}, 9),
    AdditiveAgent({u:3, v:3,w:3,x:2,y:1,z:1}, 3)],
    PropStar, name="Group 3")

print("\n\n\ndemocratic-fair allocation among three groups:")
demo(line_protocol.allocate, [family1, family2, family3], goods)

