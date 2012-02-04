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


class AXMLPrinter :
    def __init__(self, raw_buff) :
        self.axml = AXMLParser( raw_buff )
        self.xmlns = False

        self.buff = ""

        while 1 :
            _type = self.axml.next()
#           print "tagtype = ", _type

            if _type == START_DOCUMENT :
                self.buff += "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
            elif _type == START_TAG :
                self.buff += "<%s%s\n" % ( self.getPrefix( self.axml.getPrefix() ), self.axml.getName() )

                # FIXME : use namespace
                if self.xmlns == False :
                    self.buff += "xmlns:%s=\"%s\"\n" % ( self.axml.getNamespacePrefix( 0 ), self.axml.getNamespaceUri( 0 ) )
                    self.xmlns = True

                for i in range(0, self.axml.getAttributeCount()) :
                    self.buff += "%s%s=\"%s\"\n" % ( self.getPrefix( self.axml.getAttributePrefix(i) ), self.axml.getAttributeName(i), self.getAttributeValue( i ) )

                self.buff += ">\n"

            elif _type == END_TAG :
                self.buff += "</%s%s>\n" % ( self.getPrefix( self.axml.getPrefix() ), self.axml.getName() )

            elif _type == TEXT :
                self.buff += "%s\n" % self.axml.getText()

            elif _type == END_DOCUMENT :
                break

    def getBuff(self) :
        return self.buff.encode("utf-8")

    def getPrefix(self, prefix) :
        if prefix == None or len(prefix) == 0 :
            return ""

        return prefix + ":"

    def getAttributeValue(self, index) :
        _type = self.axml.getAttributeValueType(index)
        _data = self.axml.getAttributeValueData(index)

        #print _type, _data
        if _type == TYPE_STRING :
            return self.axml.getAttributeValue( index )

        elif _type == TYPE_ATTRIBUTE :
            return "?%s%08X" % (self.getPackage(_data), _data)

        elif _type == TYPE_REFERENCE :
            return "@%s%08X" % (self.getPackage(_data), _data)

        # WIP
        elif _type == TYPE_FLOAT :
            return "%f" % unpack("=f", pack("=L", _data))[0] 

        elif _type == TYPE_INT_HEX :
            return "0x%08X" % _data

        elif _type == TYPE_INT_BOOLEAN :
            if _data == 0 :
                return "false"
            return "true"

        elif _type == TYPE_DIMENSION :
            return "%f%s" % (self.complexToFloat(_data), DIMENSION_UNITS[_data & COMPLEX_UNIT_MASK])

        elif _type == TYPE_FRACTION :
            return "%f%s" % (self.complexToFloat(_data), FRACTION_UNITS[_data & COMPLEX_UNIT_MASK])

        elif _type >= TYPE_FIRST_COLOR_INT and _type <= TYPE_LAST_COLOR_INT :
            return "#%08X" % _data

        elif _type >= TYPE_FIRST_INT and _type <= TYPE_LAST_INT :
            return "%d" % androconf.long2int( _data )

        return "<0x%X, type 0x%02X>" % (_data, _type)

    def complexToFloat(self, xcomplex) :
        return (float)(xcomplex & 0xFFFFFF00)*RADIX_MULTS[(xcomplex>>4) & 3];

    def getPackage(self, id) :
        if id >> 24 == 1 :
            return "android:"
        return ""

