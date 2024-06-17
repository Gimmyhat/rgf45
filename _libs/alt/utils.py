import time

def progress(data_list, timeout=10):

    i, t0 = 0, 0
    if True:
        n = len(data_list)
    else:
        n = None

    for item in data_list:
        t1 = time.time()
        i += 1
        if t1-t0 > timeout:
            if n:
                print(i, 'of', n)
            else:
                print(i)
            t0 = t1
        yield item