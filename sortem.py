#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
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
"""
__appname__ = "Sort-em"
__license__ = "BSD"
__author__ = "Blayne Campbell"
__date__ = "October 31, 2013"
__website__ = "http://blaynecampbell.com/sort-em/"
__status__ = "Development"

import sqlite3
import hashlib
import shutil
import sys
import os


# Set Database Name
database = 'data.db'  # Useful for multiple database needs

# Do not edit
con = None
sdir = None
proc = None


def setdir():
    """
    Setting Directory to Process
    """
    print "Provide the ABSOLUTE PATH to process.."
    sdir = str(raw_input("Directory:"
                         "(" + os.getcwd() + '/files' + "):"))
    if len(sdir) >= 1:
            if os.path.exists(sdir):
                print "Now processing: ", sdir
            else:
                print "Specified path does not exist!"
                exit()
    else:
        print "Processing default location: " + os.getcwd() + "/files"
        sdir = os.getcwd() + '/files'
        return sdir


def admvdup():
    yes = {'yes', 'y', 'ye'}
    no = {'no', 'n', ''}
    proc = None
    while proc is None:
        print ""
        choice = raw_input("Move duplicates to the 'duplicates' directory?"
                           "(yes/NO)").lower()
        if choice in yes:
            print "You chose to MOVE files after analysis.."
            proc = 1
            return proc
        elif choice in no:
            print "You chose NOT to move files."
            proc = 0
            return proc
        else:
            sys.stdout.write("Please respond with 'yes' or 'no'")


def chksum(fin):
    """
    Generate sha512 checksum for current file
    """
    sha = hashlib.sha512()
    with open(fin, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * sha.block_size), b''):
            sha.update(chunk)
    return sha.hexdigest()


def index():
    count = 1
    con = None
    try:
        con = sqlite3.connect(database)
        cur = con.cursor()
        cur.execute("""DROP TABLE IF EXISTS files""")
        cur.execute("""CREATE TABLE files(id INT, name TEXT, type INT,
                    path TEXT, hash STR, master INT, dupe INT, moved INT)""")
        for path, subdirs, files in os.walk(sdir):
            for name in files:
                n, e = os.path.splitext(name)
                e = e.lstrip('.')
                h = chksum(os.path.join(path, name))
                cur.execute("""INSERT INTO files VALUES (
                    ?, ?, ?, ?, ?, 0, 0, 0)""",
                            (count, name, e, path, h))
                count += 1
                con.commit()
    except sqlite3.Error, e:
        print "Error %s:" % e.args[0]
        sys.exit(1)

    finally:
        if con:
            con.close()


def iddup():
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute("""SELECT * FROM files""")
    data = cur.fetchone()
    while data:
        (i, n, t, p, h, m, d, v) = data
        if d == 0 and m == 0:
            cur.execute("""UPDATE files SET master = 1
                WHERE id = ?""", (i,))
            h = str(h)
            cur.execute("""UPDATE files SET dupe = 1 WHERE
                hash = ? AND id <> ? AND master <> 1""", (h, i,))
        con.commit()
        cur.execute("""SELECT * FROM files WHERE id > ?""", (i,))
        data = cur.fetchone()


def duplog():
    """
    Create Logfile
    """
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute("""SELECT * FROM files WHERE dupe = 1""")
    data = cur.fetchall()
    if not data:
        print "No Duplicates found."
    else:
        print "Duplicate Files Found (see duplicates.log):"
    log = open('duplicates.log', 'wb')
    for dupe in data:
        log.write(dupe[3] + '/' + dupe[1] + '\n')  # UNIX: \n || Windows: \r\n
    log.close()


def duplink():
    """
    Create html file containing links to duplicates
    """
    con = sqlite3.connect(database)
    cur = con.cursor()
    cur.execute("""SELECT * FROM files where master='1'""")
    data = cur.fetchall()
    link = open('duplicates.html', 'wb')
    link.write('<html>'
            '<head>'
            '<meta charset="UTF-8">'
            '<link href="style.css" rel="stylesheet">'
            '<title>dupe-links</title>'
            '<body>'
            '<h1>Links to duplicates:</h1>')
    for row in data:
        cur.execute("""SELECT * FROM files where hash = ? and dupe = 1""", (row[4], ))
        ddata = cur.fetchall()
        if not ddata:
            pass
        else:
            link.write('<div class="record"><ul>')
            link.write('<span class="record_name">Duplicates for %s</span>' % row[1])
            for r in ddata:
                link.write('<li><a href="%s/%s">%s/%s</a></li>' % (str((r[3])), str(r[1]), str((r[3])), str(r[1])))
            link.write('</ul></div>')
    link.write('</body></html>')
    logloc = os.getcwd()
    print "View Duplicates: file://" + logloc + "/duplicates.html"
    link.close()


def mvdup(db):
    outdir = os.getcwd() + '/duplicates'
    con = sqlite3.connect(db)
    cur = con.cursor()
    cur.execute("""SELECT * FROM files WHERE dupe = 1  AND moved <> 1""")
    data = cur.fetchall()
    if not data:
        print "No files to move OR files have already been moved previously"
    else:
        print "Moving Duplicates.."
        for d in data:
            f = str(d[3] + '/' + d[1])
            i = d[0]
            dest = str(outdir + d[3])
            if not os.path.exists(dest):
                os.makedirs(dest)
            shutil.move(f, dest)
            cur.execute("""UPDATE files SET moved = 1 WHERE id = ?""", (i,))
            con.commit()
    con.close()


def move(p):
    """
    Moving duplicates
    """
    if p is 1:
        mvdup(database)
    else:
        pass


try:
    with open(database):
        print "found a database already named: ", database
        move(admvdup())
        iddup()
        duplog()
        duplink()
except IOError:
    print 'No database found. Will create database named: ', database
    sdir = setdir()
    proc = admvdup()
    print "sdir: ", sdir
    print "proc: ", proc
    index()
    iddup()
    duplog()
    duplink()
    move(proc)


print "DONE"

if con:
    con.close()
