#!/usr/bin/env python
# -*- coding:utf-8 -*-
# from Optimization import Opt
# from new_start import BaseLine
from prior_learning import PriorLearning
from baseline import BaseLine
# from center_opt import CenterOpt
if __name__ == '__main__':
    method = BaseLine()
    method.run()
    # from judgement_tools.judgement import JudgeMent
    #
    # judge = JudgeMent('solution.txt')
    # judge.run_judge()
