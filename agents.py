#!python3

"""
Classes that represent agents with general, additive and binary preferences.
"""


from abc import ABC, abstractmethod        # Abstract Base Class
from utils import plural
import math, itertools
import more_itertools


class Agent(ABC):
    """
    An abstract class.
    Represents an agent or several agents with the same valuation function.
    """

    def __init__(self, total_value:int, cardinality:int=1):
        self.total_value = total_value
        self.cardinality = cardinality

    @abstractmethod
    def value(self, bundle:set)->int:
        """
        This abstract method should calculate the agent's value for the given bundle of goods.

        >>> a = MonotoneAgent({"x": 1, "y": 2, "xy": 4})
        >>> a.value(set("xy"))
        4
        """

    def value_except_best_c_goods(self, bundle:set, c:int=1)->int:
        """
        Calculates the value of the given bundle when the "best" (at most) c goods are removed from it.
        Formally, it calculates:
              min [G subseteq bundle] value (bundle - G)
        where G is a subset of cardinality at most c.
        This is a subroutine in checking whether an allocation is EFc.

        >>> a = MonotoneAgent({"x": 1, "y": 2, "xy": 4})
        >>> a.value_except_best_c_goods(set("xy"), c=1)
        1
        >>> a.value_except_best_c_goods(set("xy"), c=2)
        0
        >>> a.value_except_best_c_goods(set("x"), c=1)
        0
        >>> a.value_except_best_c_goods(set(), c=1)
        0
        """
        if len(bundle) <= c: return 0
        else: return min([
            self.value(bundle.difference(sub_bundle))
            for sub_bundle in itertools.combinations(bundle, c)
        ])

    def value_except_worst_c_goods(self, bundle:set, c:int=1)->int:
        """
        Calculates the value of the given bundle when the "worst" c goods are removed from it.
        Formally, it calculates:
              max [G subseteq bundle] value (bundle - G)
        where G is a subset of cardinality at most c.
        This is a subroutine in checking whether an allocation is EFx.

        >>> a = MonotoneAgent({"x": 1, "y": 2, "xy": 4})
        >>> a.value_except_worst_c_goods(set("xy"), c=1)
        2
        """
        if len(bundle) <= c: return 0
        else: return max([
            self.value(bundle.difference(sub_bundle))
            for sub_bundle in itertools.combinations(bundle, c)
        ])

    def value_1_of_c_MMS(self, bundle:set, c:int=1)->int:
        """
        Calculates the value of the 1-out-of-c maximin-share.
        This is a subroutine in checking whether an allocation is MMS.

        >>> a = MonotoneAgent({"x": 1, "y": 2, "xy": 4})
        >>> a.value_1_of_c_MMS(set("xy"), c=1)
        4
        >>> a.value_1_of_c_MMS(set("xy"), c=2)
        1
        >>> a.value_1_of_c_MMS(set("xy"), c=3)
        0
        """
        partition_values = []
        for partition in more_itertools.partitions(bundle):
            if len(partition) > c:
                continue
            elif len(partition) < c:
                partition_value = 0
            else:
                partition_value = min([self.value(bundle) for bundle in partition])
            partition_values.append(partition_value)
        return max(partition_values)

    def is_EFc(self, own_bundle: set, all_bundles: list, c: int) -> bool:
        """
        Checks whether the current agent finds the given allocation envy-free-except-c-goods (EFc).
        :param own_bundle:   the bundle given to the family of the current agent.
        :param all_bundles:  a list of all bundles.
        :return: True iff the current agent finds the allocation EFc.
        """
        own_value = self.value(own_bundle)
        for other_bundle in all_bundles:
            if own_value < self.value_except_best_c_goods(other_bundle, c):
                return False
        return True

    def is_EF1(self, own_bundle: set, all_bundles: list) -> bool:
        """
        Checks whether the current agent finds the given allocation envy-free-except-1-good (EF1).
        :param own_bundle:   the bundle given to the family of the current agent.
        :param all_bundles:  a list of all bundles.
        :return: True iff the current agent finds the allocation EF1.
        """
        return self.is_EFc(own_bundle, all_bundles, c=1)

    def is_EFx(self, own_bundle: set, all_bundles: list)->bool:
        """
        Checks whether the current agent finds the given allocation EFx.
        :param own_bundle:   the bundle given to the family of the current agent.
        :param all_bundles:  a list of all bundles.
        :return: True iff the current agent finds the allocation EFx.
        """
        own_value = self.value(own_bundle)
        for other_bundle in all_bundles:
            if own_value < self.value_except_worst_c_goods(other_bundle, c=1):
                return False
        return True

    def is_EF(self, own_bundle: set, all_bundles: list)->bool:
        """
        Checks whether the current agent finds the given allocation envy-free.
        :param own_bundle:   the bundle given to the family of the current agent.
        :param all_bundles:  a list of all bundles.
        :return: True iff the current agent finds the allocation envy-free.
        """
        own_value = self.value(own_bundle)
        for other_bundle in all_bundles:
            if own_value < self.value(other_bundle):
                return False
        return True

    def is_1_of_c_MMS(self, own_bundle:set, c:int, approximation_factor:float=1)->bool:
        own_value = self.value(own_bundle)
        target_value = approximation_factor * self.value_1_of_c_MMS(c)
        return own_value >= target_value

    def is_PROP(self, own_bundle:set, num_of_agents:int)->bool:
        """
        Checks whether the current agent finds the given allocation proportional.
        :param own_bundle:     the bundle consumed by the current agent.
        :param num_of_agents:  the total number of agents.
        :return: True iff the current agent finds the allocation PROPc.
        """
        own_value = self.value(own_bundle)
        return own_value*num_of_agents >= self.total_value

    def is_PROPc(self, own_bundle:set, num_of_agents:int, c:int)->bool:
        """
        Checks whether the current agent finds the given allocation PROPc.
        When there are k agents (or families), an allocation is PROPc for an agent
        if his value for his own bundle is at least 1/k of his value for the following bundle:
            [all the goods except the best c].
        :param own_bundle:   the bundle consumed by the current agent.
        :param num_of_agents:  the total number of agents.
        :param c: how many best-goods to exclude from the total bundle.
        :return: True iff the current agent finds the allocation PROPc.

        NOTE: requires the field self.desired_goods!
        """
        own_value = self.value(own_bundle)
        total_except_best_c = self.value_except_best_c_goods(
            self.desired_goods, c=num_of_agents-1)
        return own_value*num_of_agents >= total_except_best_c



