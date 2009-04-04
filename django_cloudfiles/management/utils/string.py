from sys import stdout

def write(str):
    stdout.write(str)
    stdout.flush()        

ORDERS = (
    (10**(3*4), "TB"),
    (10**(3*3), "GB"),
    (10**(3*2), "MB"),
    (10**(3*1), "KB"),
    (10**(3*0), "B"),
)
def format_bytes(bytes):
    for order, mnemonic in ORDERS:
        if bytes > order:
            return bytes//order, mnemonic
