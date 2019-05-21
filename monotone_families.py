#!python3

"""
Allocation algorithms for families with monotone agents:
* Line protocol (EF1 for two monotone families).

See: https://arxiv.org/abs/1709.02564 Section 4 for details.
"""

from functools import lru_cache
from collections import defaultdict
import fairness_criteria
from agents import *

class MonotoneFamily:
    """
    Represents a family of monotone agents.
    """
    def __init__(self, members:list, name:str="Anonymous Monotone Family"):
        """
        Initializes a family with the given list of members.
        :param members: a list of MonotoneAgent objects.
        """
        super().__init__(members, name)



def allocate_on_a_line(families:list, goods: set)->list:
    """
    Order the goods on a line and allocate them in an EF1 way.
    Currently only 2 families are supported.
    :return a list of bundles - a bundle per family.

    >>> family1 = MonotoneFamily([BinaryAgent({"w","x"},1),BinaryAgent({"x","y"},2),BinaryAgent({"y","z"},3), BinaryAgent({"z","w"},4)])
    >>> family2 = MonotoneFamily([BinaryAgent({"w","z"},2),BinaryAgent({"z","y"},3)])
    >>> (bundle1,bundle2) = allocate_on_a_line([family1, family2], ["w","x","y","z"])
    >>> sorted(bundle1)
    ['x', 'z']
    >>> sorted(bundle2)
    ['w', 'y']
    """
    n_families = len(families)
    if n_families!=2:
        raise("Currently only 2 families are supported")
    remaining_goods=list(goods)  # order the goods on a line
    bundles = [set() for f in families]

    ###### STOPPED HERE #########
    turn_index = 0
    family_index = 0
    while len(remaining_goods) > 0:
        current_family = families[family_index]
        current_family_bundle = bundles[family_index]
        allocate_on_a_line.trace("\nTurn #{}: {}'s turn to pick a good from {}:".format(turn_index + 1, current_family.name, sorted(remaining_goods)))
        g = choose_good(current_family, current_family_bundle, remaining_goods)
        allocate_on_a_line.trace("{} picks {}".format(current_family.name, g))
        current_family_bundle.add(g)
        remaining_goods.remove(g)
        turn_index += 1
        family_index = (family_index + 1) % n_families
    return bundles
allocate_on_a_line.trace = lambda *x: None  # To enable tracing, set allocate_using_RWAV.trace=print




AGENT_WEIGHT_FORMAT = "{0: <12}{1: <12}{2: <3}{3: <3}{4: <9}"
GOODS_WEIGHT_FORMAT = "{0: <6}{1: <9}"

def choose_good(family:BinaryFamily, owned_goods:set, remaining_goods:set)->str:
    """
    Calculate the good that the family chooses from the set of remaining goods.
    It uses weighted-approval-voting.

    >>> agent1 = BinaryAgent({"x","y"})
    >>> agent2 = BinaryAgent({"z","w"})
    >>> fairness_1_of_best_2 = lambda r: 1 if r>=2 else 0
    >>> family = BinaryFamily([agent1,agent2], fairness_1_of_best_2)
    >>> choose_good(family, set(), {"x","y","z"})
    'z'
    """
    map_good_to_total_weight = defaultdict(int)
    choose_good.trace("Calculating member weights:")
    choose_good.trace(AGENT_WEIGHT_FORMAT.format("","Desired set","r","s","weight"))
    for (member,target_value) in family.members:
        current_member_weight           = member_weight(member, target_value, owned_goods, remaining_goods)
        for good in member.desired_goods:
            map_good_to_total_weight[good] += current_member_weight * member.cardinality

    choose_good.trace("Calculating remaining good weights:")
    choose_good.trace(GOODS_WEIGHT_FORMAT.format("","Weight"))
    for good in remaining_goods:
        choose_good.trace(GOODS_WEIGHT_FORMAT.format(good, map_good_to_total_weight[good]))
    return min(remaining_goods, key=lambda good: (-map_good_to_total_weight[good], good))
choose_good.trace = lambda *x: None  # To enable tracing, set choose_good.trace=print


def member_weight(member: BinaryAgent, target_value: int, owned_goods: set, remaining_goods: set) -> float:
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
    the_member_weight = weight(member_remaining_value, member_should_get_value)
    members_string = "{} member{}".format(member.cardinality, plural(member.cardinality))
    desired_goods_string = ",".join(sorted(member.desired_goods))
    member_weight.trace(AGENT_WEIGHT_FORMAT.format(
        members_string, desired_goods_string,
        member_remaining_value, member_should_get_value, the_member_weight))
    return the_member_weight
member_weight.trace = lambda *x: None  # To enable tracing, set member_weight.trace=print



