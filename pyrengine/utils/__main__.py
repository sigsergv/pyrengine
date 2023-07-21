'''Utils script for pyrengine operations
'''

import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='python3 -m pyrengine.utils', description='asdad')
    parser.add_argument('-s', dest='show', help='Show application parameter, allowed values are: alembic_migrations, examples_dir')
    args = parser.parse_args()

    if args.show == 'alembic_migrations':
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'migrations'))
        print(path)
    elif args.show == 'examples_dir':
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'examples'))
        print(path)
