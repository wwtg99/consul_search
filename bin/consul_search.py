import os
import sys


sys.path.insert(0, os.path.abspath('lib'))
from consulsearch.application import Application


if __name__ == '__main__':
    app = Application()
    app.run()
