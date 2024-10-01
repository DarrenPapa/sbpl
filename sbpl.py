#!/usr/bin/env python3
import os, sys, pickle, time, atexit

LOCDIR = os.path.dirname(sys.argv[0])
LIBDIR = os.path.join(LOCDIR, "lib")
VERSION = "0.1"
TIME_ELAPSED = lambda: print(f"\nTime Elapsed (s): {time.time()-START:,.8f}\n")

if not os.path.isdir(LIBDIR):
    os.mkdir(LIBDIR)
    print("[INFO]: Created directory `lib`")

stack = []
includes = set()

chars = {
    "\\\\":"\\[escape]",
    "\\n":"\n",
    "\\t":"\t",
    "\\s":"\s",
    "\\v":"\v",
    "\\f":"\f",
    "\\r":"\r",
    "\\[win_nl]":"\r\n",
    "\\[unix_nl]":"\n",
    "\\[null]":"\0",
    "\\[escape]":"\\"
}

def expr(arg):
    arg = arg.strip()
    if arg == "top":
        return stack.pop() if stack else 0
    elif arg == "top:peek":
        return stack[-1] if stack else 0
    elif arg == "bottom":
        return stack.pop(0) if stack else 0
    elif arg == "bottom:peek":
        return stack[0] if stack else 0
    elif arg.endswith("i"):
        return int(arg[:-1])
    elif arg.endswith("f"):
        return float(arg[:-1])
    elif arg == "true":
        return 1
    elif arg == "false":
        return 0
    elif arg.isalnum():
        return arg
    return 0

def exprs(args):
    if args and args[0] == "string:" and args[-1].endswith(":end"):
        text = " ".join(args[1:])[:-4]
        for c, r in chars.items():
            text = text.replace(c, r)
        return text,
    elif "verbose" in flags and args and args[0] == "string:":
        print("Warning: String doesnt have an ':end' marker!")
    elif "verbose" in flags and args and args[0].startswith("string:"):
        text = args[0].split(":", maxsplit=1)[1]
        t2 = " ".join(args[1:])
        if t2:
            text += " "+t2
        print(f"Warning: Did you mean 'string: {text}'")
    return *map(expr, args),

def process(code, name="__main__"):
    res = []
    oname = name
    c = enumerate(code.split("\n"), 1)
    if "verbose" in flags:
        print(f"Processing {name!r}")
    for lp, line in c:
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        elif line.startswith("#"):
            line = line[1:].strip()
            if line.startswith("#!"):
                pass
            elif line:
                ins, arg = line.split(maxsplit=1) if " " in line else (line, None)
                if ins == "include" and arg is not None:
                    if arg.startswith('<') and arg.endswith('>'):
                        arg = os.path.join(LIBDIR, arg[1:-1])
                    elif arg.startswith('"') and arg.endswith('"'):
                        arg = arg[1:-1]
                    if not os.path.isfile(arg):
                        print(f"\nError on line {lp} in file `{name}`\nFile {arg!r} does not exist.")
                        break
                    if arg not in includes:
                        includes.add(name)
                    else:
                        continue
                    res.extend(process(open(arg).read(), arg))
                elif ins == "chname" and arg is not None:
                    if name != "__main__":
                        name = arg
                elif ins == "force.chname" and arg is not None:
                    name = arg
                elif ins == "doNotShowTime" and arg is None:
                    atexit.unregister(TIME_ELAPSED)
                else:
                    print(f"\nError on line {lp} in file `{name}`\nInvalid directory: {ins}")
                    exit(1)
            else:
                print(f"\nError on line {lp} in file `{name}`\nInvalid directory: {ins}")
                exit(1)
        else:
            ins, *args = line.split()
            args = *args,
            res.append((lp, name, ins, args))
    else:
        if "verbose" in flags:
            if oname == name:
                print(f"Finished processing {name!r}")
            else:
                print(f"Finished processing {oname!r} -> new context {name!r}")
        return tuple(res)
    exit(1)

def minimize(lst):
    lst = list(lst)
    if len(lst) == 0:
        return []
    k = [[lst[0], 1]]
    if len(lst) == 1:
        return lst
    for i in lst[1:]:
        if i == k[-1][0]:
            k[-1][1] += 1
        else:
            k.append([i, 1])
    return [f'[{item}] * {count}' if count > 1 else item for item, count in k]

def reprocess(code, name):
    return *[(pos, name if file == "__main__" else f"{name}-{file}", ins, args) for pos, file, ins, args in code],

def sources(code):
    src = set()
    for _, name, _, _ in code:
        src.add(name)
    return *src,

