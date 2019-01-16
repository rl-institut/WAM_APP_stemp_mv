from oemof.solph import analyzer as an


class TotalInvestmentAnalyzer(an.Analyzer):
    requires = ('results', 'param_results')
    depends_on = (an.SizeAnalyzer,)

    def analyze(self, *args):
        super(TotalInvestmentAnalyzer, self).analyze(*args)
        seq_result = self._get_dep_result(an.SizeAnalyzer)
        try:
            psc = self.psc(args)
            size = seq_result[args]
            invest = psc['investment_capex']
        except KeyError:
            return
        result = invest * size
        self.result[args] = result
        self.total += result


class CO2Analyzer(an.Analyzer):
    requires = ('results', 'param_results')
    depends_on = (an.SequenceFlowSumAnalyzer,)

    def analyze(self, *args):
        super(CO2Analyzer, self).analyze(*args)
        seq_result = self._get_dep_result(an.SequenceFlowSumAnalyzer)
        try:
            psc = self.psc(args)
            flow = seq_result[args]
            co2 = psc['co2_emissions']
        except KeyError:
            return
        result = co2 * flow
        self.result[args] = result
        self.total += result


class LCOEAutomatedDemandAnalyzer(an.LCOEAnalyzer):
    def __init__(self):
        super(LCOEAutomatedDemandAnalyzer, self).__init__([])

    def init_analyzer(self):
        # Find all demands:
        for nodes in self.analysis.param_results:
            try:
                if nodes[1].tags is not None and 'demand' in nodes[1].tags:
                    self.load_sinks.append(nodes[1])
            except AttributeError:
                pass
        super(LCOEAutomatedDemandAnalyzer, self).init_analyzer()


class FossilCostsAnalyzer(an.Analyzer):
    depends_on = (an.VariableCostAnalyzer,)

    def analyze(self, *args):
        super(FossilCostsAnalyzer, self).analyze(*args)
        vc_result = self._get_dep_result(an.VariableCostAnalyzer)
        try:
            psc = self.psc(args)
            if psc['is_fossil']:
                result = vc_result[args]
            else:
                return
        except KeyError:
            return
        self.result[args] = result
        self.total += result
