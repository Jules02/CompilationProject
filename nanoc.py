from lark import Lark
from symboltable import *

symboltable = SymbolTable()
import struct

cpt = 0
double_constants = {}

g = Lark("""
TYPE: "long" | "double"
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\\-*\\/\\>]/
DOUBLE: /[0-9]*\\.[0-9]+([eE][+-]?[0-9]+)?/
declaration: TYPE IDENTIFIER                                                -> declaration                   
liste_var:                                                                  -> vide
    | declaration ("," declaration)*                                        -> vars
expression: IDENTIFIER                                                      -> var
    | expression OPBIN expression                                           -> opbin
    | NUMBER                                                                -> number
    | DOUBLE                                                                -> double
    |"(" "double" ")" expression                                            -> cast_double
commande: IDENTIFIER "=" expression ";"                                     -> affectation
    | declaration ";"                                                       -> decl_cmd
    | declaration "=" expression ";"                                        -> declpuisinit_cmd
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
op2asm_double = {'+' : 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1'}
def asm_expression(e):
    global double_constants
    if e.data == "var":
        var_name = e.children[0].value
        if symboltable.is_declared(var_name):
            var_type = symboltable.get_type(var_name)
            if var_type == "double":
                return f"movsd xmm0, [{var_name}]", "double"
            return f"mov rax, [{var_name}]", "long"
        raise ValueError(f"Variable '{var_name}' is not declared.")
    if e.data == "number": 
        return f"mov rax, {e.children[0].value}", "long"
    if e.data == "double":
        val = e.children[0].value
        float_val = float(val)
        if float_val in double_constants:
            const_name, _, _ = double_constants[val]
            return f"movsd xmm0, [{const_name}]", "double"
        else:
            binary = struct.unpack('<Q', struct.pack('<d', float_val))[0]
            const_name = f".LC{len(double_constants)}"
            low_word = binary & 0xFFFFFFFF
            high_word = (binary >> 32) & 0xFFFFFFFF
            double_constants[val] = (const_name, low_word, high_word)
            return f"movsd xmm0, [{const_name}]", "double"
    if e.data == "cast_double":
        code, typ = asm_expression(e.children[0])
        if typ == "long":
            return f"{code}\ncvtsi2sd xmm0, rax", "double"
        return f"{code}", "double"
    if e.data == "opbin":
        left_code, left_type = asm_expression(e.children[0])
        op = e.children[1].value
        right_code, right_type = asm_expression(e.children[2])
        if left_type == "long" and right_type == "long":
            return f"""{left_code}
push rax
{right_code}
mov rbx, rax
pop rax
{op2asm[op]}""", "long"
        code = ""
        if left_type == "long":
            code += f"{left_code}\ncvtsi2sd xmm1, rax\n"
        else:
            code += f"{left_code}\nmovsd xmm1, xmm0\n"

        if right_type == "long":
            code += f"{right_code}\ncvtsi2sd xmm0, rax\n"
        else:
            code += f"{right_code}\n"

        code += f"{op2asm_double[op]}"
        return code, "double"

def asm_bloc(b):
    seq = ""
    for c in b.children:
        seq += asm_commande(c) + "\n"
    return seq

def asm_commande(c):
    global cpt
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        code, typ = asm_expression(exp)
        if symboltable.is_declared(var.value) and symboltable.get_type(var.value) == "double":
            return f"{code}\nmovsd [{var.value}], xmm0"
        return f"{code}\nmov [{var.value}], rax"
    if c.data == "decl_cmd":
        type_node = c.children[0].children[0]
        var = c.children[0].children[1]
        var_name = var.value
        
        if not symboltable.is_declared(var_name):
            symboltable.declare(var_name, type_node.value)
        return ""
    if c.data == "declpuisinit_cmd":
        type_node = c.children[0].children[0]
        var = c.children[0].children[1]
        exp = c.children[1]
        var_name = var.value
        
        if not symboltable.is_declared(var_name):
            symboltable.declare(var_name, type_node.value)
        
        code, typ = asm_expression(exp)
        symboltable.initialize(var_name)
        if type_node.value == "double":
            return f"{code}\nmovsd [{var_name}], xmm0"
        return f"{code}\nmov [{var_name}], rax"
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = cpt
        cpt += 1
        code, typ = asm_expression(exp)
        return f"""loop{idx}:{code}
cmp rax, 0
jz end{idx}
{asm_bloc(body)}
jmp loop{idx}
end{idx}: nop
"""
    if c.data == "ite":
        exp = c.children[0]
        body_if = c.children[1]
        idx = cpt
        cpt += 1
        code, typ = asm_expression(exp)
        
        if len(c.children) > 2:
            body_else = c.children[2]
            return f"""{code}
cmp rax, 0
jz else{idx}
{asm_bloc(body_if)}
jmp endif{idx}
else{idx}: 
{asm_bloc(body_else)}
endif{idx}: nop
"""
        else:
            return f"""{code}
cmp rax, 0
jz endif{idx}
{asm_bloc(body_if)}
endif{idx}: nop
"""
    if c.data == "print":
        exp = c.children[0]
        code, typ = asm_expression(exp)
        if typ == "double":
            return f"""{code}
mov rdi, fmt_double
mov rax, 1
call printf
"""
        else:
            return f"""{code}
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
"""
    if c.data == "skip": return "nop"


def asm_program(p):
    global double_constants, cpt
    double_constants.clear()
    cpt = 0
    
    with open("moule.asm", encoding="utf-8") as f:
        prog_asm = f.read()


    decl_vars = ""
    init_vars = ""
    
    def scan_double_constants(node):
        if hasattr(node, 'data'):
            if node.data == "affectation" or node.data == "declpuisinit_cmd":
                if len(node.children) >= 2 and hasattr(node.children[1], 'data') and node.children[1].data == "double":
                    val = node.children[1].children[0].value
                    float_val = float(val)
                    binary = struct.unpack('<Q', struct.pack('<d', float_val))[0]
                    const_name = f".LC{len(double_constants)}"
                    low_word = binary & 0xFFFFFFFF
                    high_word = (binary >> 32) & 0xFFFFFFFF
                    double_constants[val] = (const_name, low_word, high_word)
            for child in node.children:
                scan_double_constants(child)
    
    scan_double_constants(p.children[2])
    
    # handle main parameters
    for i, c in enumerate(p.children[1].children):
        type_node = c.children[0]
        var = c.children[1]
        decl_vars += f"{var.value}: dq 0\n"
        symboltable.declare(var.value, type_node.value)
        if type_node.value == "double":
            init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atof
movsd [{var.value}], xmm0
"""
        else:
            init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var.value}], rax