class MonotoneAgent(Agent):
    """
    Represents an agent or several agents with a general monotone valuation function.

    >>> a = MonotoneAgent({"x": 1, "y": 2, "xy": 4})
    >>> a
    1 agent  with monotone valuations
    >>> a.value("")
    0
    >>> a.value({"x"})
    1
    >>> a.value("yx")
    4
    >>> a.value({"y","x"})
    4
    >>> a.is_EF({"x"}, [{"y"}])
    False
    >>> a.is_EF1({"x"}, [{"y"}])
    True
    >>> a.is_EFx({"x"}, [{"y"}])
    True
    >>> MonotoneAgent({"x": 1, "y": 2, "xy": 4}, cardinality=2)
    2 agents with monotone valuations

    """
    def __init__(self, map_bundle_to_value:dict, cardinality:int=1):
        """
        Initializes an agent with a given valuation function.
        :param map_bundle_to_value: a dict that maps each subset of goods to its value.
        :param cardinality: the number of agents with the same valuation.
        """
        total_value = max(map_bundle_to_value.values())
            # The valuation is assumed to be monotone,
            # so we assume that the total value is the maximum value.
        Agent.__init__(self, total_value=total_value, cardinality=cardinality)
        self.map_bundle_to_value = {frozenset(bundle):value for bundle,value in  map_bundle_to_value.items()}
        self.map_bundle_to_value[frozenset()] = 0   # normalization: the value of the empty bundle is always 0

    def value(self, goods:set)->int:
        """
        Calculates the agent's value for the given set of goods.
        """
        goods = frozenset(goods)
        if goods in self.map_bundle_to_value:
            return self.map_bundle_to_value[goods]
        else:
            raise ValueError("The value of {} is not specified in the valuation function".format(goods))

    def __repr__(self):
        return "{} agent{} with monotone valuations".format(self.cardinality, plural(self.cardinality))




