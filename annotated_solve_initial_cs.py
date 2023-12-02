#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 10:13:55 2023

@author: zhangemily
"""

import numpy as np
import pandas as pd
import QuantLib as ql
from Credit_Curves import *
from CDS import *
from scipy import optimize

def price(yield_spread, target_npv):
    
    today = ql.Date(17, 8, 2023)
    
    calendar = ql.China(ql.China.IB)
    daycount = ql.Actual365Fixed()
    convention = ql.ModifiedFollowing
    
    valuation_date = today
    ql.Settings.instance().evaluationDate = valuation_date
    
    default_recovery = 0.25
    credit_obj = CreditCurve_BondYieldSpread(yield_spread, default_recovery, calendar, daycount, convention, today)
    credit_crv = credit_obj.curve
    disc_crv = ql.FlatForward(0, calendar, 0.02, daycount)
    
    start = ql.Date(17, 8, 2023)
    expiry = ql.Date(19, 2, 2024)
    sch = ql.Schedule([ql.Date(17, 11, 2023), ql.Date(19, 2, 2024)])
    spread = 0.003193    # fix leg
    notional = 1e8
    side = ql.Protection.Seller
    trade_recovery = 0.25
    premium_front = True
    
    inst = CDS(start, expiry, sch, spread, notional, trade_recovery, side, premium_front)
    npv = inst.NPV(today, credit_crv, disc_crv, calendar, daycount, convention)
    
    return npv - target_npv


def solve_initial_y(npv):
    y = optimize.bisect(price, 0, 5e-3, args = npv)
    return y

if __name__ == '__main__':
    target_npv = 3655
    recovery = 0.25
    
    cs = solve_initial_y(target_npv)
    print('Initial Yield Spread: ', cs)