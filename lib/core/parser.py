from .info import *
from .utils import *
import array
import pickle
import atexit

stack = []
includes = set()

class bstate:
    def __init__(self, name):
        self.name = name
    def __eq__(self, other):
        if not isinstance(other, bstate):
            return False
        return other.name == self.name
    def __ne__(self, other):
        return not self == other
    def __repr__(self):
        return f"bstate({self.name!r})"

def expr_preruntime(arg):
    if arg.endswith("i"):
        return int(arg[:-1])
    elif arg.endswith("f"):
        return float(arg[:-1])
    elif arg == "true":
        return 1
    elif arg == "false":
        return 0
    elif arg == "nil":
        return bstate("nil")
    elif arg == "none":
        return bstate("none")
    elif arg == "mark":
        return bstate("mark")
    return arg

def expr_runtime(arg):
    if not isinstance(arg, str):
        return arg
    arg = arg.strip()
    if arg == "top":
        return stack.pop() if stack else bstate("nil")
    elif arg == "top:peek":
        return stack[-1] if stack else bstate("nil")
    elif arg.startswith("arr:index:"):
        index = int(arg[10:])
        if stack and isinstance(stack[-1], (array.array, list)) and stack[-1] and index in range(-len(stack[-1]), len(stack[-1])):
            return stack[-1][index]
        else:
            return bstate("nil")
    elif arg.startswith("arr:top"):
        if stack and isinstance(stack[-1], (array.array, list)) and stack[-1]:
            return stack[-1].pop()
        else:
            return bstate("nil")
    elif arg.startswith("arr:peek"):
        if stack and isinstance(stack[-1], (array.array, list)) and stack[-1]:
            return stack[-1][-1]
        else:
            return bstate("nil")
    elif arg.replace(".", "").replace("_", "").isalnum():
        return arg
    # some how some unrpocessed integers passed
    elif arg.endswith("i"):
        return int(arg[:-1])
    elif arg.endswith("f"):
        return float(arg[:-1])
    return bstate("nil")

def evaluate(expression):
    if expression and expression[0] == "list":
        return compress(expression[1:])
    match (expression):
        case [op1, "==", op2]:
            return expr_runtime(op1) == expr_runtime(op2)
        case [op1, "!=", op2]:
            return expr_runtime(op1) != expr_runtime(op2)
        case [op1, ">", op2]:
            return expr_runtime(op1) > expr_runtime(op2)
        case [op1, "<", op2]:
            return expr_runtime(op1) > expr_runtime(op2)
        case [op1, ">=", op2]:
            return expr_runtime(op1) >= expr_runtime(op2)
        case [op1, "<=", op2]:
            return expr_runtime(op1) >= expr_runtime(op2)
        case ["not", op1]:
            return not expr_runtime(op1)
        case [op1, "or", op2]:
            return expr_runtime(op1) or expr_runtime(op2)
        case [op1, "and", op2]:
            return expr_runtime(op1) and expr_runtime(op2)
        case [op1, "+", op2]:
            return expr_runtime(op1) + expr_runtime(op2)
        case [op1, "-", op2]:
            return expr_runtime(op1) - expr_runtime(op2)
        case [op1, "*", op2]:
            return expr_runtime(op1) * expr_runtime(op2)
        case [op1, "/", op2]:
            return expr_runtime(op1) / expr_runtime(op2)
        case [op1, "%", op2]:
            return expr_runtime(op1) % expr_runtime(op2)
        case [op1, "^", op2]:
            return expr_runtime(op1) ** expr_runtime(op2)
        case ["len-of", op1]:
            value = expr_runtime(op1)
            if hasattr(value, "__len__"):
                return len(value)
            else:
                return bstate("nil")
        case _:
            return bstate("nil")

