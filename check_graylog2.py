#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import datetime
import distutils.version
import json
import nagiosplugin
import nagiosplugin.performance
import nagiosplugin.state
import sys
import time

if sys.version_info >= (3,0):
	import urllib.error
	import urllib.request
else:
	import urllib2


class Graylog2Processing(nagiosplugin.Context):
	def evaluate(self, metric, resource):
		if metric.value:
			return self.result_cls(nagiosplugin.state.Ok, "Graylog2 Server is processing messages", metric)
		else:
			return self.result_cls(nagiosplugin.state.Critical, "Graylog2 Server is not processing messages", metric)


class Graylog2ServerID(nagiosplugin.Context):
	def performance(self, metric, resource):
		return nagiosplugin.performance.Performance(metric.name, metric.value)


class Graylog2IndexerFailures(nagiosplugin.Context):
	def evaluate(self, metric, resource):
		failures = metric.value
		if len(failures) == 0:
			return self.result_cls(nagiosplugin.state.Ok, "No indexer failures")
		else:
			failure = failures[0]

			# parse timestamp
			fmt = "%Y-%m-%dT%H:%M:%S.%fZ"
			timestamp = datetime.datetime.strptime(failure['timestamp'], fmt)

			if datetime.datetime.utcnow() - timestamp < datetime.timedelta(hours=2):
				return self.result_cls(nagiosplugin.state.Warn, "Indexer failure at %s: %s" % (failure['timestamp'], failure['message']))
			else:
				return self.result_cls(nagiosplugin.state.Ok, "No indexer failure within last hour")


class Graylog2Summary(nagiosplugin.Summary):
	"""Status line conveying message processing status.
	"""
	def ok(self, results):
		return '%s events/sec' % results['throughput'].metric.value


class Graylog2Check(nagiosplugin.Resource):
	def __init__(self, args):
		self.args = args
		if args.ssl:
			proto = "https"
		else:
			proto = "http"
		api_base_uri = '%s://%s:%d' % (proto, self.args.host, int(self.args.port))
		if args.url is not None:
			api_base_uri += args.url
		self.api_base_uri = api_base_uri

	def probe(self):
		# initialize api handler
		query_start = time.time()

		self.init_api()

		system = self.get_api_data('/system')

		if distutils.version.LooseVersion(system['version']) < distutils.version.LooseVersion('2.0.0'):
			yield nagiosplugin.Metric('graylog2_serverid', system['server_id'])
		else:
			yield nagiosplugin.Metric('graylog2_nodeid', system['node_id'])
			yield nagiosplugin.Metric('graylog2_clusterid', system['cluster_id'])

		yield nagiosplugin.Metric('graylog2_processing', system['is_processing'])

		if distutils.version.LooseVersion(system['version']) < distutils.version.LooseVersion('4.0.0'):
			events = self.get_api_data('/count/total')
			yield nagiosplugin.Metric('events', events['events'])
		else:
			events = self.get_api_data('/system/indexer/overview')
			yield nagiosplugin.Metric('events', events['counts']['events'])


		inputs = self.get_api_data('/system/inputs')
		yield nagiosplugin.Metric('inputs', inputs['total'])

		throughput = self.get_api_data('/system/throughput')
		yield nagiosplugin.Metric('throughput', throughput['throughput'])

		indexer_failures = self.get_api_data('/system/indexer/failures?limit=1&offset=0')
		yield nagiosplugin.Metric('indexer_failures', indexer_failures['failures'])

		duration = time.time() - query_start
		yield nagiosplugin.Metric('query_time', duration, uom='s')

	def init_api(self):
		if sys.version_info >= (3, 0):
			passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
			passman.add_password(None, self.api_base_uri, self.args.username, self.args.password)
			urllib.request.install_opener(urllib.request.build_opener(urllib.request.HTTPBasicAuthHandler(passman)))
		else:
			passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
			passman.add_password(None, self.api_base_uri, self.args.username, self.args.password)
			urllib2.install_opener(urllib2.build_opener(urllib2.HTTPBasicAuthHandler(passman)))

	def get_api_data(self, suffix):
		uri = "%s%s" % (self.api_base_uri, suffix)
		return self.__get_json(uri)

	@staticmethod
	def __get_json(uri):
		if sys.version_info >= (3, 0):
			try:
				req = urllib.request.Request(uri)
				resp = urllib.request.urlopen(req)
			except urllib.error.HTTPError as e:
				raise RuntimeError('Graylog2 API Failure: %s' % str(e))
			except urllib.error.URLError as e:
				raise RuntimeError('Graylog2 API URLError: %s' % str(e))
		else:
			try:
				req = urllib2.Request(uri)
				resp = urllib2.urlopen(req)
			except urllib2.HTTPError as e:
				raise RuntimeError('Graylog2 API Failure: %s' % str(e))
			except urllib2.URLError as e:
				raise RuntimeError('Graylog2 API URLError: %s' % str(e))

		body = resp.read()

		try:
			j = json.loads(body)
		except ValueError as msg:
			raise RuntimeError("Graylog2 API returned non-JSON value: %s" % str(msg))

		return j


@nagiosplugin.guarded
def main():
	argp = argparse.ArgumentParser()
	argp.add_argument('-v', '--verbose', action='count', default=0)
	argp.add_argument('-u', '--username', default='admin', help='Graylog2 username (default: %(default)s)')
	argp.add_argument('--password', help='Graylog2 password')
	argp.add_argument('-H', '--host', default="localhost", help='Hostname or network address to probe (default: %(default)s)')
	argp.add_argument('-p', '--port', default=12900, help='TCP port to probe (default: %(default)s)')
	argp.add_argument('-s', '--ssl', action='store_true', help="Connect using ssl")
	argp.add_argument('--url', default=None, help="Add a URL prefix (like /api) for proxied Graylog instances, default is no prefix")
	argp.add_argument('-w', '--warn', default=1.0, help="Warning time for response (default: %(default)s)")
	argp.add_argument('-c', '--crit', default=2.0, help="Critical time for response (default: %(default)s)")
	args = argp.parse_args()

	if args.url is not None:
		if not args.url.startswith("/"):
			raise RuntimeError("URL part needs to start with /")
		if args.url.endswith("/"):
			raise RuntimeError("URL part should not end with /")

	check = nagiosplugin.Check(Graylog2Check(args))
	check.add(nagiosplugin.ScalarContext('throughput', '@0', fmt_metric='Processing {value} messages / sec'))
	check.add(nagiosplugin.ScalarContext('events', '@0'))
	check.add(nagiosplugin.ScalarContext('inputs', '@0'))

	check.add(nagiosplugin.ScalarContext('query_time', ":%s" % args.warn, ":%s" % args.crit))
	check.add(Graylog2Processing('graylog2_processing'))
	check.add(Graylog2ServerID('graylog2_serverid'))
	check.add(Graylog2ServerID('graylog2_nodeid'))
	check.add(Graylog2ServerID('graylog2_clusterid'))
	check.add(Graylog2IndexerFailures('indexer_failures'))
	check.add(Graylog2Summary())
	check.main(verbose=args.verbose)

if __name__ == '__main__':
	main()
