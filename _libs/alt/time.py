from __future__ import absolute_import
from datetime import datetime, timedelta

def iso(dt):

    if dt.__class__.__name__=='date':
        return dt.strftime('%Y-%m-%d')
    elif dt.__class__.__name__=='time':
        return dt.strftime('%H:%M:%S')
    else:
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def from_iso(iso):
    
    if len(iso)==19:
        return datetime.strptime(iso,'%Y-%m-%d %H:%M:%S')
    
    if len(iso)==10:
        return datetime.strptime(iso,'%Y-%m-%d').date()

    return datetime.fromisoformat(iso)

def now():

    return iso( datetime.now() )

def today():

    return iso( datetime.now().date() )

def diff_format(dt0, dt1=None, tz=None, sec=False):

    if dt0 is None:
        return ''

    if not dt1:
        dt1 = datetime.now()
        if tz:
            dt1 += timedelta(hours=tz)

    if isinstance(dt1, (str)):
        dt1 = from_iso(dt1)
    if isinstance(dt0, (str)):
        dt0 = from_iso(dt0)

    diff = dt1 - dt0

    diff = abs(int(diff.total_seconds()))
    h = diff // 3600
    m = (diff % 3600) // 60
    s = diff % 60
    if h>=24:
        d = diff // (3600*24)
        h = (diff % (3600*24)) // 3600
        sd = '({0:d}d {1:02d}:{2:02d})'.format(d,h,m)
    else:
        if sec:
            sd = '({0:02d}:{1:02d}:{2:02d})'.format(h,m,s)
        else:
            sd = '({0:02d}:{1:02d})'.format(h,m)

    return sd
