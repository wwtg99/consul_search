Consul Search
=============

Search in the consul key/values.

# Installation

```
python setup.py install
```

# Usage

## Search values

```
consul_search -c config.yml -q ^consul$
```

While `-q` option support regrex to search in the consul value.

## Search keys

```
consul_search -c config.yml -f keys -q consul
```
