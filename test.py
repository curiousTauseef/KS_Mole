import itertools

def my_generator(a):
    yield a

for i in itertools.chain(my_generator(34), [5]):
    print i
