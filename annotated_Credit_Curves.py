#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thur Aug  3 18:54:57 2023

@author: zhangemily
"""

import numpy as np
import pandas as pd
import QuantLib as ql

# 市场流动性好，多个可参考利差
class CreditCurve_BondYieldSpread:
    
    def __init__(self, spread_data, recovery, disc_crv, calendar, daycount, convention, rule, today):
        
        self.spread_data = spread_data
        self.recovery = recovery
        self.disc_crv = disc_crv
        self.calendar = calendar
        self.daycount = daycount
        self.convention = convention
        self.rule = rule
        self.today = today
        
        self.curve = self._build(self.spread_data, self.recovery, self.disc_crv, self.calendar, self.daycount, self.convention, self.rule, self.today)
        

    def _build(self, spread_data, recovery, disc_crv, calendar, convention, daycount, rule, today):
        
        hps = [ql.SpreadCdsHelper(ql.QuoteHandle(ql.SimpleHandle(spread_data.loc[i, 'Spread'])), ql.Period(spread_data.loc[i, 'Tenor']), 0, calendar, ql.Quarterly, convention, rule, daycount, recovery, ql.YieldTermStructureHandle(disc_crv)) for i in spread_data.index]
               
        credit_crv = ql.PiecewiseLinearZero(self.toda, hps, daycount)
        return credit_crv
    
    
    def tweak_parallel(self, tweak):
        spread_data_tweaked = self.spread_data.copy()
        spread_data_tweaked['Spread'] += tweak
        curve = self._build(spread_data_tweaked, self.recovery, self.disc_crv, self.calendar, self.daycount, self.convention, self.rule, self.today)
        return curve



# Flat Hazard Rate
class CreditCurve_BondYieldSpread:
    
    def __init__(self, yield_spread, recovery, calendar, daycount, convention, today):
        
        self.yield_spread = yield_spread
        self.recovery = recovery
        self.calendar = calendar
        self.daycount = daycount
        self.convention = convention
        self.today = today
        
        self.curve = self._build(self.yield_spread, self.recovery, self.calendar, self.daycount, self.convention, self.today)   

    
    def _build(self, yield_spread, recovery, calendar, daycount, convention, today):
        
        credit_crv = ql.FlatHazardRate(today, ql.QuoteHandle(ql.SimpleQuote( -np.log(1 - yield_spread / (1 - recovery)))), daycount)
        
        return credit_crv

    def tweak_parallel(self, tweak):
        spread_data_tweaked = self.yield_spread + tweak

        curve = self._build(spread_data_tweaked, self.recovery, self.calendar, self.daycount, self.convention, self.today)
        
        return curve



class FlatCurve:
    
    def __init__(self, rate, calendar, daycount, convention, today):
        self.rate = rate
        self.calendar = calendar
        self.daycount = daycount
        self.convention = convention
        self.today = today
        
        self.curve = self._build(self.rate, self.calendar, self.daycount, self.convention, self.today)

    def _build(self, rate, calendar, daycount, convention, today):
        return ql.FlatForward(today, rate, daycount)


    def tweak_parallel(self, tweak):
        return self._build(self.rate + tweak, self.calendar, self.daycount, self.convention, self.today)
               