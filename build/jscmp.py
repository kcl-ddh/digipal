'''
Tool to compare the META from two different requests

Example:

wget http://localhost:8080/digipal/api/meta/ -O meta1.js

[Change code or config (nging, uwsgi)]

wget http://localhost:8080/digipal/api/meta/ -O meta2.js

$ python build/jscmp.py meta1.js meta2.js 
            RUN_MAIN                           true                          false
     SERVER_SOFTWARE   WSGIServer/0.1 Python/2.7.10                           None
    SERVER_SOFTWARE2                           None   WSGIServer/0.1 Python/2.7.10
          wsgi.input <class 'socket._fileobject'><socket._fileobject object at 0x7f2c814fcbd0> <class 'socket._fileobject'><socket._fileobject object at 0x7f2c814fcc50>
         CSRF_COOKIE ufJ83DewRrigoij5dhZXO6MCDD0qklWz A0FoR855nI6u3IMLTEwoG0ENePtnl1xy
'''

import sys
args = sys.argv

script_name = args.pop(0)
if len(args) != 2:
    print 'Usage: %s FILE1 FILE2' % script_name
    exit()

import json
c = []
for f in args:
    c.append(json.load(open(f, 'rt')))

for k in set(c[0].keys()).union(set(c[1].keys())):
    if c[0].get(k) != c[1].get(k):
        print '%-20.20s | %-30.30s | %-30.30s' % (k, c[0].get(k), c[1].get(k))
