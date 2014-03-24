#!/usr/bin/python

from axmlparserpy import axmlprinter
from xml.dom import minidom

def main():
  ap = axmlprinter.AXMLPrinter(open('example/binary/AndroidManifest.xml', 'rb').read())
  buff = minidom.parseString(ap.getBuff()).toxml()
  print(buff)

if __name__ == "__main__":
  main()
