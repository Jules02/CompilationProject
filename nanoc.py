from lark import Lark

cpt = 0
g = Lark("""
IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9]*/
NUMBER: /[1-9][0-9]*/|"0" 
OPBIN: /[+\-*\/>]/
liste_var:                                                                  -> vide
    | IDENTIFIER ("," IDENTIFIER)*                                          -> vars
expression: IDENTIFIER                                                      -> var
    | expression OPBIN expression                                           -> opbin
    | NUMBER                                                                -> number
commande: IDENTIFIER "=" expression ";"                                     -> affectation
    | "while" "(" expression ")" "{" bloc "}"                               -> while
    | "if" "(" expression ")" "{" bloc "}" ("else" "{" bloc "}")?   -> ite
    | "printf" "(" expression ")" ";"                                       -> print
    | "skip" ";"                                                            -> skip
bloc: (commande)*                                                           -> bloc
program:"main" "(" liste_var ")" "{" commande "return" "("expression")" ";" "}"
%import common.WS
%ignore WS
""", start='commande')

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
    prog_asm = prog_asm.replace("INIT_VARS", init_vars)
    prog_asm = prog_asm.replace("DECL_VARS", decl_vars)
    asm_c = asm_commande(p.children[1])
    prog_asm = prog_asm.replace("COMMANDE", asm_c)
    return prog_asm    

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
        return f"{tab}{var.value} = {pp_expression(exp)}"
    if c.data == "skip":
        return f"{tab}skip"
    if c.data == "print":
        return f"{tab}printf({pp_expression(c.children[0])})"
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
        str_commandes += pp_commande(com, indent) + ";\n"
    return str_commandes

if __name__ == "__main__":
    with open("simple.c") as f:
        src = f.read()
    print(src)
    ast = g.parse(src)
    print(ast)
    print(pp_commande(ast))
    #print(asm_program(ast))
    #print(ast.children[0].type)
    #print(ast.children[0].value)
