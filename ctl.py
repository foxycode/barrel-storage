#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from optparse    import OptionParser

import hashlib
import struct
import zlib
import sys
import os
import re

# ------------------------------------------------------------------------------

DATAFILE = "storage.bin"
INDEXFILE = "storage.idx"
IDX_FORMAT = "<QLLL"
IDX_SIZE = 20

# ------------------------------------------------------------------------------

parser = OptionParser()
parser.add_option("-a", "--add-file", dest="add",
                  help="add file")
parser.add_option("-g", "--get-file", dest="get",
                  help="get file")
parser.add_option("-l", action="store_true", dest="list",
                  help="list files")
parser.add_option("-s", action="store_true", dest="stats",
                  help="file statistics")
parser.add_option("-r", action="store_true", dest="sort",
                  help="sort index")
parser.add_option("-t", action="store_true", dest="trunc",
                  help="truncate files")

(options, args) = parser.parse_args()

# ------------------------------------------------------------------------------

if options.stats:

    idx = None
    f = open(INDEXFILE, "rb")
    f.seek(0, os.SEEK_END)
    size = f.tell()
    f.close()

    print "Indexed files: %s" % (size/IDX_SIZE)

#endif

# ------------------------------------------------------------------------------

def qsort(list):
    """
    Quicksort using list comprehensions
    """
    if list == []:
        return []
    else:
        pivot = list[0][0]
        lesser = qsort([x for x in list[1:] if x[0] < pivot])
        greater = qsort([x for x in list[1:] if x[0] >= pivot])
        return lesser + [list[0]] + greater
    #endif
#enddef

if options.sort:

    table = []

    f = open(INDEXFILE, "rb")
    while True:
        l = f.read(IDX_SIZE)
        if not l:
            break
        idx = struct.unpack(IDX_FORMAT, l)

        table.append(idx)
    #endwhile
    f.close()

    table = qsort(table)

    f = open(INDEXFILE, "wb")
    for l in table:
        f.write(struct.pack(IDX_FORMAT, l[0], l[1], l[2], l[3]))
    #endfor
    f.close()

#endif

# ------------------------------------------------------------------------------

if options.trunc:

    f = open(INDEXFILE, "w")
    f.close()
    f = open(DATAFILE, "w")
    f.close()

#endif

# ------------------------------------------------------------------------------

if options.list:

    idx = None
    f = open(INDEXFILE, "rb")
    d = open(DATAFILE, "rb")
    while True:
        l = f.read(IDX_SIZE)
        if not l:
            break
        idx = struct.unpack(IDX_FORMAT, l)

        d.seek(idx[1])
        name = d.read(idx[2])

        print idx[0], name, "%skB" % str(idx[3]/1024)

    #endwhile
    f.close()

#endif

# ------------------------------------------------------------------------------

if options.add:

    if os.path.isfile(options.add):
        name = re.search(r".*/([^/]+)$", options.add).group(1)

        f = open(options.add, "rb")
        data = f.read()
        f.close()

        crc = zlib.adler32(data) & 0xffffffff

        idx = None
        f = open(INDEXFILE, "rb")
        while True:
            l = f.read(IDX_SIZE)
            if not l:
                break
            idx = struct.unpack(IDX_FORMAT, l)
            if idx[0] == crc:
                break
            else:
                idx = None
            #endif
        #endwhile
        f.close()

        if idx:
            sys.exit(0)
        #endif

        f = open(DATAFILE, "ab")
        pos = f.tell()
        #f.write("\x00")
        f.write(name)
        f.write(data)
        f.close()

        name_size = len(name)
        data_size = len(data)

        index = []
        f = open(INDEXFILE, "rb")
        while True:
            l = f.read(IDX_SIZE)
            if not l:
                break
            index.append(struct.unpack(IDX_FORMAT, l))
        #endwhile
        f.close()

        idx = (crc, pos, name_size, data_size)
        index.insert(0, idx)
        index = qsort(index)

        f = open(INDEXFILE, "wb")
        for l in index:
            f.write(struct.pack(IDX_FORMAT, l[0], l[1], l[2], l[3]))
        #endfor
        f.close()
        print "%s:%s" % (crc, name)

#endif

# ------------------------------------------------------------------------------

def binary_search(f, hodnota, vlevo, vpravo):
    stred = (vpravo + vlevo) / 2
    f.seek(stred*IDX_SIZE)
    idx = struct.unpack(IDX_FORMAT, f.read(IDX_SIZE))
    if idx[0] == hodnota:
        return idx
    #endif
    if hodnota < idx[0]:
        return binary_search(f, hodnota, vlevo, stred - 1)
    else:
        return binary_search(f, hodnota, stred + 1, vpravo)
    #endif
#enddef

if options.get:

    idx = None
    f = open(INDEXFILE, "rb")
    f.seek(0, os.SEEK_END)
    size = f.tell()/IDX_SIZE-1

    idx = binary_search(f, int(options.get), 0, size)

    if idx:
        f = open(DATAFILE, "rb")
        f.seek(idx[1])
        name = f.read(idx[2])
        data = f.read(idx[3])

        print name, "%skB" % str(len(data)/1024)
    #endif

#endif
