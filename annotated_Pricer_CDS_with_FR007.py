#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thur Aug  3 13:50:24 2023

@author: zhangemily
"""

import sys

import numpy as np
import pandas as pd
import json
import QuantLib as ql
from datetime import datetime
from matplotlib import pyplot as plt
from scipy.stats import norm
from scipy.stats import chi2

from annotated_fdr import *
from annotated_Credit_Curves import *
from annotated_CDS import *

def get_terms_yield(curve, calendar, today, daycount = ql.Actual365Fixed(), compounding = ql.Simple, tenors = None):
    if tenors == None:
        tenors = ['1M', '3M', '6M', '9M', '1Y', '2Y', '4Y', '3Y', '5Y']
    
    
    terms_yield = dict()
    for tenor in tenors:
        target_date = calendar.advance(today, ql.Period(tenor))
        tenor_yield = curve.zeroRate(target_date, daycount, compounding).rate()
        terms_yield[tenor] = tenor_yield
        
    print(json.dumps(terms_yield, indent = 2))
    return terms_yield
        
############################################################
# get init yield spread

# 由交易员反算
initial_yield_spread = 0.0030

# 由交易员根据交易标的计算
init_bond_yield = 0.032

# date setting
init_date = ql.Date(17, 8, 2023)
target_date = ql.Date(19, 8, 2024)
ql.Settings.instance().evaluationDate = init_date

# fr007 market data
file_name = 'fr007 data 20230817.xlsx'

# deposit data
deposit_mkt_data = pd.read_excel(file_name, 'deposit_rate')
deposit_mkt_data = deposit_mkt_data.loc[:, ['1W']].reset_index(drop = True)

# swap data
swap_mkt_data = pd.read_excel(file_name, 'swap_rate')
swap_mkt_data = swap_mkt_data.drop('TYPE', axis = 1).dropna(axis = 1).reset_index(drop = True)

# fixing data
fixing_data = pd.read_excel(file_name, 'fixings')
fixing_data.columns = ['日期', 'Fixing']
fixing_data['日期'] = fixing_data['日期'].apply(lambda x: datetime.strftime(x, '%Y-%m-%d'))

# get FR007 curve
init_fr007_curve = annotated_fdr.FR007(deposit_mkt_data, swap_mkt_data, fixing_data, init_date)

# other params
calendar = ql.China(ql.China.IB)
daycount = ql.Actual365Fixed()
convention = ql.ModifiedFollowing

# calc init bond yield spread (used for calculating spread change)
init_fr007_yield = init_fr007_curve.curve.zeroRate(target_date, daycount, ql.Simple).rate()

init_bond_yield_spread = init_bond_yield - init_fr007_yield


############################################################
# daily calculation

# date setting
today = ql.Date(17, 8, 2023)
valuation_date = today
ql.Settings.instance().evaluationDate = valuation_date

# fr007 market data
file_name = 'fr007 data.xlsx'

# deposit data
deposit_mkt_data = pd.read_excel(file_name, 'deposit_rate')
deposit_mkt_data = deposit_mkt_data.loc[:, ['1W']].reset_index(drop=True)

# swap data
swap_mkt_data = pd.read_excel(file_name, 'swap_rate')
swap_mkt_data = swap_mkt_data.drop('TYPE', axis=1).dropna(axis=1).reset_index(drop=True)
# fixing data
fixing_data = pd.read_excel(file_name, 'fixings')
fixing_data.columns = ['日期', 'Fixing']
fixing_data['日期'] = fixing_data['日期'].apply(lambda x: datetime.strftime(x, '%Y-%m-%d'))

# get FR007 curve
fr007_curve = annotated_fdr.FR007(deposit_mkt_data, swap_mkt_data, fixing_data, today)      

# other params
calendar = ql.China(ql.China.IB)
daycount = ql.Actual365Fixed()
convention = ql.ModifiedFollowing

# get fr007 yield
fr007_yield = fr007_curve.curve.zeroRate(target_date, daycount, ql.Simple).rate()

# 交易员手动输入
bond_yield_today = 0.033

# calculating spread change
bond_yield_spread_today = bond_yield_today - fr007_yield
spread_change = bond_yield_spread_today - init_bond_yield_spread

# calculating spread change
bond_yield_spread_today = bond_yield_today - fr007_yield
spread_change = bond_yield_spread_today - init_bond_yield_spread

default_recovery = 0.25

credit_obj = CreditCurve_BondYieldSpread(initial_yield_spread + spread_change, default_recovery, calendar, daycount, convention, today)

credit_crv = credit_obj.curve

disc_rate = 0.02
disc_obj = FlatCurve(disc_rate, calendar, daycount, convention, today)

disc_crv = disc_obj.curve

# terms yield
print(f'FR007 Terms yield on {str(today)}:')

fr007_terms_yield = get_terms_yield(fr007_curve.curve, calendar, today)


############################################################
# cds trade info

start = ql.Date(18, 8, 2023)
expiry = ql.Date(19, 8, 2024)
sch = ql.Schedule([ql.Date(17, 11, 2023), ql.Date(19, 2, 2024), ql.Date(17, 5, 2024), ql.Date(19, 8, 2024)])

coupon = 0.003
notional = 1e8
direction = ql.Protection.Seller
premium_front = True


############################################################
# cds pricing result

inst = CDS(start, expiry, sch, coupon, notional, trade_recovery, direction, premium_front)

npv = inst.NPV(today, credit_crv, disc_crv, calendar, daycount, convention)
print('NPV: ', npv)

cs01 = inst.CS01(today, credit_obj, disc_crv, calendar, daycount, convention)
print('CS01: ', cs01)

dv01 = inst.DV01(today, credit_crv, disc_obj, calendar, daycount, convention)
print('DV01: ', dv01)
