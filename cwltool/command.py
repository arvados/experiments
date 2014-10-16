#!/usr/bin/env python

import execjs
import json

# todo: look into sandboxing, https://github.com/gf3/sandbox

# http://rightfootin.blogspot.com/2006/09/more-on-python-flatten.html
def flatten(l, ltypes=(list, tuple)):
    ltype = type(l)
    l = list(l)
    i = 0
    while i < len(l):
        while isinstance(l[i], ltypes):
            if not l[i]:
                l.pop(i)
                i -= 1
                break
            else:
                l[i:i + 1] = l[i]
        i += 1
    return ltype(l)

def js_expr(job, command):
    def cmd(c):
        if c.startswith('={'):
            return "(function() %s )()" % c[1:]
        elif c.startswith('='):
            return "(%s)" % c[1:]
        else:
            return "'%s'" % c

    js = "(function() { var job = %s; return [%s]; })()" % (
        json.dumps(job), 
        ", ".join([cmd(c) for c in command]))

    return flatten(execjs.eval(js))

def cs_expr(job, command):
    import coffeescript 

    def cmd(c):
        if c.startswith('='):
            return "(%s)" % c[1:]
        else:
            return "'%s'" % c

    def coffeeval(src):
        return execjs.eval(coffeescript.compile("return (" + src + ")")[:-2]) 

    cs = "(() -> job = %s; [%s])()" % (
        json.dumps(job), 
        ", ".join([cmd(c) for c in command]))

    return flatten(coffeeval(cs))
