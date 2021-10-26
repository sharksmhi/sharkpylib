subscribers = dict()


def subscribe(event_type, func):
    subscribers.setdefault(event_type, set())
    subscribers[event_type].add(func)


def post_event(event_type, *args, **kwargs):
    for func in subscribers.get(event_type, []):
        func(*args, **kwargs)


def test_sub(*args, **kwargs):
    print(args)
    print(kwargs)


def test_event():
    print('Testing event')
    post_event('test', 'Test data from test_event')
    print('DONE!')


if __name__ == '__main__':
    import time
    print('Starting')
    subscribe('test', test_sub)
    time.sleep(3)
    test_event()
    time.sleep(2)
    print('ending')