class AdditiveAgent(Agent):
    """
    Represents an agent or several agents with an additive valuation function.

    >>> a = AdditiveAgent({"x": 1, "y": 2, "z": 4, "w":0})
    >>> a
    1 agent  with additive valuations. Desired goods: ['x', 'y', 'z']
    >>> a.value(set())
    0
    >>> a.value({"w"})
    0
    >>> a.value({"x"})
    1
    >>> a.value("yx")
    3
    >>> a.value({"y","x","z"})
    7
    >>> a.is_EF({"y"}, [{"y"},{"x"},{"z"},set()])
    False
    >>> a.is_PROP({"y"}, 4)
    True
    >>> a.is_PROP({"y"}, 3)
    False
    >>> a.is_PROPc({"y"}, 3, c=1)
    True
    >>> a.is_EF1({"y"}, [{"x","z"}])
    True
    >>> a.is_EF1({"x"}, [{"y","z"}])
    False
    >>> a.is_EFx({"x"}, [{"y"}])
    True
    >>> AdditiveAgent({"x": 1, "y": 2, "z": 4}, cardinality=2)
    2 agents with additive valuations. Desired goods: ['x', 'y', 'z']

    """
    def __init__(self, map_good_to_value:dict, cardinality:int=1):
        """
        Initializes an agent with a given additive valuation function.
        :param map_good_to_value: a dict that maps each single good to its value.
        :param cardinality: the number of agents with the same valuation.
        """
        total_value = sum(map_good_to_value.values())
            # The valuation is assumed to be additive,
            # so we assume that the total value is the sum of all values.
        super().__init__(total_value=total_value, cardinality=cardinality)
        self.map_good_to_value = map_good_to_value
        self.desired_goods = set([g for g,v in map_good_to_value.items() if v>0])

    def value(self, goods:set)->int:
        """
        Calculates the agent's value for the given set of goods.
        """
        return sum([self.map_good_to_value[g] for g in goods])

    def value_except_best_c_goods(self, bundle:set, c:int=1)->int:
        """
        Calculates the value of the given bundle when the "best" (at most) c goods are removed from it.
        Formally, it calculates:
              min [G subseteq bundle] value (bundle - G)
        where G is a subset of cardinality at most c.
        This is a subroutine in checking whether an allocation is EFc.

        >>> a = AdditiveAgent({"x": 1, "y": 2, "z": 4})
        >>> a.value_except_best_c_goods(set("xyz"), c=1)
        3
        >>> a.value_except_best_c_goods(set("xyz"), c=2)
        1
        >>> a.value_except_best_c_goods(set("xy"), c=1)
        1
        >>> a.value_except_best_c_goods(set("xy"), c=2)
        0
        >>> a.value_except_best_c_goods(set("x"), c=1)
        0
        >>> a.value_except_best_c_goods(set(), c=1)
        0
        """
        if len(bundle) <= c: return 0
        sorted_bundle = sorted(bundle, key=lambda g: -self.map_good_to_value[g]) # sort the goods from best to worst
        return self.value(sorted_bundle[c:])  # remove the best c goods

    def value_except_worst_c_goods(self, bundle:set, c:int=1)->int:
        """
        Calculates the value of the given bundle when the "worst" c goods are removed from it.
        Formally, it calculates:
              max [G subseteq bundle] value (bundle - G)
        where G is a subset of cardinality at most c.
        This is a subroutine in checking whether an allocation is EFx.

        >>> a = AdditiveAgent({"x": 1, "y": 2, "z": 4})
        >>> a.value_except_worst_c_goods(set("xyz"), c=1)
        6
        >>> a.value_except_worst_c_goods(set("xy"), c=1)
        2
        >>> a.value_except_worst_c_goods(set("xy"), c=2)
        0
        >>> a.value_except_worst_c_goods(set("x"), c=1)
        0
        >>> a.value_except_worst_c_goods(set(), c=1)
        0
        """
        if len(bundle) <= c: return 0
        sorted_bundle = sorted(bundle, key=lambda g: self.map_good_to_value[g])  # sort the goods from worst to best:
        return self.value(sorted_bundle[c:])  # remove the worst c goods

    def __repr__(self):
        return "{} agent{} with additive valuations. Desired goods: {}".format(self.cardinality, plural(self.cardinality), sorted(self.desired_goods))



