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


class AXMLParser :
    def __init__(self, raw_buff) :
        self.reset()

        self.buff = bytecode.BuffHandle( raw_buff )

        self.buff.read(4)
        self.buff.read(4)

        self.sb = StringBlock( self.buff )

        self.m_resourceIDs = []
        self.m_prefixuri = {}
        self.m_uriprefix = {}
        self.m_prefixuriL = []

    def reset(self) :
        self.m_event = -1
        self.m_lineNumber = -1
        self.m_name = -1
        self.m_namespaceUri = -1
        self.m_attributes = []
        self.m_idAttribute = -1
        self.m_classAttribute = -1
        self.m_styleAttribute = -1

    def next(self) :
        self.doNext()
        return self.m_event

    def doNext(self) :
        if self.m_event == END_DOCUMENT :
            return

        event = self.m_event

        self.reset()
        while 1 :
            chunkType = -1

            # Fake END_DOCUMENT event.
            if event == END_TAG :
                pass

            # START_DOCUMENT
            if event == START_DOCUMENT :
                chunkType = CHUNK_XML_START_TAG
            else :
                if self.buff.end() == True :
                    self.m_event = END_DOCUMENT
                    break
                chunkType = SV( '<L', self.buff.read( 4 ) ).get_value()


            if chunkType == CHUNK_RESOURCEIDS :
                chunkSize = SV( '<L', self.buff.read( 4 ) ).get_value()
                # FIXME
                if chunkSize < 8 or chunkSize%4 != 0 :
                    raise("ooo")

                for i in range(0, chunkSize/4-2) :
                    self.m_resourceIDs.append( SV( '<L', self.buff.read( 4 ) ) )

                continue

            # FIXME
            if chunkType < CHUNK_XML_FIRST or chunkType > CHUNK_XML_LAST :
                raise("ooo")

            # Fake START_DOCUMENT event.
            if chunkType == CHUNK_XML_START_TAG and event == -1 :
                self.m_event = START_DOCUMENT
                break

            self.buff.read( 4 ) #/*chunkSize*/
            lineNumber = SV( '<L', self.buff.read( 4 ) ).get_value()
            self.buff.read( 4 ) #0xFFFFFFFF

            if chunkType == CHUNK_XML_START_NAMESPACE or chunkType == CHUNK_XML_END_NAMESPACE :
                if chunkType == CHUNK_XML_START_NAMESPACE :
                    prefix = SV( '<L', self.buff.read( 4 ) ).get_value()
                    uri = SV( '<L', self.buff.read( 4 ) ).get_value()

                    self.m_prefixuri[ prefix ] = uri
                    self.m_uriprefix[ uri ] = prefix
                    self.m_prefixuriL.append( (prefix, uri) )
                else :
                    self.buff.read( 4 )
                    self.buff.read( 4 )
                    (prefix, uri) = self.m_prefixuriL.pop()
                    #del self.m_prefixuri[ prefix ]
                    #del self.m_uriprefix[ uri ]

                continue


            self.m_lineNumber = lineNumber

            if chunkType == CHUNK_XML_START_TAG :
                self.m_namespaceUri = SV( '<L', self.buff.read( 4 ) ).get_value()
                self.m_name = SV( '<L', self.buff.read( 4 ) ).get_value()

                # FIXME
                self.buff.read( 4 ) #flags
                
                attributeCount = SV( '<L', self.buff.read( 4 ) ).get_value()
                self.m_idAttribute = (attributeCount>>16) - 1
                attributeCount = attributeCount & 0xFFFF
                self.m_classAttribute = SV( '<L', self.buff.read( 4 ) ).get_value()
                self.m_styleAttribute = (self.m_classAttribute>>16) - 1

                self.m_classAttribute = (self.m_classAttribute & 0xFFFF) - 1

                for i in range(0, attributeCount*ATTRIBUTE_LENGHT) :
                    self.m_attributes.append( SV( '<L', self.buff.read( 4 ) ).get_value() )

                for i in range(ATTRIBUTE_IX_VALUE_TYPE, len(self.m_attributes), ATTRIBUTE_LENGHT) :
                    self.m_attributes[i] = (self.m_attributes[i]>>24)

                self.m_event = START_TAG
                break

            if chunkType == CHUNK_XML_END_TAG :
                self.m_namespaceUri = SV( '<L', self.buff.read( 4 ) ).get_value()
                self.m_name = SV( '<L', self.buff.read( 4 ) ).get_value()
                self.m_event = END_TAG
                break

            if chunkType == CHUNK_XML_TEXT :
                self.m_name = SV( '<L', self.buff.read( 4 ) ).get_value()
                
                # FIXME
                self.buff.read( 4 ) #?
                self.buff.read( 4 ) #?

                self.m_event = TEXT
                break

    def getPrefixByUri(self, uri) :
        try :
            return self.m_uriprefix[ uri ]
        except KeyError :
            return -1

    def getPrefix(self) :
        try :
            return self.sb.getRaw(self.m_prefixuri[ self.m_namespaceUri ])
        except KeyError :
            return ""

    def getName(self) :
        if self.m_name == -1 or (self.m_event != START_TAG and self.m_event != END_TAG) :
            return ""

        return self.sb.getRaw(self.m_name)

    def getText(self) :
        if self.m_name == -1 or self.m_event != TEXT :
            return ""

        return self.sb.getRaw(self.m_name)

    def getNamespacePrefix(self, pos) :
        prefix = self.m_prefixuriL[ pos ][0]
        return self.sb.getRaw( prefix )

    def getNamespaceUri(self, pos) :
        uri = self.m_prefixuriL[ pos ][1]
        return self.sb.getRaw( uri )

    def getNamespaceCount(self, pos) :
        pass

    def getAttributeOffset(self, index) :
        # FIXME
        if self.m_event != START_TAG :
            raise("Current event is not START_TAG.")

        offset = index * 5
        # FIXME
        if offset >= len(self.m_attributes) :
            raise("Invalid attribute index")

        return offset

    def getAttributeCount(self) :
        if self.m_event != START_TAG :
            return -1

        return len(self.m_attributes) / ATTRIBUTE_LENGHT

    def getAttributePrefix(self, index) :
        offset = self.getAttributeOffset(index)
        uri = self.m_attributes[offset+ATTRIBUTE_IX_NAMESPACE_URI]

        prefix = self.getPrefixByUri( uri )
        if prefix == -1 :
            return ""

        return self.sb.getRaw( prefix )

    def getAttributeName(self, index) :
        offset = self.getAttributeOffset(index)
        name = self.m_attributes[offset+ATTRIBUTE_IX_NAME]

        if name == -1 :
            return ""

        return self.sb.getRaw( name )

    def getAttributeValueType(self, index) :
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset+ATTRIBUTE_IX_VALUE_TYPE]

    def getAttributeValueData(self, index) :
        offset = self.getAttributeOffset(index)
        return self.m_attributes[offset+ATTRIBUTE_IX_VALUE_DATA]

    def getAttributeValue(self, index) :
        offset = self.getAttributeOffset(index)
        valueType = self.m_attributes[offset+ATTRIBUTE_IX_VALUE_TYPE]
        if valueType == TYPE_STRING :
            valueString = self.m_attributes[offset+ATTRIBUTE_IX_VALUE_STRING]
            return self.sb.getRaw( valueString )
        # WIP
        return ""
        #int valueData=m_attributes[offset+ATTRIBUTE_IX_VALUE_DATA];
        #return TypedValue.coerceToString(valueType,valueData);

TYPE_ATTRIBUTE          = 2
TYPE_DIMENSION          = 5
TYPE_FIRST_COLOR_INT    = 28
TYPE_FIRST_INT          = 16
TYPE_FLOAT              = 4
TYPE_FRACTION           = 6
TYPE_INT_BOOLEAN        = 18
TYPE_INT_COLOR_ARGB4    = 30
TYPE_INT_COLOR_ARGB8    = 28
TYPE_INT_COLOR_RGB4     = 31
TYPE_INT_COLOR_RGB8     = 29
TYPE_INT_DEC            = 16
TYPE_INT_HEX            = 17
TYPE_LAST_COLOR_INT     = 31
TYPE_LAST_INT           = 31
TYPE_NULL               = 0
TYPE_REFERENCE          = 1
TYPE_STRING             = 3

RADIX_MULTS             =   [ 0.00390625, 3.051758E-005, 1.192093E-007, 4.656613E-010 ]
DIMENSION_UNITS         =   [ "px","dip","sp","pt","in","mm","","" ]
FRACTION_UNITS          =   [ "%","%p","","","","","","" ]

COMPLEX_UNIT_MASK        =   15

