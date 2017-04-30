# LexisNexis Information Extractor

A information extraction script that takes a downloaded plain text file from LexisNexis
and converts it into a proper CSV file. Wildcards such as *.txt may be used
as script argument to process multiple files at once.

This script was originally inspired by Neal Caren:
http://nealcaren.web.unc.edu/cleaning-up-lexisnexis-files/

Example use case:
python split_ln.py t*.txt

Processing the following file:
 test.txt

Meta tags that are actually considered for this file:
 ID_DOC
 PUBLICATION
 DATE
 TITLE
 URL
 PHOTO
 LENGTH

Wrote the following file with 187 items:
 test.csv 
