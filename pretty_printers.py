def pp_declaration(d):
    type_node = d.children[0]
    var = d.children[-1]
    return f"{type_node.value} {var.value}"

def pp_expression(e):
    if e.data in ("var", "number", "double"):
        return f"{e.children[0].value}"
    if e.data == "cast_double":
        exp = e.children[0]
        return f"(double)({pp_expression(exp)})"
    if e.data == "addr_of":
        var = e.children[0]
        return f"&{var.value}"
    if e.data == "dereference":
        var = e.children[0]
        return f"*{var.value}"
    if e.data == "malloc_call":
        return "malloc()"
    if e.data == "struct_attr_use":
        return f"{e.children[0]}.{e.children[1]}"
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
    if "struct_attr_affect" in c.data:
        struct_name = c.children[0]
        attr_name = c.children[1]
        exp = c.children[2]
        return f"{tab}{struct_name}.{attr_name} = {pp_expression(exp)}"
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


def pp_struct_typedef(s):
    tab = "    "
    str_structs = ""
    for struct in s.children:
        decls = struct.children[:-1]
        name = struct.children[-1].value
        str_declarations = ""
        for decl in decls[:-1]:
            str_declarations += tab + pp_declaration(decl) + ";\n"
        str_declarations += tab + pp_declaration(decls[-1]) + ";"
        str_structs +=  f"typedef struct {{\n{str_declarations}\n}} {name};\n\n"
    return str_structs

def pp_bloc(b, indent=0):
    str_commandes = ""
    for com in b.children:
        result = pp_commande(com, indent)
        if result is not None:
            str_commandes += result + "\n"
    return str_commandes

def pp_programme(p, indent=0):
    structs = p.children[0]
    type_node = p.children[1]
    args = p.children[2]
    bloc = p.children[3]
    exp = p.children[4]
    str_args = ""
    if args.data != "vide":
        for arg in args.children[:-1]:
            str_args += pp_declaration(arg) + ", "
        str_args += pp_declaration(args.children[-1])
    return f"{pp_struct_typedef(structs)}{type_node.value} main({str_args}) {{\n{pp_bloc(bloc, indent+1)}    return ({pp_expression(exp)});\n}}"