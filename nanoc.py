from lark import Lark
from pretty_printers import *
from symboltable import *

symboltable = SymbolTable()
import struct

cpt = iter(range(1000))  # iterator for unique loop labels

PRIMITIVE_TYPES = { "long" : 8, "double" : 8 }
struct_definitions = {}

double_constants = {}
raiseWarnings = False

g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0"
OPBIN: /[+\\-]/
DOUBLE: /[0-9]*\\.[0-9]+([eE][+-]?[0-9]+)?/
declaration: IDENTIFIER ("*")? IDENTIFIER            -> declaration
one_struct_def: "typedef" "struct" "{" (declaration ";")+ "}" IDENTIFIER ";" -> one_struct_def
structs_def  : (one_struct_def)*                                            -> structs_def
liste_var:                                         -> vide
         | declaration ("," declaration)*          -> vars
expression: IDENTIFIER                             -> var
          | "&" IDENTIFIER                         -> addr_of
          | "malloc" "(" ")"                       -> malloc_call
          | expression OPBIN expression            -> opbin
          | NUMBER                                 -> number
          | DOUBLE                                                          -> double
          | "(" "double" ")" expression                                     -> cast_double
commande: IDENTIFIER "=" expression ";"                                     -> affectation
        | declaration ";"                                                   -> decl_cmd
        | declaration "=" expression ";"                                    -> declpuisinit_cmd
        | IDENTIFIER IDENTIFIER ("{" expression ("," expression)* "}")? ";" -> struct_init_seq
        | "while" "(" expression ")" "{" bloc "}"                           -> while
        | "if" "(" expression ")" "{" bloc "}" ("else" "{" bloc "}")?       -> ite
        | "printf" "(" expression ")" ";"                                   -> print
        | "skip" ";"                                          -> skip
bloc: (commande)*                                              -> bloc
program: structs_def? IDENTIFIER "main" "(" liste_var ")" "{" bloc "return" "(" expression ")" ";" "}"
%import common.WS
%ignore WS
""", start='program')

def mem(var, off):
    return f'[{var}+{off}]' if off else f'[{var}]'

def get_struct_definitions(p):
    # Reads typedefs in the preamble
    structs = {}
    for struct in p.children[0].children:
        struct_name = struct.children[-1].value
        struct_def = {"attributes" : {}, "size" : 0}
        offset = 0
        for attr in struct.children[:-1]:
            attr_name = attr.children[-1].value
            attr_type = attr.children[0].value
            attr_def = {attr_name : {"type" : attr_type, "offset" : offset}}
            struct_def["attributes"].update(attr_def)
            if attr_type in structs.keys() :
                attr_size = structs[attr_type]["size"]
            elif attr_type in PRIMITIVE_TYPES.keys() :
                attr_size = PRIMITIVE_TYPES[attr_type]
            else :
                if raiseWarnings : print(f"Defining structure {struct_name} with unknown type for attribute {attr_name}")
                attr_size = 8
            struct_def["size"] += attr_size
            offset += attr_size
        structs[struct_name] = struct_def
    return structs


def get_declarations(c):
    # Recursive method traversing the body of the program in search of variable declarations
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



op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}
op2asm_double = {'+' : 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1'}

def asm_expression(e):
    global double_constants

    def push_structure(container_name, var_type, offset):
        struct_definition = struct_definitions[var_type]
        a = ""
        for attr in struct_definition["attributes"]:
            attr_type   = struct_definition["attributes"][attr]["type"]
            attr_offset = struct_definition["attributes"][attr]["offset"]
            off         = offset + attr_offset
            if attr_type == "double":
                a += f"movsd xmm0, {mem(container_name, off)}\n"
            elif attr_type == "long":
                a += f"mov   rax, {mem(container_name, off)}\n"
            else:
                a += push_structure(container_name, attr_type, off)
        return a

    if e.data == "var":
        var_name = e.children[0].value
        if symboltable.is_declared(var_name):
            var_type = symboltable.get_type(var_name)
            if var_type == "double":
                return f"movsd xmm0, [{var_name}]", "double"
            elif var_type == "long":
                return f"mov rax, [{var_name}]", "long"
            else:
                # Variable is a structure
                return push_structure(var_name, var_type, 0), var_type
        else:
            raise ValueError(f"Variable '{var_name}' is not declared.")

    if e.data == "addr_of":
        var_name = e.children[0].value
        if not symboltable.is_declared(var_name):
            raise ValueError(f"Variable '{var_name}' is not declared.")
        return f"lea rax, [{var_name}]\n", "long"

    if e.data == "malloc_call":
        return """
