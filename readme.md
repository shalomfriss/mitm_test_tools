This script uses mitm proxy to intercept the request and cache it.  It then will return the saved file
so that interactions can be replicated.  The files are saved in a directory named __files.  

To run: mitmdump -q -s intercept.py