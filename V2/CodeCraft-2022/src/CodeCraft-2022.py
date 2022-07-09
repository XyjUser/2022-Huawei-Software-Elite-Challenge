#!/usr/bin/env python
# -*- coding:utf-8 -*-

# from baseline import BaseLine
# from new_try_2 import BaseLine
from Optimization_site_log import Optimization as BaseLine

if __name__ == '__main__':
    method = BaseLine()
    method.run(100, 255)
    # from judgement_tools.judgement import JudgeMent

    # judge = JudgeMent('solution.txt')
    # judge.run_judge()
