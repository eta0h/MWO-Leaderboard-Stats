# MWO-Stats

Pulling MWO leaderbored stats through the web interface is cumbersome. Especially when one wants to look at specific stats for many different pilots, or just a quick glance to see how a given pilot ranks. To make this task easier I wrote this command line script in Python which it turned out to be be pretty useful. So I figured maybe others in the MWO Community might find it useful too.

The script DOES NOT send your username / password anywhere. The script does need to authenticate to http://mwomercs.com to fetch the stats. If your uncomfortable, just create / use an alternate account.  

How to use it:

1 - Python Installation

    Download Python 2.7 - https://www.python.org/ftp/python/2.7.12/python-2.7.12.msi
    Install to C:\Python27\ the defaults are fine, but be sure to also check  "Add python.exe to Path"
    Reboot Windows
 
 
2 - Install Python Dependancies

    Open an admin cmd prompt and type the following:
    pip install mechanize
    pip install bs4

3 - Download the script lbstats.py and copy it somewhere, like c:\users\UserName

4 - edit the lbstats.py

    At the top fill in your MWO email and password. (Only used to authenticate with mwomercs.com )
    If you want, fill in the pilot list to get stats from multiple pilots


5 - Use the script

    Open a cmd prompt, and change directories to where you copied the script
    Eg. cd c:\Users\UserName
    test it - "lbstats.py -h"

Suggestions, contributions are welcome. This is essentially the first such project I've done so please be kind. 

Regards,
eta0h
