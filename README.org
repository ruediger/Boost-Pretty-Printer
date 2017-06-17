# -*- mode:org; mode:visual-line; coding:utf-8; -*-
** [[http://sourceware.org/gdb/][GDB]] Pretty Printers for [[http://boost.org][Boost]]
Since version 7.0, GDB has Python scripting support. This can be used to provide "pretty printers" to make the output of GDB more usable. The libstdc++ project currently provides a set of pretty printers for their implementation of the C++ standard library. This projects goal is to provide a similar set of pretty printers for the Boost library.

Help is appreciated!

See [[SUPPORTED.org]] for supported classes and names of contributors. See [[NOTES.org]] for other general notes. See [[HACKING.org]] for more low-level information about printers in general.

The pretty printers are licensed under the terms of the [[http://www.boost.org/users/license.html][Boost Software License, version 1.0]].

*** Installation
GDB version 7 or better is required. Currently, most printers work with either Python 2 or Python 3.

To install, check out the git repository:
#+BEGIN_EXAMPLE
git clone git://github.com/ruediger/Boost-Pretty-Printer.git
#+END_EXAMPLE

Then, add the following lines to your =~/.gdbinit=:
#+BEGIN_EXAMPLE
python
import sys
sys.path.insert(1, 'PATH-TO-THE-REPO/Boost-Pretty-Printer')
import boost
boost.register_printers(boost_version=(x,y,z))
end
#+END_EXAMPLE

If you have no =~/.gdbinit= file just create it. And of course, replace =PATH-TO-THE-REPO= with the absolute path to the Boost Pretty Printer repository. =boost_version= is a tuple with boost version which you use. =boost_version= may be omitted. In that case boost version will be detected automatically. Note, that autodetect routine makes gdb startup somewhat slower.

Now you can simply use GDB's =print= (short =p=) statement to pretty print the supported boost objects.
*** Example
#+BEGIN_EXAMPLE
  $ cat > foo.c++
  #include <boost/range/iterator_range.hpp>
  using namespace boost;

  int main() {
    char buf[] = "Hello World";
    iterator_range<char const*> range(buf, buf + sizeof(buf));

    return range[0];
  }
  ^D
  $ g++ -g3 foo.c++
  $ gdb -q a.out
  Reading symbols from /home/ruediger/develop/demos/a.out...done.
  (gdb) break 7
  Breakpoint 1 at 0x4006cb: file /home/ruediger/develop/demos/foo.c++, line 7.
  (gdb) run
  Starting program: /home/ruediger/develop/demos/a.out

  Breakpoint 1, main () at /home/ruediger/develop/demos/foo.c++:8
  8         return range[0];
  (gdb) p range
  $1 = boost::iterator_range<char const*> of length 12 = {72 'H', 101 'e', 108 'l', 108 'l', 111 'o', 32 ' ', 87 'W', 111 'o', 114 'r', 108 'l', 100 'd', 0 '\000'}
#+END_EXAMPLE

*** Volatililty Of Printers
Due to the limited nature of the debugging interface, individual printers included in this package can stop working with every Boost update. Specifically, a printer for =boost::intrusive::list= designed for Boost version 1.40 might or might not work with Boost 1.46. The reasons for this are explained in [[HACKING.org]]. Keeping the printers up to date is a daunting task, and contributions are welcome in that sense. If you need to debug some data structures and you find that there is no printer for them, or that the included printer stopped working, consider investing some time in fixing them and creating a pull request. Various information about this process is provided in [[HACKING.org]].

*** Managing Printers From Inside GDB
This python module installs a single top-level printer called =boost=, and individual subprinters for the various supported types. Here are some useful commands to manage printers from inside gdb:
#+BEGIN_EXAMPLE
# show list of loaded boost printers (also shows which, if any, are disabled)
info pretty-printer global boost
# disable some printers
disable pretty-printer global boost;boost::intrusive::list
# re-enable all boost printers
enable pretty-printer global boost;.*
#+END_EXAMPLE

For more information, see the [[https://sourceware.org/gdb/onlinedocs/gdb/Pretty-Printing.html][GDB documentation]].