mov rdi, 8
call malloc\n""", "long"

    if e.data == "number":
        return f"mov rax, {e.children[0].value}\n", "long"

    if e.data == "double":
        val = e.children[0].value
        if val not in double_constants:
            float_val = float(val)
            binary = struct.unpack('<Q', struct.pack('<d', float_val))[0]
            const_name = f"LC{len(double_constants)}"
            double_constants[val] = (const_name, binary & 0xFFFFFFFF, (binary >> 32) & 0xFFFFFFFF)
        const_name = double_constants[val][0]
        return f"movsd xmm0, [{const_name}]\n", "double"

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
            if raiseWarnings: print("Implicitly converting long to double")
        else:
            code += f"{left_code}\nmovsd xmm1, xmm0\n"
        if right_type == "long":
            code += f"{right_code}\ncvtsi2sd xmm0, rax\n"
            if raiseWarnings: print("Implicitly converting long to double")
        else:
            code += right_code + "\n"
        code += f"\n{op2asm_double[op]}"
        return code, "double"

def asm_bloc(b):
    return "\n".join(asm_commande(c) for c in b.children)

def asm_commande(c):

    def affect(var_type, var_name, offset):
        if var_type == "double":
            return f"movsd {mem(var_name, offset)}, xmm0\n"
        elif var_type == "long":
            return f"mov   {mem(var_name, offset)}, rax\n"
        else:
            a = ""
            struct_definition = struct_definitions[var_type]
            for attr in struct_definition["attributes"]:
                attr_type   = struct_definition["attributes"][attr]["type"]
                attr_offset = struct_definition["attributes"][attr]["offset"]
                a += affect(attr_type, var_name, offset + attr_offset)
            return a


    if c.data == "affectation":
        var_name = c.children[0].value
        exp = c.children[1]
        code, typ = asm_expression(exp)
        if not symboltable.is_declared(var_name):
            print(f"Trying to affect a value to {var_name}, which was not declared. Ignoring.")
            return ""
        var_type = symboltable.get_type(var_name)
        # TODO: handle case when typ is not var_type
        symboltable.initialize(var_name)
        return code + "\n" + affect(var_type, var_name, 0)

    if c.data == "decl_cmd":
        # All declarations were already made
        return ""

    if c.data == "declpuisinit_cmd":
        # Variable was already declared, we just need to initialize it
        declaration = c.children[0]
        var_type = declaration.children[0].value
        var_name = declaration.children[-1].value
        exp = c.children[1]
        code, typ = asm_expression(exp)
        # TODO: handle case when typ is not var_type
        return code + "\n" + affect(var_type, var_name, 0)

    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        idx = next(cpt)
        code, _ = asm_expression(exp)
        return f"""loop{idx}:
{code}
cmp rax, 0
jz end{idx}
{asm_bloc(body)}
jmp loop{idx}
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

def asm_declaration(var_name, type):
    w = 0
    if type in PRIMITIVE_TYPES.keys():
        w = PRIMITIVE_TYPES[type]
    else:
        w = struct_definitions[type]["size"]
    d = f"{var_name}: dq " + ", ".join(["0"] * (w//8)) + "\n"
    return d

def asm_initialization(var_name, type, position):
    initialization = ""
    if type == "double":
        initialization += f"""
mov rbx, [argv]
mov rdi, [rbx + {position}]
call atof
movsd [{var_name}], xmm0
"""
    elif type == "long":
        initialization += f"""
mov rbx, [argv]
mov rdi, [rbx + {position}]
call atoi
mov [{var_name}], rax
"""
    else:

        def affect_init(var_type, var_name, offset):
            if var_type == "double":
                return f"""mov rbx, [argv]
mov rdi, [rbx + {position + offset}]
call atof
movsd {mem(var_name, offset)}, xmm0
"""
            elif var_type == "long":
                return f"""mov rbx, [argv]
mov rdi, [rbx + {position + offset}]
call atoi
mov   {mem(var_name, offset)}, rax
"""
            else:
                a = ""
                struct_definition = struct_definitions[var_type]
                for attr in struct_definition["attributes"]:
                    attr_type   = struct_definition["attributes"][attr]["type"]
                    attr_offset = struct_definition["attributes"][attr]["offset"]
                    a += affect_init(attr_type, var_name, offset + attr_offset)
                return a

        initialization += affect_init(type, var_name, 0)
        position += struct_definitions[type]["size"]
    return initialization

def asm_program(p):
    global double_constants, struct_definitions
    double_constants.clear()

    with open("moule.asm", encoding="utf-8") as f:
        prog_asm = f.read()

    decl_vars = ""
    init_vars = ""

    struct_definitions = get_struct_definitions(p)

    # Handle arguments for main. They are all declared and initialized
    position = 0
    for c in p.children[2].children:
        type      = c.children[0].value
        var_name  = c.children[-1].value
        if type not in (PRIMITIVE_TYPES.keys() | struct_definitions.keys()):
            if raiseWarnings: (print(f"Variable {var_name} declared with invalid type, ignoring it"))
        else:
            # Declaration
            decl_vars += asm_declaration(var_name, type)
            symboltable.declare(var_name, type)
            # Initialization
            init_vars += asm_initialization(var_name, type, position)
            if type in PRIMITIVE_TYPES.keys() :
                position += PRIMITIVE_TYPES[type]
            else:
                position += struct_definitions[type]["size"]
            symboltable.initialize(var_name)

    # Collect all other declarations in the body of the program
    for d in get_declarations(p.children[3]):
        type = d.children[0].value
        var_name = d.children[-1].value
        if type not in (PRIMITIVE_TYPES.keys() | struct_definitions.keys()):
            if raiseWarnings: (print(f"Variable {var_name} declared with invalid type, ignoring it"))
        else:
            if not symboltable.is_declared(var_name):
                decl_vars += asm_declaration(var_name, type)
                symboltable.declare(var_name, type)

    commandes_code = asm_bloc(p.children[3])
    ret_type       = p.children[1].value
    code_ret, typ  = asm_expression(p.children[4])

    if ret_type == "double" and typ == "long":
        code_ret += "\ncvtsi2sd xmm0, rax"
    elif ret_type == "long" and typ == "double":
        code_ret += "\ncvttsd2si rax, xmm0"

    for val, (name, _, _) in double_constants.items():
        binary = struct.unpack('<Q', struct.pack('<d', float(val)))[0]
        decl_vars += f"{name}: dq 0x{binary:016X} ; {val}\n"

    prog_asm = (prog_asm
                .replace("RETOUR",    code_ret)
                .replace("DECL_VARS", decl_vars)
                .replace("INIT_VARS", init_vars)
                .replace("COMMANDE",  commandes_code))

    return prog_asm



if __name__ == "__main__":
    with open("src.c", encoding="utf-8") as f:
        src = f.read()
    raiseWarnings = True
    ast = g.parse(src)
    print(asm_program(ast))
