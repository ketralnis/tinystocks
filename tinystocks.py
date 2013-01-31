#!/usr/bin/env python

import os.path
import json
import urllib2
from collections import namedtuple
from termcolor import colored

import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

def get_stock_quote(ticker_symbol):
    # shamelessly stolen from http://coreygoldberg.blogspot.com/2011/09/python-stock-quotes-from-google-finance.html
    url = 'http://finance.google.com/finance/info?q=%s' % ticker_symbol.upper()
    data = urllib2.urlopen(url).read()
    lines = data.splitlines()
    lines = [x for x in lines if x not in ('// [', ']')] # they have some weird-ass format
    return json.loads(''.join(lines))

ownership = namedtuple('ownership', 'symbol count bought')

def cgain(s, val):
    if val == 0.0:
        return s
    elif val > 0.0:
        return colored(s, 'white')
    elif val < 0.0:
        return colored(s, 'red')


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

def main():
    udata = get_userdata()

    totalvalue    = 0.0
    totalpurchase = 0.0

    fields = 'symbol curprice count curvalue purchaseprice gainper totalgain totalgain%'.split()
    print ' '.join(('%15s' % f) for f in fields)

    for symbol, os in sorted(udata.iteritems()):
        mycount    = 0.0
        myvalue    = 0.0
        mypurchase = 0.0

        if symbol == 'CASH':
            curprice = 1.0

        else:
            quote    = get_stock_quote(symbol)
            curprice = float(quote['l_cur'])

        for o in os:
            mycount    += o.count
            myvalue    += o.count * curprice
            mypurchase += o.count * o.bought

        mygain = myvalue - mypurchase
        gainper = (myvalue - mypurchase)/mycount
        totalgainperc = mygain/mypurchase*100
        print ('%15s %+15s %15.2f %+15s %+15s %s %s %s'
               % (symbol,
                  locale.currency(curprice),
                  mycount,
                  locale.currency(myvalue),
                  locale.currency(mypurchase),
                  cgain('%15s' % locale.currency(gainper), gainper),
                  cgain('%15s' % locale.currency(mygain), mygain),
                  cgain('%14.2f%%' % totalgainperc, totalgainperc)))

        totalvalue    += myvalue
        totalpurchase += mypurchase

    print 'Portfolio value: %s' % locale.currency(totalvalue)
    print 'Total purchase price: %s' % locale.currency(totalpurchase)

    gain = totalvalue - totalpurchase
    gainperc = gain/totalpurchase*100
    print ('Total portfolio gain: %s (%s)'
           % (cgain(locale.currency(gain), gain),
              cgain('%.2f%%' % gainperc, gainperc)))

if __name__ == '__main__':
    main()