def exprs_runtime(args):
    put = []
    res = []
    p = 0
    while p < len(args):
        c = args[p]
        if c == "\"":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and not c.endswith("\""):
                c = args[p]; put.append(c); p += 1
            p -= 1
            text = " ".join(put)[:-1]
            for c, r in CHARS.items():
                text = text.replace(c, r)
            res.append(text.replace("\\[quote]", "\""))
        elif c == "(":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and c != ")":
                c = args[p]; put.append(c); p += 1
            p -= 1
            put.pop()
            res.append(evaluate(put))
        elif c == "((":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and c != "))":
                c = args[p]; put.append(c); p += 1
            p -= 1
            put.pop()
            repeatition, *parts = put
            res.append(compress([*exprs_runtime(parts)]*expr_runtime(repeatition)))
        elif c == "'":
            c = ""
            p += 1
            put.clear()
            while p < len(args) and not c.endswith("'"):
                c = args[p]; put.append(c); p += 1
            p -= 1
            text = " ".join(put)[:-1]
            for c, r in CHARS.items():
                text = text.replace(c, r)
            res.append(text.replace("\\[quote]", "'"))
        else:
            res.append(expr_runtime(c))
        p += 1
    return *res,

def exprs_preruntime(args):
    return *map(expr_preruntime, args),

def process(code, name=MAIN_NAME):
    res = []
    oname = name
    c = enumerate(code.split("\n"), 1)
    for lp, line in c:
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        elif line.startswith("#"):
            line = line[1:].strip()
            if line.startswith("!"):
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
                    if name != MAIN_NAME:
                        name = arg
                elif ins == "force.chname" and arg is not None:
                    name = arg
                elif ins == "define" and arg is not None:
                    if arg in includes:
                        return tuple()
                    else:
                        includes.add(arg)
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
            args = exprs_preruntime(args)
            res.append((lp, name, ins, args))
    else:
        return tuple(res)
    exit(1)

