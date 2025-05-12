from lark import Lark

cpt = 0
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\-*\/>]/
FLOAT: /[0-9]*\.[0-9]+/
DOUBLE: /[0-9]*\.[0-9]+([eE][+-]?[0-9]+)?/
liste_var:                            -> vide
    | IDENTIFIER ("," IDENTIFIER)*    -> vars
expression: IDENTIFIER            -> var
    | expression OPBIN expression -> opbin
    | NUMBER                      -> number
    | FLOAT                       -> float
    | DOUBLE                      -> double
    |"(" "float" ")" expression     -> cast_float
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

# Floating-point values cannot be used as immediate operands; 
# they must be loaded from memory into xmm.
float_constants = {}
double_constants = {}

op2asm = {'+' : 'add rax, rbx', '-': 'sub rax, rbx'}
op2asm_float = {'+' : 'addss xmm0, xmm1', '-': 'subss xmm0, xmm1'}
op2asm_double = {'+' : 'addsd xmm0, xmm1', '-': 'subsd xmm0, xmm1'}
def asm_expression(e):
    global float_constants, double_constants
    if e.data == "var": return f"mov rax, [{e.children[0].value}]"
    if e.data == "number": return f"mov rax, {e.children[0].value}"
    if e.data == "float":
        val = e.children[0].value
        const_name = f"float_{len(float_constants)}"
        float_constants[const_name] = val
        return f"movss xmm0, [{const_name}]"  
    if e.data == "double":
        val = e.children[0].value
        const_name = f"double_{len(double_constants)}"
        double_constants[const_name] = val
        return f"movsd xmm0, [{const_name}]"
    if e.data == "cast_float": return "cvtsi2ss xmm0, rax"
    if e.data == "cast_double": return "cvtsi2sd xmm0, rax"
    e_left = e.children[0]
    e_op = e.children[1]
    e_right = e.children[2]
    asm_left = asm_expression(e_left)
    asm_right = asm_expression(e_right)
    return f"""{asm_left} 
push rax
{asm_right}
mov rbx, rax
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
    global float_constants, double_constants
    float_constants.clear()
    double_constants.clear()
    with open("moule.asm", encoding="utf-8") as f:
        prog_asm = f.read()
    ret = asm_expression(p.children[2])
    prog_asm = prog_asm.replace("RETOUR", ret)
    init_vars = ""
    decl_vars = ""
    for i, c in enumerate(p.children[0].children):
        init_vars += f"""mov rbx, [argv]
mov rdi, [rbx + {(i+1)*8}]
call atoi
mov [{c.value}], rax
"""
        decl_vars += f"{c.value}: dq 0\n"
        
    for name, value in float_constants.items():
        decl_vars += f"{name}: dd {value}\n"
    
    for name, value in double_constants.items():
        decl_vars += f"{name}: dq {value}\n"
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    asm_c = asm_commande(p.children[1])
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
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
    #print(pp_commande(ast))
#print(ast.children)
#print(ast.children[0].type)
#print(ast.children[0].value)
