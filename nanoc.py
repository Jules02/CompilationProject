from lark import Lark
<<<<<<< HEAD
import struct
=======
from symboltable import *

symboltable = SymbolTable()
>>>>>>> upstream/jules/typage

cpt = 0
var_types = {}
g = Lark("""
TYPE: "long"
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
<<<<<<< HEAD
OPBIN: /[+\-*\/>]/
DOUBLE: /[0-9]*\.[0-9]+([eE][+-]?[0-9]+)?/
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
    | DOUBLE                      -> double
    |"(" "double" ")" expression     -> cast_double
commande: commande (";" commande)*   -> sequence
    | "while" "(" expression ")" "{" commande "}" -> while
    | IDENTIFIER "=" expression              -> affectation
|"if" "(" expression ")" "{" commande "}" ("else" "{" commande "}")? -> ite
| "printf" "(" expression ")"                -> print
| "skip"                                  -> skip
program:"main" "(" liste_var ")" "{" commande "return" "(" expression ")" "}"
=======
OPBIN: /[+\\-*\\/\\>]/
declaration: TYPE IDENTIFIER                                -> declaration                   
liste_var:                                                                  -> vide
    | declaration ("," declaration)*                                        -> vars
expression: IDENTIFIER                                                      -> var
    | expression OPBIN expression                                           -> opbin
    | NUMBER                                                                -> number
commande: IDENTIFIER "=" expression ";"                                    -> affectation
    | declaration ";"                                                  -> decl_cmd
    | declaration "=" expression ";"                        -> declpuisinit_cmd
    | "while" "(" expression ")" "{" bloc "}"                               -> while
    | "if" "(" expression ")" "{" bloc "}" ("else" "{" bloc "}")?           -> ite
    | "printf" "(" expression ")" ";"                                       -> print
    | "skip" ";"                                                            -> skip
bloc: (commande)*                                                           -> bloc
program: TYPE "main" "(" liste_var ")" "{" bloc "return" "("expression")" ";" "}"
>>>>>>> upstream/jules/typage
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

<<<<<<< HEAD
double_constants = {}

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx', '*': 'imul rax, rbx', '/': 'cqo\nidiv rbx'}
op2asm_double = {'+' : 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1', '*': 'mulsd xmm0, xmm1', '/': 'divsd xmm0, xmm1'}
=======
def get_declarations(c):
    # Cette fonction récursive permet de parcourir le corps du programme à la recherche de déclarations de variables
    if c.data == "bloc":
        d = []
        for child in c.children:
            d.extend(get_declarations(child))
        return d
    if c.data == "decl_cmd" or c.data == "declpuisinit_cmd":
        return [c.children[0]]
    if c.data == "while":
        return get_declarations(c.children[1])
    if c.data == "ite":
        d = get_declarations(c.children[1])
        if len(c.children) == 3:
            d.extend(get_declarations(c.children[2]))
        return d
    return []


op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}


>>>>>>> upstream/jules/typage
def asm_expression(e):
    global double_constants, var_types
    if e.data == "var": 
        var_name = e.children[0].value
        if var_name in var_types and var_types[var_name] == 'double':
            return f"movsd xmm0, [{var_name}]"
        return f"mov rax, [{e.children[0].value}]"
    if e.data == "number": return f"mov rax, {e.children[0].value}"
    if e.data == "double":
        val = e.children[0].value
        try:
            float_val = float(val)
            binary = struct.unpack('<Q', struct.pack('<d', float_val))[0]
            const_name = f"double_{len(double_constants)}"
            hexval = f"0x{binary:016X} ; {val}"
            double_constants[const_name] = hexval
            return f"movsd xmm0, [{const_name}]"
        except ValueError:
            return "mov rax, 0"
    if e.data == "cast_double": return "cvtsi2sd xmm0, rax"
    if e.data == "opbin":
        e_left = e.children[0]
        e_op = e.children[1]
        e_right = e.children[2]
        asm_left = asm_expression(e_left)
        asm_right = asm_expression(e_right)
        
        if "xmm0" in asm_left or "xmm0" in asm_right:
            if "xmm0" in asm_left:
                if "xmm0" not in asm_right:
                    return f"{asm_left}\nmovsd xmm1, xmm0\n{asm_right}\ncvtsi2sd xmm0, rax\n{op2asm_double[e_op.value]}"
                else:
                    return f"{asm_left}\nmovsd xmm1, xmm0\n{asm_right}\n{op2asm_double[e_op.value]}"
            else:
                return f"{asm_right}\nmovsd xmm1, xmm0\n{asm_left}\ncvtsi2sd xmm0, rax\n{op2asm_double[e_op.value]}"
        else:
            result = f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
pop rax
{op2asm[e_op.value]}"""
        return result

def asm_bloc(b):
    seq = ""
    for c in b.children:
        seq += asm_commande(c) + "\n"
    return seq

def asm_commande(c):
    global cpt, var_types
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
<<<<<<< HEAD
        asm_exp = asm_expression(exp)
        
        if "xmm0" in asm_exp:
            var_types[var.value] = 'double'
            return f"{asm_exp}\nmovsd [{var.value}], xmm0"
        else:
            var_types[var.value] = 'int'
            return f"{asm_exp}\nmov [{var.value}], rax"
    if c.data == "skip": return "nop"
    if c.data == "print":
        exp = c.children[0]
        asm_exp = asm_expression(exp)
        if "xmm0" in asm_exp:
            return f"""{asm_exp}
mov rdi, fmt_double
mov rax, 1
call printf
"""
        else:
            return f"""{asm_exp}
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
"""
=======
        return f"{asm_expression(exp)}\nmov [{var.value}], rax"
    if c.data == "decl_cmd":
        return ""
    if c.data == "declpuisinit_cmd":
        type = c.children[0].children[0]
        var = c.children[0].children[1]
        exp = c.children[1]
        symboltable.initialize(var.value)
        return f"{asm_expression(exp)}\nmov [{var.value}], rax"
>>>>>>> upstream/jules/typage
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = cpt
        cpt += 1
        return f"""loop{idx}:{asm_expression(exp)}
cmp rax, 0
jz end{idx}
{asm_bloc(body)}
jmp loop{idx}
end{idx}: nop
"""
    if c.data == "ite":
<<<<<<< HEAD
        exp = c.children[0]
        body_if = c.children[1]
        idx = cpt
        cpt += 1
        
        if len(c.children) > 2:
            body_else = c.children[2]
            return f"""{asm_expression(exp)}
cmp rax, 0
jz else{idx}
{asm_commande(body_if)}
jmp endif{idx}
else{idx}: 
{asm_commande(body_else)}
endif{idx}: nop
"""
        else:
            return f"""{asm_expression(exp)}
cmp rax, 0
jz endif{idx}
{asm_commande(body_if)}
endif{idx}: nop
"""
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"{asm_commande(d)}\n {asm_commande(tail)}"
=======
        return "TODO"
    if c.data == "print": return f"""{asm_expression(c.children[0])}
mov rsi, fmt
mov rdi, rax
xor rax, rax
call printf
"""
    if c.data == "skip": return "nop"
>>>>>>> upstream/jules/typage


def asm_program(p):
    global double_constants, var_types
    double_constants.clear()
    var_types.clear()
    with open("moule.asm", encoding="utf-8") as f:
        prog_asm = f.read()
<<<<<<< HEAD
    asm_c = asm_commande(p.children[1])
    ret = asm_expression(p.children[2])
    init_vars = ""
    decl_vars = ""
    for i, c in enumerate(p.children[0].children):
        var_name = c.value
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var_name}], rax
"""
        decl_vars += f"{var_name}: dq 0\n"
        var_types[var_name] = 'int'
        
    for name, hexval in double_constants.items():
        decl_vars += f"{name}: dq {hexval}\n"
        
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
    prog_asm = prog_asm.replace("RETOUR", ret)
    return prog_asm    

def pp_expression(e):
    if e.data in ("var","number","float","double"): return f"{e.children[0].value}"
    if e.data == "cast_float": 
        exp = e.children[0]
        return f"(float)({pp_expression(exp)})"
    if e.data == "cast_double":
        exp = e.children[0]
        return f"(double)({pp_expression(exp)})"
=======

    # Retour du programme
    ret_type = p.children[0]
    ret = asm_expression(p.children[3])
    prog_asm = prog_asm.replace("RETOUR", ret)

    # Déclaration et initialisation des variables passées en argument
    decl_vars = ""
    init_vars = ""
    for i, c in enumerate(p.children[1].children):
        type = c.children[0]
        var = c.children[1]
        decl_vars += f"{var}: dq 0\n"
        symboltable.declare(var.value, type.value)
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var}], rax
"""
        symboltable.initialize(var.value)

    # Déclaration des variables déclarées dans le corps du programme
    for d in get_declarations(p.children[2]):
        type = d.children[0]
        var = d.children[1]
        decl_vars += f"{var}: dq 0\n"
        symboltable.declare(var.value, type.value)

    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)

    # Corps du programme
    asm_b = asm_bloc(p.children[2])
    prog_asm = prog_asm.replace("COMMANDE", asm_b)

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
>>>>>>> upstream/jules/typage
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
    if c.data == "decl_cmd":
        return tab + pp_declaration(c.children[0]) + ";"
    if c.data == "declpuisinit_cmd":
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
    with open("simple.c", encoding="utf-8") as f:
        src = f.read()
    ast = g.parse(src)
<<<<<<< HEAD
    print(asm_program(ast))
=======
    #print(pp_programme(ast))
    print(asm_program(ast))

    print(symboltable.table)
    #print(asm_program(ast))
    #print(ast.children[0].type)
    #print(ast.children[0].value)
>>>>>>> upstream/jules/typage
