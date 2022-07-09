#!/usr/bin/env python
# -*- coding:utf-8 -*-

# from baseline import BaseLine

from Optimization import Opt

if __name__ == '__main__':
    method = Opt()
    method.run(15000, 250)
    # baseLine = BaseLine()
    # baseLine.run()
    # from judgement_tools.judgement import JudgeMent

    # judge = JudgeMent('solution.txt')
    # judge.run_judge()
