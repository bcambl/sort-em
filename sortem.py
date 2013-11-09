#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Copyright (c) 2013, Blayne Campbell
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.
'''
__appname__ = "Sort'em"
__license__ = "BSD"
__author__ = "Blayne Campbell"
__date__ = "October 31, 2013"
__website__ = "http://blaynecampbell.com"
'''
Sort'em was created to sort and detect file duplicates based on MD5.
This project was inspired by one of my collegues Mario.
'''

import sqlite3
import hashlib
import sys
import os

'''Setting Directory to Process'''
print "Provide the ABSOLUTE PATH to process.."
sdir = str(raw_input("Directory:"
            "(Default: " + os.getcwd() + '/files' + "):"))
if len(sdir) >= 1:
        if os.path.exists(sdir):
            print "Now processing: ", sdir
        else:
            print "Specified path does not exist!"
            exit()
else:
    print "Processing default location: " + os.getcwd() + "/files"
    sdir = os.getcwd() + '/files'


def md5sum(fin):
    '''Generate md5 checksum for current file'''
    md5 = hashlib.md5()
    with open(fin, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()

count = 1
con = None
try:
    '''Initialize database and create table for file records'''
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS files")
    cur.execute("CREATE TABLE files(id INT, name TEXT,"
                "type INT, path TEXT, hash STR, master INT, dupe INT)")
    for path, subdirs, files in os.walk(sdir):
        for name in files:
            '''Populate table with file records'''
            n, e = os.path.splitext(name)
            h = md5sum(os.path.join(path, name))
            cur.execute("""INSERT INTO files VALUES (
                ?, ?, ?, ?, ?, 0, 0)""",
                        (count, name, e, path, h))
            count += 1
            con.commit()
except sqlite3.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)

finally:
    if con:
        con.close()

con = sqlite3.connect('data.db')
cur = con.cursor()
cur.execute("""SELECT * FROM files""")
data = cur.fetchone()
while data:
    '''Mark master and duplicate files in database file'''
    (i, n, t, p, h, m, d) = data
    if d == 0 and m == 0:
        cur.execute("""UPDATE files SET master = 1
            WHERE id = ?""", (i,))
        h = str(h)
        cur.execute("""UPDATE files SET dupe = 1 WHERE
            hash = ? AND id <> ? AND master <> 1""", (h, i,))
    con.commit()
    cur.execute("""SELECT * FROM files WHERE id > ?""", (i,))
    data = cur.fetchone()

if con:
        con.close()
'''
At this point the script is extendable to process the duplicates as you wish.
'''


'''
The following code simply creates a logfile stating all duplicate files
found in the database file.
'''
con = sqlite3.connect('data.db')
cur = con.cursor()
cur.execute("""SELECT * FROM files WHERE dupe = 1""")
data = cur.fetchall()
print "Duplicate Files Found:"
f = open('duplicates.log', 'wb')
for dupe in data:
    print dupe[3] + '/' + dupe[1]
    '''Newline for UNIX systems \n OR Windows systems \r\n'''
    f.write(dupe[3] + '/' + dupe[1] + '\n')
f.close()

con.close()