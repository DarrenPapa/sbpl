# Please do not modify as this is the documentation
# for sbpl and its inner workings.
# Failure to abide to this rule will fall under
# copyright infridgement.

# See LICENSE.txt

docu = {
"MATH":"""Mathematical Operations

Using math expressions.
Math expressions CANNOT have strings in them!

Use the stack and access them through `top` or
`top:peek` or where ever that string is.

Math expressions are denoted using `( expr )`
And yes the spaces are relevant for every item in there.

Example:
    println ( 90i + 80i )

Use `( len-of [value] )` to get the length of a value.
It returns nil if the value isnt one of the types that has
length in them.

Limitations:

Expressions in general cant be linked like `( 1i + 2i + 3i )` due to
how it is parsed, it makes the implementation more easier and
more faster than using advanced parsing.""",
"IO":"""IO

Input/Output Operations.

print [value]   - Prints the value.
println [value] - Prints the value with a newline.
input           - Asks for input then pushes the response
onto the stack.""",
"STACK":"""Stack

A data structure that uses simple operations to store values.
To add onto the stack is called pushing and removing from the stack
is called popping.

The stack enforces a FILO (first in last out) structure.
The first pushed item will be the last popped item.

Example:
push 90i -> [90]
push 80i -> [90, 80]
pop -> [90]
pop -> []

See also 'STACK OPS'""",
"STACK OPS":"""Stack Operations

push [value]          - Pushes the value into the stack.
pop                   - Discard the top value.
                      (See 'ARGUMENTS' on how to use the top value)
dupe                  - Duplicate the top item.
rot                   - Rotate the top two items.
reverse               - Reverse the stack.
clear                 - Clear the stack.
stack:show            - Print out the stack.
stack:save [file:str] - Save the stack to a file.
stack:load [file:str] - Load the file onto the stack.
                      Does not affect items already in the stack.""",
"FUNCTIONS":"""Functions

Functions are useful for reusing blocks of code.
To reduce the redundancy of code.

fn [name:str]      - Define a function. The name is mangled depending
                   On context.
sfn [name:str]     - Define a function that doesnt have name mangling.
call [name:str]    - Call a function.
dyncall [name:str] - Call a function and mangle the name depending
                   On the current context.""",
"IF STATEMENTS":"""If Statements

iftrue [value]  - If value is true then it runs.
iffalse [value] - If value is false then it runs.

See also 'COMPARISONS'""",
"COMPARISONS":"""Comparisons

Operators to compare values.
These are operators in math expressions.

[arg1] == [arg2]
[arg1] != [arg2]
[arg1:number] < [arg2:number]
[arg1:number] > [arg2:number]
[arg1:number] <= [arg2:number]
[arg1:number] >= [arg2:number]

not [arg1]
[arg1] or [arg2]
[arg1] and [arg2]

See also 'MATH'""",
"ARGUMENTS":"""Arguments

Values that are passed to instructions.
Commas are not used to separate arguments.
Example:
    println string: Hello, world!:end

Data types:
    strings    - `" Hello, world!"`
               Yes the space is needed.
    intgers    - `100i`
    floats     - `100.0f`
    identifier - names (any alphanumeric names)
               Dots and underscores are also valid!
               So `module.some_func` is valid.

Stack:
    top      - Pops the top value.
    top:peek - Top value.
    arr:top  - Pops the top of an collection.
             Located on the top of the stack.
    arr:peek - The top of the collection.
             Located on the top of the stack.

Constants:
    true
    false
    nil  - When a value cannot be found or is invalid.
    none - Explicitly empty.
    mark - To section of a part of the stack.""",
"LOOPS":"""Loops

Loops are useful for reducing the redundancy.
Dont wanna dont wanna repeat stuff dont you?

foreach          - Iterates through the collection at the top of the stack.
                 Pushes the current item onto the stack.
                 Shallow copies the iterator to avoid side effects.
for [steps:int]  - Iterates steps number of times. Pushes the current step to
                 the stack.
ufor [steps:int] - Iterates steps number of times. Does not push the
                 current step onto the stack.
loop             - Loop indefinitely.""",
"BLOCKED INSTRUCTIONS":"""Instructions That Require 'end'

Instructions that use code blocks.

fn
sfn
for
ufor
loop
module
iftrue
iffalse
setup
ifmain
notmain

Example:
    fn main
        println " Hello, world!"
    end
""",
"MODULES":"""Modularizing Code

Inportant for organizing large code bases.

version [name:str] [version:float] - Sets the version info of the module.
require [name:str] [version:float] - Stricttly requires the given version.
partreq [name:str] [version:float] - Partialy requires that version.
                                   Unless the given version is lower,
                                   it wont raise an error.
module [name:str]                  - Define an inline module."""
}

def printd(text):
    text = text.split("\n")
    win = 15
    if len(text) > win:
        p = 0
        print("Press enter to advance...")
        while p<len(text):
            print("\n".join(text[p:p+win]),end="")
            if input("") == ".":
                break
            p += win
    else:
        print("\n".join(text))

print("Documentation for SBPL\nEnter TOPICS to see available topics. Enter INFO to see more.")
while True:
    act = input(": ")
    if act == "TOPICS":
        print(f"Topics: {', '.join(map(repr,docu.keys()))}")
    elif act == "INFO":
        print("""Info

Core Devs:
    - Darren Chase Papa
        lib.core.*
        sbpl.py
        docu.py

Documentation shown here were written by:
    - Darren Chase Papa""")
    elif act in docu:
        printd(docu[act])
    else:
        print("Enter TOPICS to see available topics.")