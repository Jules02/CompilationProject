from lark import Lark
from pretty_printers import *
from symboltable import *

symboltable = SymbolTable()
import struct

cpt = iter(range(1000))  # iterator for unique loop labels

PRIMITIVE_TYPES = {"long": 1, "double": 1}
struct_definitions = {}

double_constants = {}
raiseWarnings = False

g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0"
OPBIN: /[+\\-*\\/\\>]/
DOUBLE: /[0-9]*\\.[0-9]+([eE][+-]?[0-9]+)?/
declaration: IDENTIFIER "*" IDENTIFIER            -> declaration
           | IDENTIFIER IDENTIFIER                -> declaration
one_struct_def: "typedef" "struct" "{" (declaration ";")+ "}" IDENTIFIER ";" -> one_struct_def
structs_def  : (one_struct_def)*                                            -> structs_def
liste_var:                                         -> vide
         | declaration ("," declaration)*          -> vars
expression: IDENTIFIER                             -> var
          | "&" IDENTIFIER                         -> addr_of
          | "malloc" "(" ")"                       -> malloc_call
          | expression OPBIN expression            -> opbin
          | NUMBER                                 -> number
          | DOUBLE                                 -> double
          | "(" "double" ")" expression            -> cast_double
commande: IDENTIFIER "=" expression ";"                      -> affectation
        | declaration ";"                                   -> decl_cmd
        | declaration "=" expression ";"                    -> declpuisinit_cmd
        | IDENTIFIER IDENTIFIER ("{" expression ("," expression)* "}")? ";" -> struct_init_seq
        | "while" "(" expression ")" "{" bloc "}"           -> while
        | "if" "(" expression ")" "{" bloc "}" ("else" "{" bloc "}")? -> ite
        | "printf" "(" expression ")" ";"                   -> print
        | "skip" ";"                                          -> skip
bloc: (commande)*                                              -> bloc
program: structs_def? IDENTIFIER "main" "(" liste_var ")" "{" bloc "return" "(" expression ")" ";" "}"
%import common.WS
%ignore WS
""", start='program')

def get_struct_definitions(p):
    structs = {}
    for struct in p.children[0].children:
        struct_name = struct.children[-1].value
        struct_def = {"attributes": {}, "size": 0}
        for attr in struct.children[:-1]:
            attr_type = attr.children[0].value
            attr_name = attr.children[-1].value  # last child is the name!
            struct_def["attributes"].update({attr_name: attr_type})
            if attr_type in structs:
                struct_def["size"] += structs[attr_type]["size"]
            elif attr_type in PRIMITIVE_TYPES:
                struct_def["size"] += 1
            else:
                if raiseWarnings:
                    print(f"Defining structure {struct_name} with unknown type for attribute {attr_name}")
                struct_def["size"] += 1
        structs[struct_name] = struct_def
    return structs


def get_declarations(c):
    if c.data == "bloc":
        d = []
        for child in c.children:
            d.extend(get_declarations(child))
        return d
    if c.data in ("decl_cmd", "declpuisinit_cmd"):
        return [c.children[0]]
    if c.data == "while":
        return get_declarations(c.children[1])
    if c.data == "ite":
        d = get_declarations(c.children[1])
        if len(c.children) == 3:
            d.extend(get_declarations(c.children[2]))
        return d
    return []

op2asm = {'+': 'add rax, rbx', '-': 'sub rax, rbx'}
op2asm_double = {'+': 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1'}

def asm_expression(e):
    """Gera código e tipo da expressão. Sempre retorna (code:str, typ:str)."""
    global double_constants

    if e.data == "var":
        var_name = e.children[0].value
        if not symboltable.is_declared(var_name):
            raise ValueError(f"Variable '{var_name}' is not declared.")
        var_type = symboltable.get_type(var_name)
        if var_type == "double":
            return f"movsd xmm0, [{var_name}]", "double"
        else: 
            return f"mov rax, [{var_name}]", "long"

    if e.data == "addr_of":
        var_name = e.children[0].value
        if not symboltable.is_declared(var_name):
            raise ValueError(f"Variable '{var_name}' is not declared.")
        return f"lea rax, [{var_name}]", "long"

    if e.data == "malloc_call":
        # aloca 8 bytes e devolve ponteiro em rax
        return "mov rdi, 8\ncall malloc", "long"

    if e.data == "number":
        return f"mov rax, {e.children[0].value}", "long"

    if e.data == "double":
        val = e.children[0].value
        if val not in double_constants:
            float_val = float(val)
            binary = struct.unpack('<Q', struct.pack('<d', float_val))[0]
            const_name = f"LC{len(double_constants)}"
            double_constants[val] = (const_name, binary & 0xFFFFFFFF, (binary >> 32) & 0xFFFFFFFF)
        const_name = double_constants[val][0]
        return f"movsd xmm0, [{const_name}]", "double"

    if e.data == "cast_double":
        code, typ = asm_expression(e.children[0])
        if typ == "long":
            return f"{code}\ncvtsi2sd xmm0, rax", "double"
        return code, "double"

    if e.data == "opbin":
        left_code, left_type = asm_expression(e.children[0])
        op = e.children[1].value
        right_code, right_type = asm_expression(e.children[2])

        if left_type == right_type == "long":
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
            code += right_code + "\n"
        code += op2asm_double[op]
        return code, "double"

    if raiseWarnings:
        print(f"Unsupported expression kind: {e.data}")
    return "", "long" 

def asm_commande(c):
    if c.data == "affectation":
        var_name = c.children[0].value
        exp = c.children[1]
        code, typ = asm_expression(exp)
        if not symboltable.is_declared(var_name):
            print(f"Trying to affect a value to {var_name}, which was not declared. Ignoring.")
            return ""
        symboltable.initialize(var_name)
        if symboltable.get_type(var_name) == "double":
            return f"{code}\nmovsd [{var_name}], xmm0"
        else:
            return f"{code}\nmov [{var_name}], rax"

    if c.data == "decl_cmd":
        return ""

    if c.data == "declpuisinit_cmd":
        declaration = c.children[0]
        type_ = declaration.children[0].value
        var_name = declaration.children[-1].value  # ← índice final
        exp = c.children[1]
        code, typ = asm_expression(exp)
        symboltable.initialize(var_name)
        if type_ == "double":
            return f"{code}\nmovsd [{var_name}], xmm0"
        else:
            return f"{code}\nmov [{var_name}], rax"

    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = next(cpt)
        code, _ = asm_expression(exp)
        return f"""loop{idx}:{code}
