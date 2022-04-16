from django.core.cache import cache
from copy import copy
import datetime

from CalendarApi.constraints import C_datedelta


lifetime = (C_datedelta.days+1)*24*60*60  # 8 day


def set_blocked_time(date, start_time, end_time, lifetime=lifetime):
    if cache.get('blocked_time'):
        blocked_time = cache.get('blocked_time')
        today = datetime.date.today()
        for k in blocked_time.copy().keys():
            if k < today:
                del blocked_time[k]
            else:
                break
        if blocked_time.get(date):
            is_contain = False
            for times_id in range(len(blocked_time[date])):
                if blocked_time[date][times_id][0] > start_time:
                    blocked_time[date].insert(
                        times_id, (start_time, end_time)
                    )
                    break
            if not is_contain:
                blocked_time[date].append((start_time, end_time))
            lifetime = 7*24*60*60
            cache.set('blocked_time', blocked_time, lifetime)
        else:
            blocked_list_sorted = {}
            is_contain = False
            for block_d, block_t in blocked_time.items():
                if (date < block_d) and not is_contain:
                    blocked_list_sorted[date] = [(start_time, end_time), ]
                    blocked_list_sorted[block_d] = block_t
                    is_contain = True
                else:
                    blocked_list_sorted[block_d] = block_t
            if not is_contain:
                blocked_list_sorted[date] = [(start_time, end_time), ]
            lifetime = 7*24*60*60
            cache.set('blocked_time', blocked_list_sorted, lifetime)
    else:
        blocked_time = {}
        blocked_time[date] = [(start_time, end_time), ]
        # lifetime = 7*24*60*60
        # lifetime = 60*5
        cache.set('blocked_time', blocked_time, lifetime)
    return True


def del_blocked_time(date, start_time, lifetime=lifetime):
    blocked_time = cache.get('blocked_time')
    if not blocked_time[date]:
        return False
    for times in blocked_time[date]:
        if times[0] == start_time:
            blocked_time[date].remove(times)
    if len(blocked_time[date]) == 0:
        del blocked_time[date]
    cache.set('blocked_time', blocked_time, lifetime)
    return True


def get_blocked_time() -> dict:
    blocked_time = cache.get('blocked_time')
    if not blocked_time:
        return None
    today = datetime.date.today()
    for k in blocked_time.copy().keys():
        if k < today:
            del blocked_time[k]
        else:
            break
    return blocked_time  # dict(list(tuple))