"""
        symboltable.initialize(var.value)

    # collect all other declarations
    for d in get_declarations(p.children[2]):
        type_node = d.children[0]
        var = d.children[1]
        if not symboltable.is_declared(var.value):
            decl_vars += f"{var.value}: dq 0\n"
            symboltable.declare(var.value, type_node.value)
        
    # Add double constants to .data section
    # for name, hexval in double_constants.items():
    #     decl_vars += f"{name}: dq {hexval}\n"

    ret_type = p.children[0].value
    code, typ = asm_expression(p.children[3])
    
    for val, (name, low, high) in double_constants.items():
        decl_vars += f"{name}:\n"
        decl_vars += f"        .long {low}\n"
        decl_vars += f"        .long {high}\n"
    
    # Handle type conversion when function return type differs from the expression type
    if ret_type == "double":
        if typ == "long":
            code = f"{code}\ncvtsi2sd xmm0, rax"
        code += """
mov rdi, fmt_double
mov rax, 1
call printf
"""
    elif ret_type == "long":
        if typ == "double":
            code += "\ncvttsd2si rax, xmm0"
        code += """
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
"""
        
    prog_asm = prog_asm.replace("RETOUR", code)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_bloc(p.children[2]))
    
    return prog_asm

###############################################################################################
            #Pretty printer
###############################################################################################

def pp_declaration(d):
    type_node = d.children[0]
    var = d.children[1]
    return f"{type_node.value} {var.value}"

def pp_expression(e):
    if e.data in ("var", "number", "double"): 
        return f"{e.children[0].value}"
    if e.data == "cast_double":
        exp = e.children[0]
        return f"(double)({pp_expression(exp)})"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"

def pp_commande(c, indent=0):
    tab = "    " * indent
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
        return f"{tab}printf({pp_expression(c.children[0])});"
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"{tab}while ({pp_expression(exp)}) {{\n{pp_bloc(body, indent + 1)}{tab}}}"
    if c.data == "ite":
        exp = c.children[0]
        com = c.children[1]
        if len(c.children) == 3:
            com_else = c.children[2]
            return f"{tab}if ({pp_expression(exp)}) {{\n{pp_bloc(com, indent + 1)}{tab}}} else {{\n{pp_bloc(com_else, indent + 1)}{tab}}}"
        return f"{tab}if ({pp_expression(exp)}) {{\n{pp_bloc(com, indent + 1)}{tab}}}"

def pp_bloc(b, indent=0):
    str_commandes = ""
    for com in b.children:
        str_commandes += pp_commande(com, indent) + "\n"
    return str_commandes

def pp_programme(p, indent=0):
    type_node = p.children[0]
    args = p.children[1]
    bloc = p.children[2]
    exp = p.children[3]
    str_args = ""
    if args.data != "vide":
        for arg in args.children[:-1]:
            str_args += pp_declaration(arg) + ", "
        str_args += pp_declaration(args.children[-1])
    return f"{type_node.value} main({str_args}) {{\n{pp_bloc(bloc, indent+1)}    return ({pp_expression(exp)});\n}}"


###############################################################################################
            #Main
###############################################################################################

if __name__ == "__main__":
    with open("simpleTypage.c", encoding="utf-8") as f:
        src = f.read()
    ast = g.parse(src)
    print(asm_program(ast))

    # print(symboltable.table)
    #print(asm_program(ast))
    #print(ast.children[0].type)
    #print(ast.children[0].value)
