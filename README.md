Consul Search
=============

Search in the consul key/values.

# Installation

Install from patsnap internal repository
```
pip install consul-search
```

Or, you can install from source
```
python setup.py install
```

# Configuration

Create `config.yml` and change values from `config.example.yml`.

Configuration description please refer to `config.example.yml`

# Usage

Search in values

```
consul_search -c config.yml -q consul
```

Search in keys

```
consul_search -c config.yml -f keys -q consul
```

Search with regex
```
consul_search -c config.yml -q ^consul$ -e
```

Restrict search root
```
consul_search -c config.yml -q consul -t root
```

Show more results (default show only 10 results)
```
consul_search -c config.yml -q consul -l 20
```

Change output type, support text, json or csv
```
consul_search -c config.yml -q consul --output-type=json
```

Output to file
```
consul_search -c config.yml -q consul -o out.txt
```
