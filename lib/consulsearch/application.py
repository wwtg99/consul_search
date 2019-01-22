import argparse
from hsettings.loaders import YamlLoader
from consulsearch.search import ConsulKvSearch


def init_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file path', required=True)
    parser.add_argument('-t', '--root', help='search root path', default='')
    parser.add_argument('-f', '--fields', help='search fields, keys or values, default values', default='values',
                        choices=['keys', 'values'])
    parser.add_argument('-q', '--query', help='query patterns, support regrex', required=True)
    parser.add_argument('-l', '--limit', help='query result limits, default 10', default=10)
    return parser.parse_args(args=args)


def main():
    args = init_args()
    if args.config:
        config = args.config
        settings = YamlLoader.load(config)
        root = args.root or settings.get('search.root', '')
        search = ConsulKvSearch(settings)
        if args.fields == 'values':
            res = search.search_value(args.query, root=root, limit=args.limit)
        else:
            res = search.search_key(args.query, root=root, limit=args.limit)
        for r in res:
            print(r)


if __name__ == '__main__':
    main()
