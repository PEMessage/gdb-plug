

import os
import sys

if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    upper_dir = os.path.dirname(script_dir)
    sys.path.insert(0, upper_dir)

    from gdbplug import Plug
    Plug.begin(home=os.path.join(upper_dir, 'out'))
    if True:
        Plug.plug("lebr0nli/GEP")
    Plug.end()
    Plug.update()
    Plug.load("GEP")

