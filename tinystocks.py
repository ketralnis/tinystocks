#!/usr/bin/env python

import os.path
import json
import sys
import urllib2
from collections import namedtuple
from termcolor import colored

import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def get_stock_quote(ticker_symbol):
    # shamelessly stolen from http://coreygoldberg.blogspot.com/2011/09/python-stock-quotes-from-google-finance.html
    url = 'http://www.google.com/finance/info?q=%s' % ticker_symbol.upper()
    data = urllib2.urlopen(url).read()
    lines = data.splitlines()
    lines = [x for x in lines if x not in ('// [', ']')] # they have some weird-ass format
    return json.loads(''.join(lines))

ownership = namedtuple('ownership', 'symbol count bought')

def cgain(s, val):
    if val == 0.0:
        return s, len(s)
    elif val > 0.0:
        return colored(s, 'white'), len(s)
    elif val < 0.0:
        return colored(s, 'red'), len(s)


def get_userdata():
    home = os.environ['HOME']
    fname = os.path.join(home, '.stocks')

    lines = list(open(fname))

    data = {}

    for i, line in enumerate(lines):
        line = line.rstrip('\n')
        if not line or line.startswith('#'):
            continue

        fields = line.split(',')
        assert len(fields) == 3
        o = ownership(symbol = fields[0].upper(),
                      count  = float(fields[1]),
                      bought = float(fields[2]))

        data.setdefault(o.symbol, []).append(o)

    return data

class Table(object):
    def __init__(self, fields):
        self.fields = fields
        self.lens = dict((f, len(f)) for f in fields)
        self.rows = []

    def append(self, row):
        assert sorted(row.data.keys()) == sorted(self.fields)

        for k, v in row.data.iteritems():
            self.lens[k] = max(self.lens[k], row.elens[k])

        self.rows.append(row)

    @staticmethod
    def padto(s, numchrs, elen):
        padding = ' ' * (numchrs - elen)
        return ''.join((padding, s))

    def dump(self, fd):
        interfield = 2 # space between fields

        for f in self.fields:
            flen = self.lens[f]
            fd.write(self.padto(f, flen+interfield, len(f)))
        fd.write('\n')

        for r in self.rows:
            for f in self.fields:
                flen = self.lens[f]
                fd.write(self.padto(r.data[f], flen+interfield, r.elens[f]))
            fd.write('\n')

class Row(object):
    def __init__(self):
        self.data = {}
        self.elens = {}

    def set(self, k, v, elen=None):
        self.data[k] = v
        self.elens[k] = elen or len(v)

    def __setitem__(self, k, v):
        return self.set(k, v, len(v))

def main():
    udata = get_userdata()

    totalvalue    = 0.0
    totalpurchase = 0.0
    totalopen     = 0.0

    fields = 'symbol count curprice curvalue purchaseprice today today% gaintoday totalgainper totalgain totalgain%'.split()
    t = Table(fields)

    for symbol, os in sorted(udata.iteritems()):
        mycount    = 0.0
        myvalue    = 0.0
        mypurchase = 0.0

        if symbol == 'CASH':
            curprice = 1.0
            changetoday = 0.0
            changetodayperc = 0.0

        elif symbol == 'FEE':
            curprice = 0.0
            changetoday = 0.0
            changetodayperc = 0.0

        else:
            quote       = get_stock_quote(symbol)
            curprice    = float(quote['l_cur'])
            changetoday = float(quote['c'])
            changetodayperc = float(quote['cp'])

        for o in os:
            mycount    += o.count
            myvalue    += o.count * curprice
            mypurchase += o.count * o.bought

        mygain = myvalue - mypurchase
        gainper = (myvalue - mypurchase)/mycount
        gaintoday = mycount * changetoday
        totalgainperc = mygain/mypurchase*100
        r = Row()
        r['symbol']          = symbol
        r['count']           = '%.0f' % mycount
        r['curprice']        = locale.currency(curprice, grouping=True)
        r['curvalue']        = locale.currency(myvalue, grouping=True)
        r['purchaseprice']   = locale.currency(mypurchase, grouping=True)
        r.set('today',       * cgain(locale.currency(changetoday, grouping=True), changetoday))
        r.set('today%',      * cgain('%.2f%%' % changetodayperc, changetodayperc))
        r.set('gaintoday',   * cgain(locale.currency(gaintoday, grouping=True), gaintoday))
        r.set('totalgainper',* cgain(locale.currency(gainper, grouping=True), gainper))
        r.set('totalgain',   * cgain(locale.currency(mygain, grouping=True), mygain))
        r.set('totalgain%',  * cgain('%.2f%%' % totalgainperc, totalgainperc))

        t.append(r)

        totalvalue    += myvalue
        totalpurchase += mypurchase
        totalopen     += myvalue - changetoday

    t.dump(sys.stdout)

    print 'Portfolio value:\t%s' % locale.currency(totalvalue, grouping=True)
    print 'Total purchase price:\t%s' % locale.currency(totalpurchase, grouping=True)

    todaygain = totalvalue-totalopen
    todaygainperc = todaygain / totalopen * 100
    print ('Total gain today:\t%s (%s)'
           % (cgain(locale.currency(todaygain, grouping=True), todaygain)[0],
              cgain('%.3f%%' % todaygainperc, todaygainperc)[0]))

    gain = totalvalue - totalpurchase
    gainperc = gain/totalpurchase*100
    print ('Total portfolio gain:\t%s (%s)'
           % (cgain(locale.currency(gain, grouping=True), gain)[0],
              cgain('%.3f%%' % gainperc, gainperc)[0]))

if __name__ == '__main__':
    main()
