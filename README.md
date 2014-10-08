[![Build Status](https://travis-ci.org/CygnusNetworks/nagios-plugin-graylog2.svg?branch=master)](https://travis-ci.org/CygnusNetworks/nagios-plugin-graylog2)
nagios-plugin-graylog2
======================
An [Graylog2] availability and performance monitoring plugin for Nagios.

[Graylog2]: http://www.graylog2.org

How it works
------------
This plugin works by submitting a REST API request to a local or remote Graylog2 server. Graylog2 server will respond to this API request by default. If yours don't, check that you have configured rest_listen_uri correctly.

This monitoring checks if the graylog2 server is processing data (as reported by the REST API). 
For performance monitoring, the number of data sources, number of recorded messages and the throughput is reported.
Additionally the REST API response time is measured and submitted to nagios as load indicator.


Usage
-----
```
check_graylog2 [-h] [-v] [-u USERNAME] [--password PASSWORD] [-H HOST]
                      [-p PORT] [-w WARN] [-c CRIT]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose
  -u USERNAME, --username USERNAME
                        Graylog2 username (default: admin)
  --password PASSWORD   Graylog2 password
  -H HOST, --host HOST  Hostname or network address to probe (default:
                        localhost)
  -p PORT, --port PORT  TCP port to probe (default: 12900)
  -w WARN, --warn WARN  Warning time for response (default: 1.0)
  -c CRIT, --crit CRIT  Critical time for response (default: 2.0)
```

Requirements
------------

- Python 2.7
- nagiosplugin

