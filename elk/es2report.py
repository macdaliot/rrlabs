#!/usr/bin/env python3

import elasticsearch, getopt, logging, sys, urllib3

logging.basicConfig(level = logging.ERROR)

def usage():
    print('Usage: {} [OPTIONS]'.format(sys.argv[0]))
    print('Options:')
    print('  -d             enable debug')
    print('  -p port        the port of the ES server (default "9200")')
    print('  -s string      the name or the address of the ES server (default "localhost")')
    print('  -t integer     the version of the discovery (default "19700101")')
    print('  -w string      the workplace of the discovery (i.e. "example")')

def main():
    # Default options
    workplace = None
    version = 19700101
    es_host = 'localhost'
    es_port = 9200

    # Reading options
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'dp:s:t:w:')
    except getopt.GetoptError as err:
        logging.error(err)
        usage()
        sys.exit(255)
    for opt, arg in opts:
        if opt == '-d':
            logging.getLogger().setLevel(logging.DEBUG)
        elif opt == '-p':
            es_port = int(arg)
        elif opt == '-s':
            es_host = arg
        elif opt == '-t':
            version = arg
        elif opt == '-w':
            workplace = arg.lower()
        else:
            assert False, 'unhandled option'

    # Checking options
    es = elasticsearch.Elasticsearch([{'host': es_host, 'port': es_port}])
    if not es.ping(request_timeout = 0.5):
        logging.error('cannot connect to ElasticSearch server "{}:{}"'.format(es_host, es_port))
        sys.exit(255)
    if not workplace:
        logging.error('option "-w" not set')
        sys.exit(255)
    index = '{}-{}'.format(workplace, version)

    # Reading domains
    s = es.search(index = index, doc_type = 'domain', body = {'size': 10000, 'query': {'match_all': {}}})
    domains_total = s['hits']['total']
    if domains_total > 10000:
        logging.error('TODO: must implement scroll')
        sys.exit(255)
    domains = []
    for domain in s['hits']['hits']:
        domains.append(domain['_source'])

    # Printing the report
    output = '# Internet domains\n'
    output += '{} Internet domains has been found:\n'.format(domains_total)
    for domain in domains:
        output += '* {}\n'.format(domain['name'])
    print(output)

if __name__ == '__main__':
    main()
