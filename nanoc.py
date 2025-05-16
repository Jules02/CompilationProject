from lark import Lark
from symboltable import *

symboltable = SymbolTable()

cpt = 0
g = Lark("""
TYPE: "long"
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\\-*\\/\\>]/
declaration: TYPE IDENTIFIER
liste_var:                                                                  -> vide
    | declaration ("," declaration)*                                        -> vars
expression: IDENTIFIER                                                      -> var
    | expression OPBIN expression                                           -> opbin
    | NUMBER                                                                -> number
commande: IDENTIFIER "=" expression ";"                                    -> affectation
    | declaration ";"                                                  -> declaration
    | declaration "=" expression ";"                        -> declarationpuisinitialisation 
    | "while" "(" expression ")" "{" bloc "}"                               -> while
    | "if" "(" expression ")" "{" bloc "}" ("else" "{" bloc "}")?           -> ite
    | "printf" "(" expression ")" ";"                                       -> print
    | "skip" ";"                                                            -> skip
bloc: (commande)*                                                           -> bloc
program: TYPE "main" "(" liste_var ")" "{" bloc "return" "("expression")" ";" "}"
%import common.WS
%ignore WS
""", start='program')


###############################################################################################
            #ASM
###############################################################################################

def get_vars_expression(e):
    pass

def get_vars_commande(c):
    pass

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}


def asm_expression(e):
    if e.data == "var": return f"mov rax, [{e.children[0].value}]"
    if e.data == "number": return f"mov rax, {e.children[0].value}"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    asm_left = asm_expression(e_left)
    asm_right = asm_expression(e_right)
    return f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""


def asm_commande(c):
    global cpt
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        return f"{asm_expression(exp)}\nmov [{var.value}], rax"
    if c.data == "skip": return "nop"
    if c.data == "print": return f"""{asm_expression(c.children[0])}
mov rsi, fmt
mov rdi, rax
xor rax, rax
call printf
"""
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = cpt
        cpt += 1
        return f"""loop{idx}:{asm_expression(exp)}
cmp rax, 0
jz end{idx}
{asm_commande(body)}
jmp loop{idx}
end{idx}: nop
"""
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"{asm_commande(d)}\n {asm_commande(tail)}"


def asm_program(p):
    with open("moule.asm") as f:
        prog_asm = f.read()
    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)
    decl_vars = ""
    init_vars = ""
    for i, c in enumerate(p.children[1].children):
        type = c.children[0]
        var = c.children[1]
        decl_vars += f"{var}: dq 0\n"
        symboltable.declare(var, type)
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var}], rax
"""
        symboltable.initialize(var)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    asm_c = asm_commande(p.children[2])
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
    return prog_asm    

###############################################################################################
            #Pretty printer
###############################################################################################

def pp_declaration(d):
    type = d.children[0]
    var = d.children[1]
    return f"{type.value} {var.value}"

def pp_expression(e):
    if e.data in ("var", "number"):
        return f"{e.children[0].value}"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"

def pp_commande(c, indent=0):
    tab = "    " * indent  # 4 espaces par niveau d'indentation
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        return f"{tab}{var.value} = {pp_expression(exp)};"
    if c.data == "declaration":
        return tab + pp_declaration(c.children[0]) + ";"
    if c.data == "declarationpuisinitialisation":
        decla = c.children[0]
        exp = c.children[1]
        return f"{tab}{pp_declaration(decla)} = {pp_expression(exp)};"
    if c.data == "skip":
        return f"{tab}skip;"
    if c.data == "print":
        return f"{tab}printf ( {pp_expression(c.children[0])} );"
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"{tab}while ( {pp_expression(exp)} ) {{\n{pp_bloc(body, indent + 1)}{tab}}}"
    if c.data == "ite":
        exp = c.children[0]
        com = c.children[1]
        if len(c.children) == 3:
            com_else = c.children[2]
            return (
                f"{tab}if ( {pp_expression(exp)} ) {{\n"
                f"{pp_bloc(com, indent + 1)}"
                f"{tab}}} else {{\n"
                f"{pp_bloc(com_else, indent + 1)}"
                f"{tab}}}"
            )
        return (
            f"{tab}if ( {pp_expression(exp)} ) {{\n"
            f"{pp_bloc(com, indent + 1)}"
            f"{tab}}}"
        )

def pp_bloc(b, indent=0):
    str_commandes = ""
    for com in b.children:
        str_commandes += pp_commande(com, indent) + "\n"
    return str_commandes

def pp_programme(p, indent=0):
    tab = "    " * indent  # 4 espaces par niveau d'indentation
    type = p.children[0]
    args = p.children[1]
    com = p.children[2]
    exp = p.children[3]
    str_args = ""
    if args.data != "vide":
        for arg in args.children[:-1]:
            str_args += pp_declaration(arg) + ", "
        str_args += pp_declaration(args.children[-1]) # évite l'ajout d'une virgule après le dernier argument
    return (
        f"{type} main ( {str_args} ) {{\n"
        f"{pp_bloc(com, indent+1)}"
        f"{tab}    return ( {pp_expression(exp)} );\n"
        f"}}"
    )


###############################################################################################
            #Main
###############################################################################################

if __name__ == "__main__":
    with open("simple.c") as f:
        src = f.read()
    ast = g.parse(src)
    print(pp_programme(ast))
    #print(asm_program(ast))
    #print(ast.children[0].type)
    #print(ast.children[0].value)
