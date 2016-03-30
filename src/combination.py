#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Get data from interface
"""


# ___                      
#  |  ._ _  ._   _  ._ _|_ 
# _|_ | | | |_) (_) |   |_ 
#           |              
from collections import defaultdict
import sys

def add_spin_orbit(dd_value,d_formula,d_so,strict=True):
    """
    Input: 
    dd_value |
    -> key: run_id
    -> value: |
         key: ele
         value: Energie who whant to add the spin orbit corection

    d_formula|
    -> key: name
    -> value: the flaten formula (H,H,O) for H2O for exemple.

    d_so|
    -> key: d[ele]  
    -> value:  Value of the correction (Format Energie)

    Return:
    dd_value |
    -> key: run_id
    -> value: |
         key: ele
         value: Energie whith the spin orbit corection

    If strinc and if not all the spin correction are avaliable raise a error
    """

    d = defaultdict(dict)

    for run_id,d_ref in dd_value.items():
        for ele, energy in d_ref.items():          
            try:
                d[run_id][ele] = energy + sum(d_so[i] for i in d_formula[ele]) - d_so[ele]
            except KeyError:

                if strict:
                    print "No SpinOrbit corection for:", ele
                    print "Or for one of this children"
                    sys.exit(1)
                else:
                    pass
    return d

def merge_two_dicts(x, y):
    '''Given two dicts, merge them into a new dict as a shallow copy.'''
    z = x.copy()
    z.update(y)
    return z

def calc_atomisation(dd_value,d_formula,strict=False):
    """
    Input: 
    dd_value |
    -> key: run_id
    -> value: |
         key: ele
         value: Energie who whant to calc the deviation

    Return: 
        Return the deviation only for the molecule

    Can:
        Can return empty dict
    """
    d = defaultdict(dict)

    for run_id,d_ref in dd_value.items():
        for ele, energy in d_ref.items():

            if len(d_formula[ele]) == 1:
                continue

            try:
                d[run_id][ele] = sum(d_ref[i] for i in d_formula[ele]) - d_ref[ele]
                d[run_id][ele] *= 627.509
            except KeyError:

                if strict:
                    print "No energy for:", ele
                    print "Or for one of this children"
                    print "Cannot compute the atomisation energy"
                    sys.exit(1)
                else:
                    pass
    return d


def calc_deviation(dd_value, run_id_ref,strict=True):
    """
    Input: 
    dd_value |
    -> key: run_id
    -> value: |
         key: ele
         value: Energie who whant to calc the deviation

    run_id_ref: The run_id interger who will be the referance

    Return:
    dd_ae |
    -> key: run_id
    -> value: |
         key: ele
         value: ennergie difference

    If stric, All the element present need to be on the ref
    """

    # All the element in d need to be in the ref
    d_ae  = defaultdict(dict)

    for run_id,d_ele in dd_value.items():

        if run_id == run_id_ref:
            continue
        else:
            for ele, energy in d_ele.items():

                try:
                    d_ae[run_id][ele] = energy - dd_value[run_id_ref][ele]
                except KeyError:

                    if strict:
                        print "Some element are not present in the ref:",ele
                        sys.exit(1)
                    else:
                        pass
    return d_ae

def calc_mad(d_deviation):
    """
    Input: 
    dd_value |
    -> key: run_id
    -> value: |
         key: ele
         value: Energie who whant to calc the deviation

    Return: 
        Return the Mean Absolute Deviation
    """

    d_mad = {}
    for run_id,d_ele in d_deviation.items():
        l_energy = d_ele.values()
        mad = sum(map(abs, l_energy)) / len(l_energy)
        d_mad[run_id] = mad

    return d_mad
