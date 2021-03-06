#!python3

"""
RWAV protocol - Round-Robin with Approval Voting (for families with binary agents)

See: https://arxiv.org/abs/1709.02564 subsections 3.2 and 5.4 for details.
"""

from functools import lru_cache
from collections import defaultdict
from families import *
from utils import plural

import logging, sys
logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))
# To enable tracing, logger.setLevel(logging.INFO)


def allocate(families:list, goods: set)->list:
    """
    Run the RWAV protocol (Round Robin with Weighted Voting) on the given families.
    :return a list of bundles - a bundle per family.

    >>> fairness_1_of_best_2 = fairness_criteria.OneOfBestC(2)
    >>> family1 = Family([BinaryAgent({"w","x"},1),BinaryAgent({"x","y"},2),BinaryAgent({"y","z"},3), BinaryAgent({"z","w"},4)], fairness_1_of_best_2)
    >>> family2 = Family([BinaryAgent({"w","z"},2),BinaryAgent({"z","y"},3)], fairness_1_of_best_2)
    >>> (bundle1,bundle2) = allocate([family1, family2], ["w","x","y","z"])
    >>> sorted(bundle1)
    ['x', 'z']
    >>> sorted(bundle2)
    ['w', 'y']
    """
    # Calculate target value for each member in each family:
    for family in families:
        for member in family.members:
            member.target_value = family.fairness_criterion.target_value_for_binary(member.total_value)


    num_of_families = len(families)
    remaining_goods=set(goods)
    bundles = [set() for f in families]

    turn_index = 0
    family_index = 0
    while len(remaining_goods) > 0:
        current_family = families[family_index]
        current_family_bundle = bundles[family_index]
        logger.info("\nTurn #{}: {}'s turn to pick a good from {}:".format(turn_index + 1, current_family.name, sorted(remaining_goods)))
        g = choose_good(current_family, current_family_bundle, remaining_goods, num_of_families)
        logger.info("{} picks {}".format(current_family.name, g))
        current_family_bundle.add(g)
        remaining_goods.remove(g)
        turn_index += 1
        family_index = (family_index + 1) % num_of_families
    return bundles




# templates for printing to logger:
AGENT_WEIGHT_FORMAT = "{0: <12}{1: <12}{2: <3}{3: <3}{4: <9}"
GOODS_WEIGHT_FORMAT = "{0: <6}{1: <9}"



def choose_good(family:Family, owned_goods:set, remaining_goods:set, num_of_families:int=2)->str:
    """
    Calculate the good that the family chooses from the set of remaining goods.
    It uses weighted-approval-voting.

    >>> agent1 = BinaryAgent({"x","y"})
    >>> agent2 = BinaryAgent({"z","w"})
    >>> fairness_1_of_best_2 = fairness_criteria.OneOfBestC(2)
    >>> family = Family([agent1,agent2], fairness_criterion=fairness_1_of_best_2, name="Family 1")
    >>> agent1.target_value = agent2.target_value = 1
    >>> choose_good(family, set(), {"x","y","z"})
    'z'
    """
    map_good_to_total_weight = defaultdict(int)
    choose_good.logger.info("Member weights:")
    choose_good.logger.info(AGENT_WEIGHT_FORMAT.format("","Desired set","r","s","weight"))
    for member in family.members:
        current_member_weight           = member_weight(member, member.target_value, owned_goods, remaining_goods, num_of_families)
        for good in member.desired_goods:
            map_good_to_total_weight[good] += current_member_weight * member.cardinality

    choose_good.logger.info("Remaining good weights:")
    choose_good.logger.info(GOODS_WEIGHT_FORMAT.format("","Weight"))
    for good in remaining_goods:
        choose_good.logger.info(GOODS_WEIGHT_FORMAT.format(good, map_good_to_total_weight[good]))
    return min(remaining_goods, key=lambda good: (-map_good_to_total_weight[good], good))
choose_good.logger=logging.getLogger("choose_good")


def member_weight(member: BinaryAgent, target_value: int, owned_goods: set, remaining_goods: set, num_of_families:int=2) -> float:
    """
    Calculate the voting-weight of the given member with the given owned goods and remaining goods.

    >>> Alice = BinaryAgent({"w","x"})
    >>> Bob   = BinaryAgent({"w","x","y","z"})
    >>> member_weight(Alice, 1, set(), {"x","y","z"})
    0.5
    >>> member_weight(Bob, 2, set(), {"x","y","z"})
    0.375
    """
    member_remaining_value = member.value(remaining_goods)  # the "r" of the member
    member_current_value = member.value(owned_goods)
    member_should_get_value = target_value - member_current_value  # the "s" of the member
    the_member_weight = weight(member_remaining_value, member_should_get_value, num_of_families)
    members_string = "{} member{}".format(member.cardinality, plural(member.cardinality))
    desired_goods_string = ",".join(sorted(member.desired_goods))
    member_weight.logger.info(AGENT_WEIGHT_FORMAT.format(
        members_string, desired_goods_string,
        member_remaining_value, member_should_get_value, the_member_weight))
    return the_member_weight
member_weight.logger = logging.getLogger("member_weight")




@lru_cache(maxsize=None)
def balance(r:int, s:int, k:int=2)->float:
    """
    Calculates the function B_k(r,s), which represents
       the balance of a user with r remaining goods and s missing goods.
    Uses the recurrence relation in https://arxiv.org/abs/1709.02564 .

    >>> balance(0,0)
    1
    >>> balance(1,1)
    0.5
    >>> balance(1,0)
    1
    >>> balance(0,1)
    0
    >>> balance(3,2)
    0.375
    >>> balance(0,-2)
    1
    >>> balance(-1,1)
    0
    >>> balance(5,0,k=3)
    1
    >>> balance(0,1,k=3)
    0
    """
    if (s<=0):
        return 1
    if (s>r):
        return 0
    if k==2:
        val1 = (balance(r-1,s)+balance(r-1,s-1))/2
        val2 = balance(r-2,s-1)
        return min(val1,val2)
    elif k>2:
        if s>1:
            raise(ValueError("When there are more than 2 families, we do not know how to calculate weights for members with s>1"))
        elif s==1:
            Lk = math.pow(2,1/(k-1))
            return 1 - 1/math.pow(Lk,r)
    raise(ValueError("Illegal values: r={} s={} k={}").format(r,s,k))


@lru_cache(maxsize=None)
def weight(r:int, s:int, k:int=2)->float:
    """
    Calculates the function w(r,s), which represents
       the voting weight of a user with r remaining goods and s missing goods.

    >>> float(weight(4,0))
    0.0
    >>> float(weight(0,2))
    0.0
    >>> weight(1,1)
    0.5
    >>> weight(4,2)
    0.25
    >>> weight(4,3)
    0.0
    >>> float(weight(4,-2))
    0.0
    >>> weight(5,0,k=3)
    0
    >>> weight(0,1,k=3)
    0
    """
    return balance(r, s, k) - balance(r - 1, s, k)


if __name__ == "__main__":
    import doctest
    (failures,tests) = doctest.testmod(report=True)
    print ("{} failures, {} tests".format(failures,tests))
