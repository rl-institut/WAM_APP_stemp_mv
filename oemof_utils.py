
from pyomo.core import Set, Constraint
from pyomo.core.base.block import SimpleBlock
import oemof.groupings as groupings


class MinimalLoad:
    def __init__(self, minimal_load=0.0):
        self.minimal_load = minimal_load


class MinimalLoadFlow(SimpleBlock):

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        r"""Creates sets, variables and constraints for Flow with investment
        attribute of type class:`.Investment`.

        Parameters
        ----------
        group : list
            List containing tuples containing flow (f) objects that have an
            attribute investment and the associated source (s) and target (t)
            of flow e.g. groups=[(s1, t1, f1), (s2, t2, f2),..]
        """
        if group is None:
            return None

        m = self.parent_block()

        # ######################### SETS #####################################
        self.FLOWS = Set(initialize=[(g[0], g[1]) for g in group])

        def _minmal_load_rule(block, i, o, t):
            """Rule definition of constraint setting an upper bound of flow
            variable in investment case.
            """
            expr = m.flow[i, o, t] >= m.flows[i, o].minimal_load.minimal_load
            return expr
        self.minimal_load = Constraint(
            self.FLOWS, m.TIMESTEPS, rule=_minmal_load_rule)


def _minimum_load_grouping(stf):
    if hasattr(stf[2], 'minimal_load'):
        if stf[2].minimal_load is not None:
            return True
    else:
        return False


minimum_load_flow_grouping = groupings.FlowsWithNodes(
    constant_key=MinimalLoadFlow,
    # stf: a tuple consisting of (source, target, flow), so stf[2] is the flow.
    filter=_minimum_load_grouping
)
