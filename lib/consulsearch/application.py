import argparse
import logging
from hsettings import Settings
from hsettings.loaders import YamlLoader, DictLoader
from colorama import Fore, Back, Style
from . import __prog__, __version__
from consulsearch.search import ConsulKvSearch


settings = Settings()


class Application:

    CONF_MAPPING = {
        'host': 'consul.host',
        'port': 'consul.port',
        'scheme': 'consul.scheme',
        'token': 'consul.token',
        'root': 'search.root',
        'limit': 'search.limit',
        'output_file': 'search.output_file',
        'output_type': 'search.output_type',
        'regex': 'search.regex',
        'log_level': 'log.log_level'
    }

    def __init__(self):
        self._console_handlers = []

    def get_arg_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--version', help='show version', action='version', version=' '.join([__prog__, __version__]))
        parser.add_argument('-c', '--config', help='config file path')
        parser.add_argument('-t', '--root', help='search root path')
        parser.add_argument('-f', '--fields', help='search fields, keys or values, default values', default='values',
                            choices=['keys', 'values'])
        parser.add_argument('-q', '--query', help='query string', required=True)
        parser.add_argument('-e', '--regex', help='query string support regex', action='store_true')
        parser.add_argument('-l', '--limit', help='query result limits')
        parser.add_argument('-o', '--output-file', help='output file path')
        parser.add_argument('--output-type', help='output type, text, json or csv', choices=['text', 'json', 'csv'],
                            default='text')
        parser.add_argument('--host', help='consul host')
        parser.add_argument('--port', help='consul port')
        parser.add_argument('--scheme', help='consul scheme')
        parser.add_argument('--token', help='consul ACL token')
        parser.add_argument('--clear-cache', help='clear cache before search', action='store_true')
        parser.add_argument('--log-level', help='log level', default='INFO')
        return parser

    def init_logger(self):
        log_level = settings.get('log.log_level', 'INFO')
        log_formatter = '[%(levelname)s] %(asctime)s : %(message)s'
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        logger_levels = [
            logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG
        ]
        for level in logger_levels:
            handler = self._create_console_level_handler(level, log_formatter)
            if handler:
                self._console_handlers.append(handler)
                root_logger.addHandler(handler)

    def merge_settings(self, args):
        config_file = args.config
        if config_file:
            settings.merge(YamlLoader.load(config_file))
        d = dict([(k, v) for k, v in vars(args).items() if k in self.CONF_MAPPING and v is not None])
        if d:
            settings.merge(DictLoader.load(d, key_mappings=self.CONF_MAPPING, only_key_mappings_includes=True))
        return settings

    def process(self, args):
        self.merge_settings(args)
        self.init_logger()
        try:
            app = ConsulKvSearch(settings)
            if args.clear_cache:
                logging.debug('Clear all cache...')
                app.clear_cache()
            logging.debug('Start to search {} in kv {}'.format(args.query, args.fields))
            res = app.search(query=args.query, field=args.fields)
            return res
        except Exception as e:
            logging.error(e)
            return []

    def output(self, result, output_type):
        if not result:
            logging.info('No results found!')
        if output_type == 'json':
            output = JsonOutput(settings)
        elif output_type == 'csv':
            output = CsvOutput(settings)
        else:
            output = TextOutput(settings)
        output.output(result)

    def run(self, args=None, parser=None):
        if not parser:
            parser = self.get_arg_parser()
        arg = parser.parse_args(args=args)
        res = self.process(arg)
        self.output(res, arg.output_type)

    def _create_console_level_handler(self, level, formatter):
        level_map = {
            logging.ERROR: {
                'filter': lambda record: record.levelno >= logging.ERROR,
                'formatter': Fore.RED + formatter + Style.RESET_ALL
            },
            logging.WARNING: {
                'filter': lambda record: record.levelno == logging.WARN,
                'formatter': Fore.YELLOW + formatter + Style.RESET_ALL
            },
            logging.INFO: {
                'filter': lambda record: record.levelno == logging.INFO,
                'formatter': Fore.GREEN + formatter + Style.RESET_ALL
            },
            logging.DEBUG: {
                'filter': lambda record: record.levelno < logging.INFO,
                'formatter': Style.RESET_ALL + formatter
            }
        }
        if level in level_map:
            handler = logging.StreamHandler()
            hfilter = logging.Filter()
            hfilter.filter = level_map[level]['filter']
            handler.addFilter(hfilter)
            handler.setFormatter(logging.Formatter(level_map[level]['formatter']))
            handler.setLevel(logging.DEBUG)
            return handler
        return None


class BaseOutput:

    def __init__(self, conf: Settings):
        self._settings = conf
        self.out_file = self._settings.get('search.output_file', '')

    def output(self, results):
        if self.out_file:
            with open(self.out_file, 'w') as fp:
                for item in results:
                    fp.write(self.parse_item(item) + '\n')
        else:
            for item in results:
                print(self.parse_item(item))

    def parse_item(self, item):
        return item


class TextOutput(BaseOutput):

    def parse_item(self, item):
        return str(item)


class JsonOutput(BaseOutput):

    def output(self, results):
        import json
        if self.out_file:
            with open(self.out_file, 'w') as fp:
                json.dump(results, fp, indent=4)
        else:
            print(json.dumps(results, indent=4))


class CsvOutput(BaseOutput):

    def parse_item(self, item):
        from collections import Iterable
        if isinstance(item, Iterable):
            return ','.join(item)
        else:
            return str(item)


def main():
    app = Application()
    app.run()