class BinaryAgent(Agent):
    """
    Represents an agent with binary valuations, or several agents with the same binary valuations.

    >>> a = BinaryAgent({"x","y","z"})
    >>> a
    1 agent  who want ['x', 'y', 'z']
    >>> a.value({"x","w"})
    1
    >>> a.value({"y","z"})
    2
    >>> a.is_EF({"x","w"},[{"y","z"}])
    False
    >>> a.is_EF1({"x","w"},[{"y","z"}])
    True
    >>> a.is_EF1({"v","w"},[{"y","z"}])
    False
    >>> a.is_EF1(set(),[{"y","w"}])
    True
    >>> a.is_EF1(set(),[{"y","z"}])
    False
    >>> a.is_1_of_c_MMS({"x","w"}, c=2)
    True
    >>> a.is_1_of_c_MMS({"w"}, c=2)
    False
    >>> BinaryAgent({"x","y","z"}, 2)
    2 agents who want ['x', 'y', 'z']
    """

    def __init__(self, desired_goods:set, cardinality:int=1):
        """
        Initializes an agent with a given set of desired goods.
        :param desired_goods: a set of strings - each string is a good.
        :param cardinality: the number of agents with the same set of desired goods.
        """
        super().__init__(total_value=len(desired_goods), cardinality=cardinality)
        self.desired_goods = set(desired_goods)

    def value(self, goods:set)->int:
        """
        Calculates the agent's value for the given set of goods.

        >>> BinaryAgent({"x","y","z"}).value({"w","x","y"})
        2
        >>> BinaryAgent({"x","y","z"}).value({"x","y"})
        2
        >>> BinaryAgent({"x","y","z"}).value("y")
        1
        >>> BinaryAgent({"x","y","z"}).value({"w"})
        0
        >>> BinaryAgent({"x","y","z"}).value(set())
        0
        >>> BinaryAgent(set()).value({"x","y","z"})
        0
        """
        # if isinstance(goods,set):
        goods = set(goods)
        return len(self.desired_goods.intersection(goods))
        # else:
        #     raise ValueError("goods must be a set")

    def value_except_best_c_goods(self, bundle:set, c:int=1)->int:
        if len(bundle) <= c: return 0
        return self.value(bundle) - c

    def value_except_worst_c_goods(self, bundle:set, c:int=1)->int:
        if len(bundle) <= c: return 0
        return self.value(bundle) - c

    def value_1_of_c_MMS(self, c:int=1)->int:
        return math.floor(self.total_value / c)

    def __repr__(self):
        return "{} agent{} who want {}".format(self.cardinality, plural(self.cardinality), sorted(self.desired_goods))



if __name__ == "__main__":
    import doctest
    (failures,tests) = doctest.testmod(report=True)
    print ("{} failures, {} tests".format(failures,tests))