cmp rax, 0
jz end{idx}
{asm_bloc(body)}jmp loop{idx}
end{idx}: nop"""

    if c.data == "ite":
        exp = c.children[0]
        body_if = c.children[1]
        idx = next(cpt)
        code, _ = asm_expression(exp)
        if len(c.children) > 2:
            body_else = c.children[2]
            return f"""{code}
cmp rax, 0
jz else{idx}
{asm_bloc(body_if)}jmp endif{idx}
else{idx}: 
{asm_bloc(body_else)}endif{idx}: nop"""
        else:
            return f"""{code}
cmp rax, 0
jz endif{idx}
{asm_bloc(body_if)}endif{idx}: nop"""

    if c.data == "print":
        exp = c.children[0]
        code, typ = asm_expression(exp)
        if typ == "double":
            return f"""{code}
mov rdi, fmt_double
mov rax, 1
call printf"""
        else:
            return f"""{code}
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf"""

    if c.data == "skip":
        return "nop"

    return ""


def asm_bloc(b):
    return "\n".join(asm_commande(c) for c in b.children)

def asm_declaration(var_name, type_):
    w = PRIMITIVE_TYPES.get(type_)
    if w is None:
        w = struct_definitions.get(type_, {}).get("size", 1)
    return f"{var_name}: dq " + ", ".join(["0"] * int(w)) + "\n"

def asm_initialization(var_name, type_, i):
    if type_ == "double":
        return f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atof
movsd [{var_name}], xmm0"""
    else:  # long / ponteiro
        return f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{var_name}], rax"""

def asm_program(p):
    global double_constants, struct_definitions
    double_constants.clear()

    with open("moule.asm", encoding="utf-8") as f:
        prog_asm = f.read()

    decl_vars = ""
    init_vars = ""
    struct_definitions = get_struct_definitions(p)
    
    for i, c in enumerate(p.children[2].children):
        type_ = c.children[0].value
        var_name = c.children[-1].value 
        if type_ not in (set(PRIMITIVE_TYPES.keys()) | set(struct_definitions.keys())):
            continue
        decl_vars += asm_declaration(var_name, type_)
        symboltable.declare(var_name, type_)
        init_vars += asm_initialization(var_name, type_, i)
        symboltable.initialize(var_name)

    for d in get_declarations(p.children[3]):
        type_ = d.children[0].value
        var_name = d.children[-1].value
        if type_ not in (set(PRIMITIVE_TYPES.keys()) | set(struct_definitions.keys())):
            continue
        if not symboltable.is_declared(var_name):
            decl_vars += asm_declaration(var_name, type_)
            symboltable.declare(var_name, type_)

    ret_type = p.children[1].value
    code_ret, expr_t = asm_expression(p.children[4])

    if ret_type == "double" and expr_t == "long":
        code_ret += "\ncvtsi2sd xmm0, rax"
    if ret_type == "long" and expr_t == "double":
        code_ret += "\ncvttsd2si rax, xmm0"

    prog_asm = prog_asm.replace("RETOUR", code_ret)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("COMMANDE", asm_bloc(p.children[3]))
    return prog_asm

if __name__ == "__main__":
    with open("src.c", encoding="utf-8") as f:
        src = f.read()
    raiseWarnings = True
    ast = g.parse(src)
    print(asm_program(ast))
