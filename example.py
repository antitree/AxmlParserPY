#!/usr/bin/python

import apk
from xml.dom import minidom

def main():
  ap = apk.AXMLPrinter(open('test.xml', 'rb').read())
  buff = minidom.parseString(ap.getBuff()).toprettyxml()
  print(buff)

if __name__ == "__main__":
  print("Starting")
  main()