def run(code, funcs=None):
    if isinstance(code, str):
        code = process(code)
    funcs = funcs if funcs is not None else {}
    p = 0
    while p < len(code):
        pos, file, ins, args = code[p]
        args = *exprs_runtime(args),
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
                stack.append(bstate("nil"))
        elif ins == "clear" and argc == 0:
            stack.clear()
        elif ins == "mark" and argc == 0:
            stack.append(bstate("mark"))
        elif ins == "clear_safe" and argc == 0:
            while stack and stack[-1] != bstate("mark"):
                stack.pop()
        elif ins == "rot" and argc == 0:
            if len(stack) < 2:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt rotate stack items!")
                break
            b, a = stack.pop(), stack.pop()
            stack.extend([b, a])
        elif ins == "reverse" and argc == 0:
            stack.reverse()
        elif ins == "stack:show" and argc == 0:
            print(f"[{'' if not stack else ' '+(','+chr(10)+'  ').join(minimize(map(repr, stack)))+' '}]")
        # arrays
        elif ins == "make-array" and argc == 1:
            if args[0] == "any":
                stack.append([])
            elif args[0] == "float":
                stack.append(array.array("f"))
            elif args[0] == "int":
                stack.append(array.array("i"))
            else:
                print(f"\nError on line {pos} in file `{file}`\nInvalid array type!")
                break
        elif ins == "pushto" and argc == 1:
            if stack and isinstance(stack[-1], (array.array, list)):
                try:
                    stack[-1].append(args[0])
                except:
                    print(f"\nError on line {pos} in file `{file}`\nCouldnt push to array!")
                    break
            else:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt access the array!")
                break
        elif ins == "popfrom" and argc == 0:
            if stack and isinstance(stack[-1], (array.array, list)):
                if stack[-1]:
                    stack[-1].pop()
            else:
                print(f"\nError on line {pos} in file `{file}`\nCouldnt access the array!")
                break
        elif ins == "rotthis" and argc == 0:
            if not stack or len(stack[-1]) < 2 or not isinstance(stack[-1], (array.array, list)):
                print(f"\nError on line {pos} in file `{file}`\nCouldnt rotate stack items!")
                break
            b, a = stack[-1].pop(), stack[-1].pop()
            stack[-1].extend([b, a])
        elif ins == "revthis" and argc == 0:
            if not stack or not isinstance(stack[-1], (array.array, list)):
                print(f"\nError on line {pos} in file `{file}`\nCouldnt reverse stack items!")
                break
            stack[-1].reverse()
        elif ins == "dupethis" and argc == 0:
            if not stack or not isinstance(stack[-1], (array.array, list)):
                print(f"\nError on line {pos} in file `{file}`\nCouldnt rotate stack items!")
                break
            if stack[-1]:
                stack[-1].append(stack[-1][-1])
            else:
                if isinstance(stack[-1], array.array):
                    stack[-1].append(0 if stack[-1].typecode == "i" else 0.0)
                elif isinstance(stack[-1], list):
                    stack[-1].append(bstate("nil"))
        # pickling the stack
        elif ins == "stack:save" and argc == 1:
            with open(args[0], "w") as f:
                f.write(f"[{'' if not stack else ','.join(minimize(map(repr, stack), True))}]")
        elif ins == "stack:load" and argc == 1:
            if not os.path.isfile(args[0]):
                print(f"\nError on line {pos} in file `{file}`\nCouldnt load stack items!\nFile {arg[0]!r} is not a file!")
                break
            with open(args[0], "r") as f:
                try:
                    stack.extend(eval(f.read(), {"__builtins__":{}, "array":array.array, "bstate":bstate}))
                except Exception as e:
                    print(f"\nError on line {pos} in file `{file}`\nCouldnt load stack items!\nReason: {repr(e)}")
                    break
        # functions
        elif ins == "fn" and argc == 1:
            temp = []
            name = args[0]
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction not closed!")
                break
            if file != MAIN_NAME:
                name = mangle(file, name)
            if name in funcs:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction already defined in file {funcs[name][0]!r}")
                break
            funcs[name] = file, temp
        elif ins == "sfn" and argc == 1:
            temp = []
            name = args[0]
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
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
                if file != MAIN_NAME:
                    name = mangle(file, name)
                funcs[name] = (file, tuple())
            else:
                print(f"\nError on line {pos} in file `{file}`\nFunction type {t!r} unknown!")
        elif ins == "ifmain" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file != MAIN_NAME:
                p += 1
                continue
            try:
                err = run(temp, funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "ifsetup" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file != SETUP_NAME:
                p += 1
                continue
            try:
                err = run(temp, funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "notmain" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf main function not closed!")
                break
            if file == MAIN_NAME:
                p += 1
                continue
            try:
                err = run(temp, funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "call" and argc == 1:
            name = args[0]
            if name not in funcs:
                print(f"\nError on line {pos} in file `{file}`\nInvalid function: {name}")
                break
            try:
                err = run(funcs[name][1], funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {pos} in file `{file}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "dyncall" and argc == 1:
            name = args[0]
            if file != MAIN_NAME:
                name = mangle(file, name)
            if name not in funcs:
                print(f"\nError on line {pos} in file `{file}`\nInvalid function: {name}")
                break
            try:
                err = run(funcs[name][1], funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nFunction raised an error!")
                break
            elif err == -1:
                return err
        # if statements
        elif ins == "iftrue" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if not oargs[0]:
                p += 1
                continue
            try:
                err = run(temp, funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "iffalse" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function not closed!")
                break
            if oargs[0]:
                p += 1
                continue
            try:
                err = run(temp, funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{ofile}`\nIf function raised an error!")
                break
            elif err == -1:
                return err
        # version handling
        elif ins == "version" and argc == 2:
            funcs[f"version:{args[0]}"] = args[1]
        elif ins == "require" and argc == 2:
            v = funcs.get(f"version:{args[0]}")
            if v == None:
                ...
            else:
                if v != args[1]:
                    print(f"\nError on line {pos} in file `{file}`\nRequires version '{args[0]}:{args[1]}' but got '{args[0]}:{v}'")
                    break
        elif ins == "partreq" and argc == 2:
            v = funcs.get(f"version:{args[0]}")
            if v == None:
                ...
            else:
                if v > args[1]:
                    print(f"\nError on line {pos} in file `{file}`\nRequires version '{args[0]}:{args[1]}' but got '{args[0]}:{v}'")
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
        elif ins == "foreach" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            try:
                for i in oargs[0]:
                    stack.append(i)
                    try:
                        err = run(temp, funcs=funcs)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception as e:
                        print(repr(e))
                        break
                    if err > 0:
                        break
                    elif err == -1:
                        raise StopIteration()
                else:
                    p += 1
                    continue
                break
            except StopIteration:
                pass
        elif ins == "for" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            try:
                for i in tuple(range(oargs[0])):
                    stack.append(i)
                    try:
                        err = run(temp, funcs=funcs)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except Exception as e:
                        print(repr(e))
                        break
                    if err > 0:
                        break
                    elif err == -1:
                        raise StopIteration()
                else:
                    p += 1
                    continue
                break
            except StopIteration:
                pass
        elif ins == "ufor" and argc == 1:
            temp = []
            opos = pos
            ofile = file
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            try:
                for i in tuple(range(oargs[0])):
                    try:
                        err = run(temp, funcs=funcs)
                    except (SystemExit, KeyboardInterrupt):
                        raise
                    except StopIteration:
                        pass
                    except Exception as e:
                        print(repr(e))
                        break
                    if err > 0:
                        break
                    elif err == -1:
                        raise StopIteration()
                else:
                    p += 1
                    continue
                break
            except StopIteration:
                pass
        elif ins == "loop" and argc == 0:
            temp = []
            opos = pos
            ofile = file
            p += 1
            k = 1
            while p < len(code):
                pos, file, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, file, ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{ofile}`\nFor function not closed!")
                break
            if not stack:
                p += 1
                continue
            ok = True
            while ok:
                try:
                    err = run(temp, funcs=funcs)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except StopIteration:
                    pass
                except Exception as e:
                    print(repr(e))
                    break
                if err > 0:
                    break
                elif err == -1:
                    ok = False
            else:
                p+=1
                continue
            break
        # libs
        elif ins == "cache" and argc == 1:
            name = args[0]
            with open(name, "wb") as f:
                f.write(pickle.dumps(funcs))
        elif ins == "load" and (argc == 1 or argc == 2):
            with open(args[0], "rb") as f:
                fs = pickle.loads(f.read())
                if argc == 2:
                    fs = {f"{args[1]}.{name}":code for name, code in fs.items()}
                funcs.update(fs)
        elif ins == "module" and argc == 1:
            temp = []
            opos = pos
            oargs = args
            p += 1
            k = 1
            while p < len(code):
                pos, _, ins, args = code[p]
                if ins in INC:
                    k += 1
                elif ins == "end":
                    k -= 1
                if ins == "end" and k == 0:
                    break
                temp.append((pos, oargs[0], ins, args))
                p += 1
            else:
                print(f"\nError on line {opos} in file `{file}`\nInline module not closed!")
                break
            try:
                err = run(temp, funcs=funcs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(repr(e))
                break
            if err > 0:
                print(f"\nError on line {opos} in file `{file}`\nInline module raised an error!")
                break
            elif err == -1:
                return err
        elif ins == "setup" and argc == 0:
            with open(args[0], "r") as f:
                name = SETUP_NAME
                x = process(f.read(), name)
                fs = {}
                if run(x, funcs=fs):
                    print(f"\nError on line {pos} in file `{file}`\nFunction {name!r} raised an error!")
                    break
                funcs.update(fs)
        elif ins == "exec" and argc == 1:
            ofile = file
            file = args[0]
            if not os.path.isfile(file):
                print(f"\nError on line {pos} in file `{ofile}`\nCouldnt find {file!r}")
                break
            with open(file) as f:
                run(f.read(), funcs=funcs)
        # system
        elif ins == "system" and argc == 1:
            stack.append(os.system(args[0]))
        elif ins == "system:getenv" and argc == 1:
            stack.append(os.getenv(args[0], 0))
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
        elif ins == "stop" and argc == 0:
            return -1
        else:
            print(f"\nError on line {pos} in file `{file}`\nInvalid instruction: {ins}\nArguments: {' '.join(map(repr, args))}")
            break
        p += 1
    else:
        return 0
    return 1