def run(code, repl=False, funcs=None):
    if isinstance(code, str):
        if "verbose" in flags:
            START = time.time()
        code = process(code)
        if "verbose" in flags:
            DELTA = time.time() - START
            print(f"Took {DELTA:,.8f} seconds\n")
    funcs = funcs if funcs is not None else {}
    p = 0
    while p < len(code):
        pos, file, ins, args = code[p]
        args = *exprs(args),
        argc = len(args)
        # stack
        if ins == "push" and argc == 1:
            stack.append(args[0])
        elif ins == "pop" and argc == 0:
            if stack:
                stack.pop()
        elif ins == "dupe" and argc == 0:
            if stack:
                stack.append(stack[-1])
            else:
                stack.append(0)
        elif ins == "clear" and argc == 0:
            stack.clear()
        elif ins == "rot" and argc == 0:
            if len(stack) < 2:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt rotate stack items!")
                break
            b, a = stack.pop(), stack.pop()
            stack.extend([b, a])
        elif ins == "show_stack" and argc == 0:
            print(f"[{'' if not stack else ' '+(','+chr(10)+'  ').join(minimize(map(repr, stack)))+' '}]")
        # math
        elif ins == "add" and argc == 2:
            stack.append(args[1]+args[0])
        elif ins == "sub" and argc == 2:
            stack.append(args[1]-args[0])
        elif ins == "mul" and argc == 2:
            stack.append(args[1]*args[0])
        elif ins == "div" and argc == 2:
            stack.append(args[1]/args[0])
        # functions
        elif ins == "fn" and argc == 1:
            temp = []
            name = args[0]
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endf":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction not closed!")
                break
            if file != "__main__":
                name = f"{os.path.basename(file).split('.')[0]}.{name}"
            if name in funcs:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction already defined in file {funcs[name][0]!r}")
                break
            funcs[name] = file, temp
        elif ins == "rfn" and argc == 1:
            temp = []
            name = args[0]
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endf":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction not closed!")
                break
            if name in funcs:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction already defined in file {funcs[name][0]!r}")
                break
            funcs[name] = file, temp
        elif ins == "define" and argc == 2:
            t, name = args
            if t == "static":
                funcs[name] = (file, tuple())
            elif t == "dynamic":
                if file != "__main__":
                    name = f"{os.path.basename(file).split('.')[0]}.{name}"
                funcs[name] = (file, tuple())
            else:
                print(f"\nError on line {pos} in file `{file}`\nFunction type {t!r} unknown!")
        elif ins == "ifmain" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endf":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file != "__main__":
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function raised an error!")
                break
        elif ins == "ifsetup" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endf":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file != "__setup__":
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function raised an error!")
                break
        elif ins == "notmain" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endf":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file == "__main__":
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function raised an error!")
                break
        elif ins == "call" and argc == 1:
            name = args[0]
            if name not in funcs:
                print(f"\nError on line {pos} in file `{file}`\nInvalid function: {name}")
                break
            if run(funcs[name][1], funcs=funcs):
                print(f"\nError on line {pos} in file `{file}`\nFunction {name!r} raised an error!")
                break
        elif ins == "dyncall" and argc == 1:
            name = args[0]
            if file != "__main__":
                name = f"{os.path.basename(file).split('.')[0]}.{name}"
            if name not in funcs:
                print(f"\nError on line {pos} in file `{file}`\nInvalid function: {name}")
                break
            if run(funcs[name][1], funcs=funcs):
                print(f"\nError on line {pos} in file `{file}`\nFunction {name!r} raised an error!")
                break
        # if statements
        elif ins == "ifeq" and argc == 2:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endif":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if args[0] != args[1]:
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{file}`\nIf function raised an error!")
                break
        elif ins == "ifne" and argc == 2:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endif":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if args[0] == args[1]:
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{file}`\nIf function raised an error!")
                break
        elif ins == "ifgt" and argc == 2:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endif":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if args[0] < args[1]:
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{file}`\nIf function raised an error!")
                break
        elif ins == "iflt" and argc == 2:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endif":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if args[0] > args[1]:
                p += 1
                continue
            if run(temp, funcs=funcs):
                print(f"\nError on line {opos} in file `{file}`\nIf function raised an error!")
                break
        # loops
        elif ins == "irange" and argc == 1:
            stack.append(tuple(range(args[0]+1)))
        elif ins == "range" and argc == 1:
            stack.append(tuple(range(args[0])))
        elif ins == "irange" and argc == 2:
            stack.append(tuple(range(args[0], args[1]+1)))
        elif ins == "range" and argc == 2:
            stack.append(tuple(range(args[0], args[1])))
        elif ins == "foreach" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endfor":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            v = stack[-1]
            for i in v:
                stack.append(i)
                if run(temp, funcs=funcs):
                    print(f"\nError on line {opos} in file `{file}`\nFor function raised an error!")
                    break
            else:
                p += 1
                continue
            break
        elif ins == "for" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endfor":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            for i in tuple(range(oargs[0])):
                stack.append(i)
                if run(temp, funcs=funcs):
                    print(f"\nError on line {opos} in file `{file}`\nFor function raised an error!")
                    break
            else:
                p += 1
                continue
            break
        elif ins == "ufor" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endfor":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            for i in tuple(range(oargs[0])):
                if run(temp, funcs=funcs):
                    print(f"\nError on line {opos} in file `{file}`\nFor function raised an error!")
                    break
            else:
                p += 1
                continue
            break
        elif ins == "loop" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins == "endloop":
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            while True:
                if run(temp, funcs=funcs):
                    print(f"\nError on line {pos} in file `{file}`\nFor function raised an error!")
                    break
            else:
                p += 1
                continue
            break
        # libs
        elif ins == "cache" and argc == 1:
            name = args[0]
            with open(name, "wb") as f:
                f.write(pickle.dumps({fname:reprocess(code, name) for fname, code in funcs.items()}))
        elif ins == "load" and (argc == 1 or argc == 2):
            with open(args[0], "rb") as f:
                fs = pickle.loads(f.read())
                if argc == 2:
                    fs = {f"{args[1]}.{name}":code for name, code in fs.items()}
                if repl:
                    mlen = max(map(len, fs.keys()))
                    print(f"Loaded functions:")
                    print(f"  {'Name'.rjust(mlen)} -> Dependencies\n")
                    for name, code in fs.items():
                        print(f"  {name.rjust(mlen)} -> {', '.join(sources(code))}")
                funcs.update(fs)
        elif ins == "dynload" and (argc == 1 or argc == 2):
            with open(args[0], "r") as f:
                name = "__main__" if argc == 1 else args[1]
                x = process(f.read(), name)
                fs = {}
                if run(x, funcs=fs):
                    print(f"\nError on line {pos} in file `{file}`\nFunction {name!r} raised an error!")
                    break
                if repl:
                    print(f"Loaded {args[0]!r}")
                    mlen = max(map(len, fs.keys()))
                    print(f"Loaded functions:")
                    print(f"  {'Name'.rjust(mlen)} -> Dependencies\n")
                    for name, code in fs.items():
                        print(f"  {name.rjust(mlen)} -> {', '.join(sources(code))}")
                funcs.update(fs)
        elif ins == "setup" and argc == 0:
            with open(args[0], "r") as f:
                name = "__setup__"
                x = process(f.read(), name)
                fs = {}
                if run(x, funcs=fs):
                    print(f"\nError on line {pos} in file `{file}`\nFunction {name!r} raised an error!")
                    break
                if repl:
                    print(f"Loaded {args[0]!r}")
                    mlen = max(map(len, fs.keys()))
                    print(f"Loaded functions:")
                    print(f"  {'Name'.rjust(mlen)} -> Dependencies\n")
                    for name, code in fs.items():
                        print(f"  {name.rjust(mlen)} -> {', '.join(sources(code))}")
                funcs.update(fs)
        # system
        elif ins == "system" and argc == 1:
            stack.append(os.system(args[0]))
        # io
        elif ins == "print":
            print(*args, end='')
        elif ins == "println":
            print(*args)
        elif ins == "input" and argc == 0:
            stack.append(input())
        # type casting
        elif ins == "toint" and argc == 1:
            try:
                stack.appent(int(args[0]))
            except:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt convert {args[0]!r} to int!")
                break
        elif ins == "tofloat" and argc == 1:
            try:
                stack.appent(float(args[0]))
            except:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt convert {args[0]!r} to int!")
                break
        elif ins == "tostring" and argc == 1:
            stack.appent(str(args[0]))
        # errors
        elif ins == "panic" and argc == 0:
            print(f"\nError on line {pos} in file `{file}`\nPanic!")
            break
        else:
            print(f"\nError on line {pos} in file `{file}`\nInvalid instruction: {ins}\nArguments: {' '.join(map(repr, args))}")
            break
        p += 1
    else:
        return 0
    return 1

known_flags = {
    "setup", "verbose", "version", "ver", "main-entry"
}
flags = set()
for pos, val in enumerate(sys.argv[1:]):
    if val.startswith("--"):
        flags.add(val[2:])
    else:
        break
if flags:
    sys.argv = [sys.argv[0], *sys.argv[pos+1:]]
    if flags - known_flags:
        print("Unknown flags:", ", ".join(flags - known_flags))
if "verbose" in flags:
    print("Flags:", flags)
    print(f"Interpreter: {os.path.abspath(sys.argv[0])}")
    if len(sys.argv) >= 2:
        print(f"File: {os.path.abspath(sys.argv[1])}")
if "version" in flags or "ver" in flags:
    print("Version:", VERSION)
program_arguments = sys.argv[1:]
argc = len(sys.argv)
stack.extend(exprs(program_arguments))
if argc >= 2:
    ff = {}
    with open(sys.argv[1]) as f:
        code = f.read()
        if "setup" in flags:
            code = process(code, name="__setup__")
        atexit.register(TIME_ELAPSED)
        START = time.time()
        if run(code, funcs=ff):
            print("\nFinished with an error!")
            exit(3)
        else:
            if "main-entry" in flags:
                if "verbose" in flags:
                    print("Automatically calling main...\n")
                    flags.remove("verbose")
                if "main" not in ff:
                    print("\nMain function does not exist!")
                    exit(3)
                if run("call main", funcs=ff):
                    print("\nMain Entry: Finished with an error!")
                    exit(3)
else:
    print(f"REPL - SBPL 0.1")
    f = {}
    ml = {
        "rfn", "fn",
        "ifmain", "ifsetup", "notmain",
        "ifeq", "ifne", "iflt", "ifgt",
        "loop", "for", "ufor", "foreach",
        ";multi"
    }
    while True:
        act = input(f"[{'' if not stack else ' '+(','+chr(10)+'  ').join(minimize(map(repr, stack)))+' '}]\n>>> ")
        if act.split(maxsplit=1)[0] in ml:
            t = [act]
            while True:
                act = input("... ")
                if act == ".done":
                    break
                t.append(act)
            act = "\n".join(t)
        if act == "exit":
            break
        elif act == ".editor":
            act = []
            print("Basic REPL In-memory Editor.\nEnter '.exit' to stop.\nEnter '.run' to execute code.\n'.help' for more.")
            while True:
                a = input(f"+++ ")
                if a == ".exit":
                    break
                elif a == ".back":
                    if act:
                        act.pop()
                    else:
                        print("No lines left.")
                elif a == ".clear":
                    act.clear()
                elif a == ".run":
                    if run("\n".join(act), True, f):
                        print("Error!")
                elif a == ".load":
                    print("Load a file. '*' to cancel.")
                    while True:
                        file = input("? ")
                        if not os.path.isfile(file):
                            print("Invalid file path!")
                        elif file == "*":
                            break
                        else:
                            with open(file) as f:
                                stack.extend(f.read().split("\n"))
                elif a == ".remove":
                    while True:
                        line = input(f"1-{len(act)}, '*' to cancel: ").strip()
                        if not line.isdigit():
                            print("Not a digit!")
                        elif line == "*":
                            break
                        else:
                            line = int(line)-1
                            if line in tuple(range(len(act))):
                                act.pop(line)
                                break
                            else:
                                print("Line out of range!")
                elif a == ".show":
                    while True:
                        line = input(f"1-{len(act)}, '*' to cancel: ").strip()
                        if not line.isdigit():
                            print("Not a digit!")
                        elif line == "*":
                            break
                        else:
                            line = int(line)-1
                            if line in tuple(range(len(act))):
                                print(act[line])
                                break
                            else:
                                print("Line out of range!")
                elif a == ".rshow":
                    while True:
                        line = input(f"1-{len(act)}, '*' to cancel: ").strip()
                        if not line.isdigit():
                            print("Not a digit!")
                        elif line == "*":
                            break
                        else:
                            line = int(line)-1
                            if line in tuple(range(len(act))):
                                print("\n".join(act[line:line+10]))
                                break
                            else:
                                print("Line out of range!")
                elif a == ".help":
                    print("'.list' List lines.\n'.back' Erase previouly entered line.\n'.remove' Remove a specific line.\n'.show' Print a specific line.\n'.rshow' Show the specified line with the next 10 available lines.\n'.clear' Delete every line.")
                elif a == ".list":
                    mlen = len(str(len(act)))+1
                    for i, line in enumerate(act, 1):
                        print(f"{str(i).rjust(mlen)} | {line}")
                else:
                    act.append(a)
        elif act.startswith("$"):
            code = os.system(act[1:])
            print(f"Error Code: {'success' if not code else code}")
        else:
            if run(act, True, f):
                print("Error!")
