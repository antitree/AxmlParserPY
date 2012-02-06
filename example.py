#!/usr/bin/python

import axmlprinter
from xml.dom import minidom

def main():
  ap = axmlprinter.AXMLPrinter(open('../manitree/examples/xml/AndroidManifest.xml', 'rb').read())
  buff = minidom.parseString(ap.getBuff()).toxml()
  print(buff)

if __name__ == "__main__":
  print("Starting")
  main()
