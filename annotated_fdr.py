#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thur Aug  3 14:38:29 2023

@author: zhangemily
"""

import numpy as np
import pandas as pd
import QuantLib as ql


def calendar_china_ib_mod(): # inter bank mkt
    calendar = ql.China(ql.China.IB)
    add_holiday_list = ['2023/01/02', 
                        '2023/01/23', '2023/01/24', '2023/01/25', '2023/01/26', '2023/01/27', '2023/04/05', 
                        '2023/05/01', '2023/05/02', '2023/05/03', 
                        '2023/06/22', '2023/06/23', 
                        '2023/09/29', '2023/10/02', '2023/10/03', '2023/10/04', '2023/10/05', '2023/10/06', 
                        
                        '2024-01-01', 
                        '2024-02-09', '2024-02-10', '2024-02-11', '2024-02-12', '2024-02-13', '2024-02-14', '2024-02-15', 
                        '2024-04-04', '2024-04-05', '2024-04-06',
                        '2024-05-01', '2024-05-02', '2024-05-03', '2024-05-04', '2024-05-05',
                        '2024-06-08', '2024-06-09', '2024-06-10',
                        '2024-09-15', '2024-09-16', '2024-09-17',
                        '2024-10-01', '2024-10-02', '2024-10-03', '2024-10-04', '2024-10-05', '2024-10-06', '2024-10-07']
    
    remove_holiday_list = ['2023/01/28', '2023/01/29', '2023/04/23', '2023/05/06', '2023/06/25', '2023/10/07', '2023/10/08',
                           '2024-02-04', '2024-02-17', '2024-04-07', '2024-04-27', '2024-04-28', '2024-09-14', '2022-09-29', '2022-10-12']
    
    
    for d in add_holiday_list:
        d = ql.DateParser.parseFormatted(d, '%Y-%m-%d')
        calendar.addHoliday(d)
    
    for d in remove_holiday_list:
        d = ql.DateParser.parseFormatted(d, '%Y-%m-%d')
        calendar.removeHoliday(d)
    
    return calendar


        


class FDR:
    
    def __init__(self, deposit_mkt_data, swap_mkt_data, fixing_data, today):
        
        self.deposit_mkt_data = deposit_mkt_data.copy()
        self.swap_mkt_data = swap_mkt_data.copy()
        self.fixing_data = fixing_data.copy()
        self.today = today
    
        self.curve, self.index = self._build(self.deposit_mkt_data, self.swap_mkt_data, self.fixing_data, self.today)

    
    def _build(self, deposit_mkt_data, swap_mkt_data, fixing_data, today):  
    
        curve = []
        index = []
        
        return curve, index


    def tweak_keytenor(self, tenor, tenor_type, tweak):
        if tenor_type.lower() == 'deposit':
            deposit_mkt_data_tweaked = self.deposit_mkt_data.copy()
            deposit_mkt_data_tweaked.loc[0, tenor] += tweak
            curve, index = self._build(deposit_mkt_data_tweaked, self.swap_mkt_data, self.fixing_data, self.today)
            return curve, index 
    
        elif tenor_type.lower() == 'swap':
            swap_mkt_data_tweaked = self.swap_mkt_data.copy()
            swap_mkt_data_tweaked.loc[0, tenor] += tweak
            curve, index = self._build(self.deposit_mkt_data_tweaked, swap_mkt_data_tweaked, self.fixing_data, self.today)
            return curve, index 
        
        else:
            return 'Invalid tweak type'
    
    # [0, tenor]和[0, :]的区别
    def tweak_parallel(self, tweak):
        deposit_mkt_data_tweaked = self.deposit_mkt_data.copy()
        swap_mkt_data_tweaked = self.swap_mkt_data.copy()
        
        deposit_mkt_data_tweaked.iloc[0, :] += tweak
        swap_mkt_data_tweaked.iloc[0, :] += tweak
        
        curve, index = self.build(deposit_mkt_data_tweaked, swap_mkt_data_tweaked, self.fixing_data, self.today())
        
        return curve, index



class FR007(FDR):
    
    def __init__(self, deposit_mkt_data, swap_mkt_data, fixing_data, today):
        
        super().__init__(deposit_mkt_data, swap_mkt_data, fixing_data, today)
        
        self.name = 'FR007'
        self.settlement_delay = 0
    
    def _build(self, deposit_mkt_data, swap_mkt_data, fixing_data, today):
        calendar = calendar_china_ib_mod()
        convention = ql.ModifiedFollowing
        fixed_daycount = ql.Actual365Fixed()
        float_daycount = ql.Actual365Fixed()
        
        name = 'FR007'
        depo_delay = 1
        swap_delay = 1
        EOM = False
        
        deposit_helpers = []
        for depo_tenor in deposit_mkt_data.columns:
            ix = ql.IborIndex(name, ql.Period(depo_tenor), depo_delay, ql.CNYCurrency(), calendar, convention, EOM, float_daycount)
            hp = ql.DepositRateHelper(ql.QuoteHandle(ql.SimpleQuote(deposit_mkt_data.loc[0, depo_tenor]/100)), ix)
            deposit_helpers.append(hp)
        
        swap_helpers = []
        for swap_tenor in swap_mkt_data.columns:
            if swap_tenor == '1M':
                swap_ix = ql.IborIndex(name, ql.Period('1M'), swap_delay, ql.CNYCurrency(),  calendar, convention, EOM, float_daycount)
                swap_hp = ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(swap_mkt_data.loc[0, swap_tenor]/100)), ql.Period(swap_tenor), calendar, ql.Monthly, convention, fixed_daycount, swap_ix)
                
                
            else:
                swap_ix = ql.IborIndex(name, ql.Period('3M'), swap_delay, ql.CNYCurrency(), calendar, convention, EOM, float_daycount)
                swap_hp = ql.SwapRateHelper(ql.QuoteHandle(ql.SimpleQuote(swap_mkt_data.loc[0, swap_tenor] / 100)), ql.Period(swap_tenor), calendar, ql.Quarterly, convention, fixed_daycount, swap_ix)
            swap_helpers.append(swap_hp)
    
            
        helpers = deposit_helpers + swap_helpers
        
        curve = ql.PiecewiseLinearZero(today, helpers, float_daycount)
        curve_ts = ql.YieldTermStructureHandle(curve)
        
        index = ql.IborIndex(name, ql.Period('1W'), swap_delay, ql.CNYCurrency(), calendar, convention, EOM, float_daycount, curve_ts)

        for i in fixing_data.index[:-1]:
            day1 = ql.DateParser.parseFormatted(fixing_data['日期'][i], '%Y-%m-%d')
            day2 = ql.DateParser.parseFormatted(fixing_data['日期'][i + 1], '%Y-%m-%d')
            f = fixing_data['Fixing'][i] / 100.0
            temp_day = day1
            
            while temp_day < day2:
                index.addFixing(temp_day, f, True)
                temp_day = calendar.advance(temp_day, 1, ql.Days)
            
        temp_day = ql.DateParser.parseFormatted(fixing_data['日期'][fixing_data.index[-1]], '%Y-%m-%d')
        f = fixing_data['Fixing'][fixing_data.index[-1]] / 100
            
        while temp_day <= today:                                        
            index.addFixing(temp_day, f, True)
            temp_day = calendar.advance(temp_day, 1, ql.Days)

        return curve, index
