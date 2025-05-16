from lark import Lark
import struct

cpt = 0
var_types = {}
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
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
%import common.WS
%ignore WS
""", start='program')

def get_vars_expression(e):
    pass

def get_vars_commande(c):
    pass

double_constants = {}

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx', '*': 'imul rax, rbx', '/': 'cqo\nidiv rbx'}
op2asm_double = {'+' : 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1', '*': 'mulsd xmm0, xmm1', '/': 'divsd xmm0, xmm1'}
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

def asm_commande(c):
    global cpt, var_types
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
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
    if c.data == "ite":
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


def asm_program(p):
    global double_constants, var_types
    double_constants.clear()
    var_types.clear()
    with open("moule.asm", encoding="utf-8") as f:
        prog_asm = f.read()
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
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    return f"{pp_expression(e_left)} {e_op.value} {pp_expression(e_right)}"
def pp_commande(c):
    if c.data == "affectation": 
        var = c.children[0]
        exp = c.children[1]
        return f"{var.value} = {pp_expression(exp)}"
    if c.data == "skip": return "skip"
    if c.data == "print": return f"printf({pp_expression(c.children[0])})"
    if c.data == "while":
        exp = c.children[0]
        body = c.children[1]
        return f"while ( {pp_expression(exp)} ) {{{pp_commande(body)}}}"
    if c.data == "sequence":
        d = c.children[0]
        tail = c.children[1]
        return f"{pp_commande(d)} ; {pp_commande(tail)}"
if __name__ == "__main__":
    with open("simple.c", encoding="utf-8") as f:
        src = f.read()
    ast = g.parse(src)
    print(asm_program(ast))
