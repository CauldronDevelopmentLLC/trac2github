#!/usr/bin/env python

import sys
import json
import datetime
import time
import re


colors = '''
  c2771a 7a87e5 43a78c e94175 55b223 845460 9ea154 bd63ab
  4d9dc7 dd7864 296d2f 406871 7b5e2e e95142 9794b0 765085
  426596 a33b5c 9b5023 7aa3a0 68af6f b69526 d37be2 c03949
  50673e bb7e94 98433c b58e53 ad80b3 3bafba 447711 8b9f2f
  e17ba6 c75321 356d5a 35b24a 63627b 4f97dd c44380 e960b0
  934676 d38046 a172ca 786c1d ce8979 6f9b72 c2676c 8e5c44
  44913f b44835 6a6dae e97d25 dd5f82 5892a6 925e15 428b85
  9494dc ed5e65 516b1c 6d984c ed6d44 7b8446 5fa631 32a568
'''.split()


# Utility functions
def pretty_json(data):
    return json.dumps(data, indent = 2, separators = (',', ':'))


# Parse options
from optparse import OptionParser

parser = OptionParser()

parser.add_option('-u', '--user', dest = 'user', help = 'GitHub user name')
parser.add_option('-o', '--org', dest = 'org', help = 'GitHub organization')
parser.add_option('-r', '--repo', dest = 'repo', help = 'GitHub repo')
parser.add_option('-t', '--token', dest = 'token', help = 'GitHub access token')
parser.add_option('-a', '--assignee', dest = 'assignee',
                  help = 'Override assignee')
parser.add_option('-c', '--create', action = 'store_true', dest = 'create',
                  default = False, help = 'Create the GitHub repo')
parser.add_option('-d', '--delete', action = 'store_true', dest = 'delete',
                  default = False, help = 'Delete the GitHub repo')
parser.add_option('-p', '--public', dest = 'public', action = 'store_true',
                  default = False, help = 'New GitHub repo is public')
parser.add_option('', '--add-labels', dest = 'add_labels',
                  action = 'store_true', default = False,
                  help = 'Add missing GitHub labels')
parser.add_option('', '--replace-labels', dest = 'replace_labels',
                  action = 'store_true', default = False,
                  help = 'Replace all GitHub labels')
parser.add_option('-i', '--preserve-ids', dest = 'preserve_ids',
                  action = 'store_true', default = False,
                  help = 'Replace all GitHub labels')
parser.add_option('', '--db', dest = 'trac_db', default = 'trac.db',
                  help = 'Trac sqlite DB')
parser.add_option('', '--components', dest = 'components',
                  help = 'Restrict to a specific Trac components. ' +
                  'Comma separated list.')
parser.add_option('-l', '--limit', dest = 'limit', metavar = 'NUMBER',
                  type = 'int', help = 'Limit the number of tickets')
parser.add_option('', '--offset', dest = 'offset', metavar = 'NUMBER',
                  type = 'int', help = 'Start at ticket offset')
parser.add_option('-m', '--user-map', dest = 'user_map', metavar = 'FILE',
                  help = 'File containing a map of Trac users to GitHub users' +
                  ' in JSON format')
parser.add_option('-n', '--note', dest = 'note',
                  help = 'Add this note to all tickets.')

options, args = parser.parse_args()


# Validate options
if options.org is None: parser.error('Missing GitHub org')
if options.repo is None: parser.error('Missing Github repo')
if options.user_map is not None:
    user_map = json.load(open(options.user_map, 'r'))
else: user_map = None


# Authentication
from requests.auth import HTTPBasicAuth

if not options.token is None:
    auth = HTTPBasicAuth(options.token, 'x-oauth-basic')

else:
    if options.user is None: user = raw_input('GitHub Login: ')
    else: user = options.user

    from getpass import getpass
    password = getpass('GitHub Password: ')

    auth = HTTPBasicAuth(user, password)


# API Call
import requests

