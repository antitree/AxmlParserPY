# This file is part of Androguard.
#
# Copyright (C) 2010, Anthony Desnos <desnos at t0t0.fr>
# All rights reserved.
#
# Androguard is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Androguard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Androguard.  If not, see <http://www.gnu.org/licenses/>.

import bytecode

import androconf
from bytecode import SV

import zipfile, StringIO
from struct import pack, unpack
from xml.dom import minidom

try :
    import chilkat
    ZIPMODULE = 0
    # UNLOCK : change it with your valid key !
    try : 
        CHILKAT_KEY = open("key.txt", "rb").read()
    except Exception :
        CHILKAT_KEY = "testme"

except ImportError :
    ZIPMODULE = 1

################################################### CHILKAT ZIP FORMAT #####################################################
class ChilkatZip :
    def __init__(self, raw) :
        self.files = []
        self.zip = chilkat.CkZip()

        self.zip.UnlockComponent( CHILKAT_KEY )

        self.zip.OpenFromMemory( raw, len(raw) )
        
        filename = chilkat.CkString()
        e = self.zip.FirstEntry()
        while e != None :
            e.get_FileName(filename)
            self.files.append( filename.getString() )
            e = e.NextEntry()

    def namelist(self) :
        return self.files

    def read(self, elem) :
        e = self.zip.GetEntryByName( elem )
        s = chilkat.CkByteData()
        
        e.Inflate( s )
        return s.getBytes()

