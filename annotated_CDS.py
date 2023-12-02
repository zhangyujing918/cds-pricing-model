#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 08:58:19 2023

@author: zhangemily
"""

import numpy as np
import pandas as pd
import QuantLib as ql
from scipy import optimize


class CDS:
    
    def __init__(self, start, expiry, sch, spread, notional, recovery, direction, premium_payfront):
        self.start = start
        self.expiry = expiry
        self.sch = sch
        self.spread = spread
        self.notional = notional
        self.recovery = recovery
        self.direction = direction
        self.premium_payfront = premium_payfront
    
    def NPV(self, today, credit_crv, disc_crv, calendar, daycount, convention):
        if self.premium_payfront:
            cds = ql.CreditDefaultSwap(self.direction, self.notional, self.spread, self.sch, convention, daycount)
            cdsEngine = ql.IsdaCdsEngine(ql.DefaultProbabilityTermStructureHandle(credit_crv), self.recovery, ql.YieldTermStructureHandle (disc_crv))
            cds.setPricingEngine(cdsEngine)
                
            coupon_npv = 0
            for i, cf in enumerate(cds.coupons()):
                date = list(self.sch)[i]
                if date >= today:
                    coupon_npv += cf.amount() * disc_crv.discount(date) * credit_crv.survivalProbability(date)
                    
            return coupon_npv + cds.defaultLegNPV()
        
        else:
            cds = ql.CreditDefaultSwap(self.direction, self.notional, self.spread, self.sch, convention, daycount)
            cdsEngine = ql.IsdaCdsEngine(ql.DefaultProbabilityTermStructureHandle(credit_crv), self.recovery, ql.YieldTermStructureHandle (disc_crv))
            cds.setPricingEngine(cdsEngine)
            return cds.NPV()
    
    def CS01(self, today, credit_obj, disc_crv, calendar, daycount, convention, tweak=1e-4):
        
        
        crv_up = credit_obj.tweak_parallel(tweak)
        crv_down = credit_obj.tweak_parallel(-tweak)
        
        npv_up = self.NPV(today, crv_up, disc_crv, calendar, daycount, convention)
        npv_down = self.NPV(today, crv_down, disc_crv, calendar, daycount, convention)
                        
        return (npv_up - npv_down) / (2 * tweak * 10000)
    
    def DV01(self, today, credit_crv, disc_obj, calendar, daycount, convention, tweak=1e-4):
        
        
        crv_up = disc_obj.tweak_parallel(tweak)
        crv_down = disc_obj.tweak_parallel(-tweak)

        npv_up = self.NPV(today, credit_crv, crv_up, calendar, daycount, convention)
        npv_down = self.NPV(today, credit_crv, crv_down, calendar, daycount, convention)
        

        return (npv_up - npv_down) / (2 * tweak * 10000)
                
                
                
                
                
                