import os
import tox
path = os.path.join(os.getcwd(), 'src')
os.chdir(path)
tox.cmdline() # environment is selected by ``TOXENV`` env variable
