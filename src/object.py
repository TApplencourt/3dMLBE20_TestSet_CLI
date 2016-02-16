#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import re
from math import sqrt, pow

# Need to add variance to the tuple
# Check with R
class Energie(object):

    def __init__(self,e,err=0.):
        self.e = e
        assert err >= 0
        self.err = float(err)

    p = re.compile(ur'^(0*)\.(0*(\d{1,2}))')

    def __str__(self):
        # Hypothese : Will display in flat form.
        #             not scientifique one

        # Same formating and take the non zero value
        err = '%f' % self.err

        if not self.err:
            return '%f' % self.e

        if self.err >= 1.:
            return "{0}+/-{1}".format(self.e, self.err)

        else:
            m = re.search(self.p, str(err))

            left = len(m.group(1))

            len_format = len(m.group(2))
            good_digit = m.group(3)

            format_string = "{:>%d.%df}" % (len_format + left, len_format)
            str_e = format_string.format(self.e)
            return "{0}({1})".format(str_e, good_digit)

    def __repr__(self):
      return self.__str__()

    # Add Left right
    def __add__(self, x):
        try:
            return Energie(self.e + x.e, sqrt(pow(self.err, 2) + pow(x.err, 2)))
        except AttributeError:
            return Energie(self.e + x, self.err)

    def __radd__(self, x):
        return self.__add__(x)

    # Minis Left right
    def __sub__(self, x):
        try:
            return Energie(self.e - x.e, sqrt(pow(self.err, 2) + pow(x.err, 2)))
        except AttributeError:
            return Energie(self.e - x, self.err)

    def __rsub__(self, x):
        try:
            return Energie(-self.e + x.e, sqrt(pow(self.err, 2) + pow(x.err, 2)))
        except AttributeError:
            return Energie(-self.e + x, self.err)

    # Multiplication
    def __mul__(self, x):
        if isinstance(x, Energie):
            raise NotImplementedError
        else:
            return Energie(self.e * x, self.err * x)

    def __rmul__(self, x):
        return self.__mul__(x)

    # Division
    def __div__(self, x):
        return Energie(self.e / x, self.err / sqrt(abs(x)))

    # -Energie
    def __neg__(self):
        return Energie(-self.e, self.err)

    # abs
    def __abs__(self):
        return Energie(abs(self.e), self.err)

    # __lt__
    def __lt__(self, x):
        try:
            return self.e < x.e
        except AttributeError:
            return self.e < x

    def __gt__(self, x):
        try:
            return self.e > x.e
        except AttributeError:
            return self.e > x

    def __format__(self, format_spec):

        format_e = self.e.__format__(format_spec)
        format_err = self.err.__format__(format_spec)

#        print "=", format_e
#        print "-", format_err
#        sys.exit()

        if not self.err:
            return format_e

        if ">" in format_spec:
            format_err = format_err.lstrip()
        elif "<" in format_spec:
            format_e = format_e.rstrip()

        if float(format_err) >= 1.:
            return "{0}+/-{1}".format(format_e, format_err)
        else:
            p2 = re.compile(ur'^0*\.0*(\d*)')
            m = re.search(p2, format_err.strip())
            good_digit = m.group(1)

            if good_digit:
                return "{0}({1})".format(format_e, good_digit)
            else:
                return format_e

import sys
def magic(self,other,opr):
    if isinstance(other, Energie_part):
        l = ["{0} = self.{0}.{1}(other.{0})".format(i,opr) for i in self.__dict__.keys()]
        l_string = "a = Energie_part({0})".format(", ".join(l))
        exec(l_string)
        return a
    else:
        l = ["{0} = self.{0}.{1}(other)".format(i,opr) for i in self.__dict__.keys()]
        l_string = "a = Energie_part({0})".format(", ".join(l))
        exec(l_string)
        return a        

class Energie_part(object):

    def __init__(self,no_relativistic=Energie(0.,0.),
                      spin_orbit=Energie(0.,0.),
                      zpe=Energie(0.,0.)):
        self.no_relativistic = no_relativistic
        self.spin_orbit = spin_orbit
        self.zpe = zpe

        assert isinstance(self.no_relativistic,Energie)
        assert isinstance(self.spin_orbit,Energie)
        assert isinstance(self.zpe,Energie)

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
      return self.__str__()

    def __add__(self, other):
        return magic(self,other,sys._getframe().f_code.co_name)

    def __radd__(self, x):
        return self.__add__(x)

    def __sub__(self, other):
        return magic(self,other,sys._getframe().f_code.co_name)

    def __mul__(self, other):
        return magic(self,other,sys._getframe().f_code.co_name)


    def __rmul__(self, x):
        return self.__mul__(x)

    def __div__(self, other):
        return magic(self,other,sys._getframe().f_code.co_name)

    # -Energie
    def __neg__(self):
        return magic(self,other,sys._getframe().f_code.co_name)

    # abs
    def __abs__(self):
        return magic(self,other,sys._getframe().f_code.co_name)

    @property
    def no_relativist_energie(self):
        assert self.no_relativistic.e != 0.
        return self.no_relativistic

    @property
    def correted_energie(self):
        return self.no_relativistic +  self.spin_orbit + self.zpe

if __name__ == '__main__':

    print "Operation"
    print "========="
    a = Energie(1.400, 0.6)
    print "a =", a
    print "a+a =", a + a
    print "a-a =", a - a
    print "a*2 =", a * 2

    print ""
    print "Display"
    print "======="

    list_ = [Energie(1.5, 1.300), 
             Energie(1, 10),
             Energie(3, 2),
             Energie(0.1, 0.1), 
             Energie(0.1, 10),
             Energie(1, 0.00100),
             Energie(8.8819036, 3.0581249),
             Energie(-100.42304, 00036)]

    print "Value", "err", "display"
    for i in list_:
        print map("{:>9.4f}".format, [i.e, i.err, i])

    print ""
    print "Energie_part"
    print "============"

    a = Energie_part(list_[0],list_[1],list_[2])
    print "a =", a
    print "a+a =", a + a
    print "a-a =", a - a
    print "a*2 =", a * 2
    print "a/2 =", a / 2
    b = (a-2*a)/2 
    print "(a-2*a)/2 =",b
    print b.no_relativist_energie
    print b.correted_energie

    print "===="
    a = Energie_part(spin_orbit=Energie(-6.3,0.4))

#    print a.no_relativist_energie
    print a.correted_energie