def allocate_using_enhanced_RWAV(families:list, goods: set, threshold: float):
    """
    Run the Enhanced RWAV protocol (see Section 3 in the paper) on the given families.
    Currently only 2 families are supported.
    Return a list of bundles - a bundle per family.
    :param threshold: a number in [0,1].
      If there is a single good g that is wanted by at least this fraction of members in one of the families,
      then this family gets g and the other family gets the other goods.

    >>> fairness_1_of_best_2 = fairness_criteria.one_of_best_c(2)
    >>> family1 = BinaryFamily([BinaryAgent({"w","x"},1),BinaryAgent({"x","y"},3),BinaryAgent({"y","z"},3), BinaryAgent({"w","v"},3)], fairness_1_of_best_2)
    >>> family2 = BinaryFamily([BinaryAgent({"w","x"},5),BinaryAgent({"y","z"},5)], fairness_1_of_best_2)
    >>> (bundle1,bundle2) = allocate_using_enhanced_RWAV([family1, family2], ["v","w","x","y","z"], threshold=0.6)
    >>> sorted(bundle1)
    ['y']
    >>> sorted(bundle2)
    ['v', 'w', 'x', 'z']
    >>> (bundle2,bundle1) = allocate_using_enhanced_RWAV([family2, family1], ["v","w","x","y","z"], threshold=0.6)
    >>> sorted(bundle1)
    ['y']
    >>> sorted(bundle2)
    ['v', 'w', 'x', 'z']
    """
    if len(families)!=2:
        raise("Currently only 2 families are supported")

    bundles = [set() for f in families]
    goods = set(goods)

    thresholds = [threshold*family.num_of_members() for family in families]
    for g in goods:
        nums = [family.num_of_members_who_want(g) for family in families]
        if nums[0] >= thresholds[0]:
            bundle1 = set(g)
            bundle2 = goods.difference(bundle1)
            allocate_using_enhanced_RWAV.trace("{} out of {} members in {} want {}, so group 1 gets {} and group 2 gets the rest".format(
                nums[0],     families[0].num_of_members(),     families[0].name, g,                  g))
            return (bundle1,bundle2)
        elif nums[1] >= thresholds[1]:
            bundle2 = set(g)
            bundle1 = goods.difference(bundle2)
            allocate_using_enhanced_RWAV.trace("{} out of {} members in {} want {}, so group 2 gets {} and group 1 gets the rest".format(
                nums[1],     families[1].num_of_members(),     families[1].name, g,                  g))
            return (bundle1,bundle2)
    return allocate_using_RWAV(families, goods)
allocate_using_enhanced_RWAV.trace = lambda *x: None  # To enable tracing, set allocate_using_enhanced_RWAV.trace=print


def allocate_twothirds(families:list, goods: set):
    """
    Run the protocol (see Section 3 in the paper) that guarantees to each family
    2/3-democratic 1-of-best-2 fairness.
    Currently, it works only for two identical families.

    >>> fairness_1_of_best_2 = fairness_criteria.one_of_best_c(2)
    >>> family1 = BinaryFamily([BinaryAgent("wx",1),BinaryAgent("yz",1)], fairness_1_of_best_2)
    >>> (bundle1,bundle2) = allocate_twothirds([family1, family1], "wxyz")
    >>> len(bundle1)
    2
    >>> len(bundle2)
    2
    """
    if len(families)!=2:
        raise("Currently only 2 families are supported")
    goods = set(goods)

    bundles = [set(), goods] # start, arbitrarily, with an allocation that gives all goods to family 2.
    num_of_members = sum([family.num_of_members() for family in families])
    num_of_iterations = 2*num_of_members   # this should be sufficient to convergence if the families are identical
    for iteration in range(num_of_iterations):
        # If there is a good $g\in G_1$ for which $q_0(g) > q_1(g)$, move $g$ to $G_2$.
        allocate_twothirds.trace("Currently, {} holds {} and {} holds {}".format(families[0].name, bundles[0], families[1].name, bundles[1]))
        change=False
        for g in list(bundles[0]):
            poor_in_2  = families[1].num_of_members(lambda member: member.value(g)>0 and member.value(bundles[1])==0)
            poor_in_1  = families[0].num_of_members(lambda member: member.value(g)>0 and member.value(bundles[0])==1)
            if poor_in_2>poor_in_1:
                allocate_twothirds.trace("Moving {} from {} to {}, harming {} members in and helping {}.".format(g, families[0].name, families[1].name, poor_in_1, poor_in_2))
                bundles[0].remove(g)
                bundles[1].add(g)
                change=True
        for g in list(bundles[1]):
            poor_in_1 = families[0].num_of_members(lambda member: member.value(g)>0 and member.value(bundles[0])==0)
            poor_in_2 = families[1].num_of_members(lambda member: member.value(g)>0 and member.value(bundles[1])==1)
            if poor_in_1>poor_in_2:
                allocate_twothirds.trace("Moving {} from {} to {}, harming {} members and helping {}.".format(g, families[1].name, families[0].name, poor_in_2, poor_in_1))
                bundles[1].remove(g)
                bundles[0].add(g)
                change=True
        if not change:
            break
    return bundles
allocate_twothirds.trace = lambda *x: None  # To enable tracing, set allocate_twothirds.trace=print





def demo(algorithm, families, goods, *args):
    """
    Demonstrate the given algorithm on the given families (must be 2 families).
    """
    if len(families)!=2:
        raise("Currently only 2 families are supported")
    bundles = algorithm(families, goods, *args)
    print("\nFinal allocation:\n * {}: {}\n * {}: {}".format(
        families[0].name, families[0].allocation_description(bundles[0]),
        families[1].name, families[1].allocation_description(bundles[1])))



@lru_cache(maxsize=None)
def balance(r:int, s:int)->float:
    """
    Calculates the function B(r,s), which represents
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
    """
    if (s<=0): return 1
    if (s>r): return 0
    val1 = (balance(r-1,s)+balance(r-1,s-1))/2
    val2 = balance(r-2,s-1)
    return min(val1,val2)

@lru_cache(maxsize=None)
def weight(r:int, s:int)->float:
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
    """
    return balance(r,s)-balance(r-1,s)


def plural(i: int)->str:
    return " " if i==1 else "s"


if __name__ == "__main__":
    import doctest
    (failures,tests) = doctest.testmod(report=True)
    print ("{} failures, {} tests".format(failures,tests))