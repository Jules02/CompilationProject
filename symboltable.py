class SymbolTable:
    def __init__(self):
        self.table = {}

    def declare(self, name: str, var_type: str):
        if name in self.table:
            raise ValueError(f"Variable '{name}' is already declared.")
        self.table[name] = {"type": var_type, "initialized": False}

    def initialize(self, name: str):
        if name not in self.table:
            raise ValueError(f"Variable '{name}' is not declared.")
        self.table[name]["initialized"] = True

    def is_declared(self, name: str) -> bool:
        return name in self.table

    def is_initialized(self, name: str) -> bool:
        if name not in self.table:
            raise ValueError(f"Variable '{name}' is not declared.")
        return self.table[name]["initialized"]

    def get_type(self, name: str) -> str:
        if name not in self.table:
            raise ValueError(f"Variable '{name}' is not declared.")
        return self.table[name]["type"]