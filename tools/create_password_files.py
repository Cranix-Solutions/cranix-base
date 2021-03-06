#!/usr/bin/python3
#
# Copyright (C) Peter Varkoly <pvarkoly@cephalix.eu> Nuremberg, Germany.  All rights reserved.
#

from xhtml2pdf import pisa             # import python module
import sys
import csv
import os
try:
    from html import escape  # python 3.x
except ImportError:
    from cgi import escape

def convertHtmlToPdf(sourceHtml, outputFilename):
    # open output file for writing (truncated binary)
    resultFile = open(outputFilename, "w+b")

    # convert HTML to PDF
    pisaStatus = pisa.CreatePDF(
            sourceHtml,                # the HTML to convert
            dest=resultFile)           # file handle to recieve result

    # close output file
    resultFile.close()                 # close output file

    # return True on success and False on errors
    return pisaStatus.err

import_dir= sys.argv[1] + "/"
role      = sys.argv[2]
user_list = '{0}/all-{1}.txt'.format(import_dir,role)
if not os.path.exists( import_dir + "/passwordfiles" ):
  os.mkdir( import_dir + "passwordfiles", 0o770 );

all_classes = []
with open(user_list) as csvfile:
    #Detect the type of the csv file
    dialect = csv.Sniffer().sniff(csvfile.readline())
    csvfile.seek(0)
    #Create an array of dicts from it
    csv.register_dialect('oss',dialect)
    reader = csv.DictReader(csvfile,dialect='oss')
    for row in reader:
        fobj = open("/usr/share/cranix/templates/password.html","r")
        template = fobj.read()
        fobj.close()
        uid=""
        group=""
        for field in reader.fieldnames:
            to_replace = '#'+field+'#'
            template = template.replace(to_replace,escape(row[field]))
            if field == "uid":
                uid=row[field]
            if  ( role == 'students' ) and ( field == "classes" ):
                group=row[field].split(' ')[0]
                if group not in all_classes:
                    all_classes.append(group)
        if role == 'students':
           convertHtmlToPdf(template, import_dir + "/passwordfiles/" + group + "-" + uid + '.pdf')
        else:
           convertHtmlToPdf(template, import_dir + "/passwordfiles/" + uid + '.pdf')

if role == 'students':
  for group in all_classes:
    os.system("/usr/bin/pdfunite " + import_dir + "passwordfiles/" + group + "-*.pdf " + import_dir + "/PASSWORDS-" + group + ".pdf")
else:
  os.system("/usr/bin/pdfunite " + import_dir + "passwordfiles/*.pdf " + import_dir + "/PASSWORDS-ALL-USER.pdf")
