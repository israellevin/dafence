dafence
=======

A simple game of conquest.

Hardly anything here ATM, but you can run server.py, which will run a local server on port 8000, and then open a browser at http://0.0.0.0:8000 to see the board. Add '?pos=level,top,bottom,right,left' as a query string to navigate anywhere. Note how slow it is when you view a big range.

Click a cell to own it (currently as root, the only user). If there is another owned cell near by on the same row or column, you will also own all the cells between them - recursively.