def api_call(method, path, data = None):
    print 'API: %s %s' % (method, path)

    hdrs = {'Accept': 'application/vnd.github.golden-comet-preview'}
    params = None
    json = None

    if data is not None:
        if method == 'GET': params = data
        else: json = data

    res = requests.request(method, 'https://api.github.com' + path,
                           auth = auth, json = json, headers = hdrs,
                           params = params)

    if res.status_code < 200 or 300 <= res.status_code:
        data = res.json()
        raise Exception, pretty_json(res.json())

    return None if res.status_code == 204 else res.json()

repo_path = '/repos/%s/%s' % (options.org, options.repo)


# Delete repo
if options.delete:
    try:
        print 'Deleting repo %s/%s' % (options.org, options.repo)
        api_call('DELETE', repo_path)

    except Exception, e:
        print e


# Create repo
if options.create:
    print 'Creating repo %s/%s' % (options.org, options.repo)
    data = {'name': options.repo, 'private': not options.public}
    api_call('POST', '/orgs/%s/repos' % options.org, data)


# Read Trac DB
import sqlite3

def dict_factory(cursor, row):
    d = {}
    for idx,col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def format_ts(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%dT%H:%M:%SZ')


def map_user(user):
    return user_map[user] if user_map is not None and user in user_map else user


def trac2md(text):
    text = re.sub('\r\n', '\n', text)
    text = re.sub(r'{{{(.*?)}}}', r'`\1`', text)

    def indent4(m):
        return '\n ' + m.group(1).replace('\n', '\n ')

    text = re.sub(r'(?sm){{{\n(.*?)\n}}}', indent4, text)
    text = re.sub(r'(?m)^====\s+(.*?)\s+====$', r'#### \1', text)
    text = re.sub(r'(?m)^===\s+(.*?)\s+===$', r'### \1', text)
    text = re.sub(r'(?m)^==\s+(.*?)\s+==$', r'## \1', text)
    text = re.sub(r'(?m)^=\s+(.*?)\s+=$', r'# \1', text)
    text = re.sub(r'^ * ', r'****', text)
    text = re.sub(r'^ * ', r'***', text)
    text = re.sub(r'^ * ', r'**', text)
    text = re.sub(r'^ * ', r'*', text)
    text = re.sub(r'^ \d+. ', r'1.', text)
 
    a = []
    for line in text.split('\n'):
        if not line.startswith(' '):
            line = re.sub(r'\[(https?://[^\s\[\]]+)\s([^\[\]]+)\]',
                          r'[\2](\1)', line)
            line = re.sub(r'\[(wiki:[^\s\[\]]+)\s([^\[\]]+)\]',
                          r'[\2](/\1/)', line)
            line = re.sub(r'\!(([A-Z][a-z0-9]+){2,})', r'\1', line)
            line = re.sub(r'\'\'\'(.*?)\'\'\'', r'*\1*', line)
            line = re.sub(r'\'\'(.*?)\'\'', r'_\1_', line)

        a.append(line)

    return cap_str('\n'.join(a), 10000)


conn = sqlite3.connect(options.trac_db)
conn.row_factory = dict_factory


c = conn.cursor()


# Get GitHub labels
github_labels = set()
for label in api_call('GET', repo_path + '/labels'):
    github_labels.add(label['name'])


# Remove GitHub labels
if options.replace_labels:
    for label in github_labels:
        print 'Deleting label ' + label
        api_call('DELETE', repo_path + '/labels/' + label)

    github_labels = set()


# Add Trac labels to GitHub
if options.add_labels or options.replace_labels:
    labels = set()
    sql = 'SELECT * FROM enum WHERE type = "ticket_type" OR type = "resolution"'

    for label in c.execute(sql):
        if label['name'] not in github_labels:
            labels.add(label['name'])

    count = 0
    for label in labels:
        print 'Adding label ' + label

        color = colors[count]
        api_call('POST', repo_path + '/labels', {'name': label, 'color': color})
        count += 1


# Close tickets
import threading
import Queue

start_time = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
start_time = datetime.datetime.now().strftime('%Y-%m-%d')
responses = Queue.Queue()
done = threading.Event()
failed = 0
total = 0


def cap_str(s, l):
    return s if len(s) <= l else s[0 : l - 3] + '...'


def get_ticket_id(result):
    return int(re.sub(r'^.*/(\d+)$', r'\1', result['issue_url']))

def close_ticket(ticket_id):
    path = repo_path + '/issues/%d' % ticket_id
    api_call('PATCH', path, {'state': 'closed'})


def process_responses():
    global start_time, responses, done, failed, total

    r = {}

    while r or not responses.empty() or not done.isSet():
        while not responses.empty():
            res = responses.get()
            r[res['id']] = res

        time.sleep(1)
        print '%d pending responses' % len(r)

        if r:
            res = api_call('GET', repo_path + '/import/issues',
                           data = {'since': start_time})

            for result in res:
                try:
                    if result['id'] not in r: continue
                    res = r[result['id']]

                    if result['status'] != 'pending':
                        total += 1
                        del r[result['id']]

                    if result['status'] == 'failed':
                        failed += 1
                        print pretty_json(result)
                        if options.preserve_ids:
                            print 'ID preservation failed'
                            sys.exit(1)

                    if result['status'] == 'imported':
                        ticket_id = get_ticket_id(result)
                        path = repo_path + '/issues/%d' % ticket_id

                        if res['close']:
                            api_call('PATCH', path, {'state': 'closed'})

                        if res['lock']:
                            pass # Not sure how to do this

                except Exception, e:
                    print e

    print 'Thread done'

thread = threading.Thread(target = process_responses)
thread.daemon = True
thread.start()


# Create tickets
sql = 'SELECT * FROM ticket'
where = []

if options.components:
    s = '(component = "'
    s += '" OR component = "'.join(options.components.split(','))
    s += '")'
    where.append(s)

if options.offset: where.append('%d < id' % options.offset)

if where: sql += ' WHERE ' + ' AND '.join(where)

sql += ' ORDER BY id'
if options.limit: sql += ' LIMIT %d' % options.limit

current_id = 0

for ticket in c.execute(sql):
    current_id += 1

    if options.preserve_ids:
        while current_id < ticket['id']:
            # Create dummy issue
            data = {'issue': {'title': 'placeholder', 'body': 'dummy'}}
            res = api_call('POST', repo_path + '/import/issues', data)
            res['close'] = True
            res['lock'] = True
            responses.put(res)
            current_id += 1

    labels = []
    if ticket['type']: labels.append(ticket['type'])
    if ticket['resolution']: labels.append(ticket['resolution'])

    ticket['reporter'] = map_user(ticket['reporter'])
    ticket['owner'] = map_user(ticket['owner'])
    ticket['description'] = trac2md(ticket['description'])

    body = 'Trac | Data'
    body += '\n---: | :---'
    body += '\nTicket | %(id)d'
    body += '\nReported by | @%(reporter)s'

    keys = 'status component priority severity milestone keywords version'
    for key in keys.split():
      if ticket[key]: body += '\n%s | %%(%s)s' % (key.capitalize(), key)

    if options.note: body += '\nNote | %s' % options.note

    body += '\n\n%(description)s'

    issue = {
        'title': ticket['summary'],
        'body': body % ticket,
        'created_at': format_ts(ticket['time']),
        'assignee': options.assignee if options.assignee else ticket['owner'],
        'labels': labels
        }

    comments = []
    c2 = conn.cursor()
    sql = 'SELECT * FROM ticket_change WHERE ticket = %(id)d' % ticket
    sql += ' ORDER BY time'

    for change in c2.execute(sql):
        if change['field'] == 'comment':
            if not change['newvalue'].strip(): continue # Ignore empty

            change['author'] = map_user(change['author'])
            change['newvalue'] = trac2md(change['newvalue'])

            comments.append({
                    'created_at': format_ts(change['time']),
                    'body': '**Comment by @%(author)s**\n%(newvalue)s' % change
                    })

    data = {'issue': issue, 'comments': comments}
    c2.close()

    # Create issue
    if options.preserve_ids: time.sleep(1)
    res = api_call('POST', repo_path + '/import/issues', data)

    # Track response
    res['close'] = ticket['status'] == 'closed'
    res['lock'] = False
    responses.put(res)


# Wait for closing thread
done.set()

print 'Waiting'
while 1 < threading.active_count():
    time.sleep(0.1)


print 'Failed %d' % failed
print 'Total %d' % total
