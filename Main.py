import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# =====================================================================
# 1. LEXER
# =====================================================================
class TokenType:
    INT = "INT"
    IDENT = "IDENT"
    NUMBER = "NUMBER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    SEMI = "SEMI"
    RETURN = "RETURN"
    EOF = "EOF"

class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        if self.current_char == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return Token(TokenType.NUMBER, int(result), self.line, self.col)

    def identifier(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        if result == "int": return Token(TokenType.INT, result, self.line, self.col)
        if result == "return": return Token(TokenType.RETURN, result, self.line, self.col)
        return Token(TokenType.IDENT, result, self.line, self.col)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue
            if self.current_char.isdigit():
                return self.number()
            if self.current_char.isalpha() or self.current_char == '_':
                return self.identifier()
            
            if self.current_char == '+': self.advance(); return Token(TokenType.PLUS, '+', self.line, self.col)
            if self.current_char == '-': self.advance(); return Token(TokenType.MINUS, '-', self.line, self.col)
            if self.current_char == '*': self.advance(); return Token(TokenType.STAR, '*', self.line, self.col)
            if self.current_char == '/': self.advance(); return Token(TokenType.SLASH, '/', self.line, self.col)
            if self.current_char == '(': self.advance(); return Token(TokenType.LPAREN, '(', self.line, self.col)
            if self.current_char == ')': self.advance(); return Token(TokenType.RPAREN, ')', self.line, self.col)
            if self.current_char == '{': self.advance(); return Token(TokenType.LBRACE, '{', self.line, self.col)
            if self.current_char == '}': self.advance(); return Token(TokenType.RBRACE, '}', self.line, self.col)
            if self.current_char == ';': self.advance(); return Token(TokenType.SEMI, ';', self.line, self.col)
            
            raise Exception(f"Illegal character '{self.current_char}' at line {self.line}")
        
        return Token(TokenType.EOF, None, self.line, self.col)

# =====================================================================
# 2. PARSER
# =====================================================================
class ASTNode: pass
class Program(ASTNode):
    def __init__(self, functions): self.functions = functions
class Function(ASTNode):
    def __init__(self, name, body): self.name = name; self.body = body
class Return(ASTNode):
    def __init__(self, expr): self.expr = expr
class Num(ASTNode):
    def __init__(self, value): self.value = value
class BinOp(ASTNode):
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self, msg):
        raise Exception(f"Parser Error: {msg} at line {self.current_token.line}")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Expected {token_type}, found {self.current_token.type}")

    def parse(self):
        functions = []
        while self.current_token.type != TokenType.EOF:
            functions.append(self.function())
        return Program(functions)

    def function(self):
        self.eat(TokenType.INT)
        name = self.current_token.value
        self.eat(TokenType.IDENT)
        self.eat(TokenType.LPAREN)
        self.eat(TokenType.RPAREN)
        body = self.block()
        return Function(name, body)

    def block(self):
        self.eat(TokenType.LBRACE)
        statements = []
        while self.current_token.type != TokenType.RBRACE:
            statements.append(self.statement())
        self.eat(TokenType.RBRACE)
        return statements

    def statement(self):
        if self.current_token.type == TokenType.RETURN:
            self.eat(TokenType.RETURN)
            expr = self.expr()
            self.eat(TokenType.SEMI)
            return Return(expr)
        self.error("Expected statement")

    def expr(self):
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            if self.current_token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
                node = BinOp(node, '+', self.term())
            elif self.current_token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)
                node = BinOp(node, '-', self.term())
        return node

    def term(self):
        node = self.factor()
        while self.current_token.type in (TokenType.STAR, TokenType.SLASH):
            if self.current_token.type == TokenType.STAR:
                self.eat(TokenType.STAR)
                node = BinOp(node, '*', self.factor())
            elif self.current_token.type == TokenType.SLASH:
                self.eat(TokenType.SLASH)
                node = BinOp(node, '/', self.factor())
        return node

    def factor(self):
        if self.current_token.type == TokenType.NUMBER:
            val = self.current_token.value
            self.eat(TokenType.NUMBER)
            return Num(val)
        elif self.current_token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        else:
            self.error("Expected number or '('")

# =====================================================================
# 3. CODE GENERATOR (x86-64 MASM)
# =====================================================================
class CodeGenerator:
    def __init__(self):
        self.asm = []

    def emit(self, line):
        self.asm.append(line)

    def generate(self, program):
        self.emit("; Generated by Clanbuntari Compiler")
        self.emit("option casemap:none")
        self.emit("includelib kernel32.lib")
        self.emit("includelib legacy_stdio_definitions.lib")
        self.emit("includelib msvcrt.lib")
        self.emit("extern printf:proc")
        self.emit("extern ExitProcess:proc")
        self.emit(".data")
        self.emit('msg db "Program exited with code: %d", 10, 0')
        self.emit(".code")
        
        for func in program.functions:
            self.emit(f"\n{func.name} PROC")
            self.emit("    sub rsp, 40")
            
            for stmt in func.body:
                self.generate_statement(stmt)
                
            self.emit("    mov rax, 0")
            self.emit("    add rsp, 40")
            self.emit("    ret")
            self.emit(f"{func.name} ENDP")
        
        self.emit("\nmain_wrapper PROC")
        self.emit("    sub rsp, 40")
        self.emit("    call main")
        self.emit("    mov rcx, rax")
        self.emit("    lea rdx, msg")
        self.emit("    call printf")
        self.emit("    mov rcx, 0")
        self.emit("    call ExitProcess")
        self.emit("main_wrapper ENDP")
        
        self.emit("\nEND")
        return "\n".join(self.asm)

    def generate_statement(self, stmt):
        if isinstance(stmt, Return):
            self.generate_expr(stmt.expr)
            self.emit("    ret")

    def generate_expr(self, node):
        if isinstance(node, Num):
            self.emit(f"    mov rax, {node.value}")
        elif isinstance(node, BinOp):
            self.generate_expr(node.left)
            self.emit("    push rax")
            self.generate_expr(node.right)
            self.emit("    pop rcx")
            
            if node.op == '+': self.emit("    add rcx, rax"); self.emit("    mov rax, rcx")
            elif node.op == '-': self.emit("    sub rcx, rax"); self.emit("    mov rax, rcx")
            elif node.op == '*': self.emit("    imul rcx, rax"); self.emit("    mov rax, rcx")
            elif node.op == '/': 
                self.emit("    mov rdx, 0")
                self.emit("    mov rbx, rcx")
                self.emit("    mov rcx, rax") 
                self.emit("    cqo")
                self.emit("    idiv rcx")
                self.emit("    mov rax, rax")

# =====================================================================
# 4. GUI (Compiler Front-end)
# =====================================================================
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class MiniCompilerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Clanbuntari C++ Compiler (Standalone)")
        self.geometry("900x700")

        self.file_path = ""

        self.lbl_title = ctk.CTkLabel(self, text="Clanbuntari C++ Compiler", font=("Segoe UI", 20, "bold"))
        self.lbl_title.pack(pady=10)

        self.btn_open = ctk.CTkButton(self, text="Select C++ Source File", command=self.load_file)
        self.btn_open.pack(pady=5)

        self.lbl_file = ctk.CTkLabel(self, text="No file selected.", text_color="gray")
        self.lbl_file.pack(pady=5)

        self.btn_compile = ctk.CTkButton(self, text="COMPILE TO EXE", fg_color="green", hover_color="darkgreen", command=self.compile_file)
        self.btn_compile.pack(pady=15)

        self.txt_log = ctk.CTkTextbox(self, font=("Consolas", 12), fg_color="#1e1e1e", text_color="#d4d4d4")
        self.txt_log.pack(fill="both", expand=True, padx=20, pady=10)
        self.txt_log.insert("1.0", "Output will appear here...\n")
        self.txt_log.configure(state="disabled")

    def log(self, text):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", text + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")
        self.update()

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("C++ Files", "*.cpp *.c")])
        if path:
            self.file_path = path
            self.lbl_file.configure(text=path)

    def find_msvc_tools(self):
        vswhere_paths = [
            r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe",
            r"C:\Program Files\Microsoft Visual Studio\Installer\vswhere.exe"
        ]
        
        vswhere = None
        for p in vswhere_paths:
            if os.path.exists(p):
                vswhere = p
                break
                
        if not vswhere:
            return None, None
            
        try:
            cmd = [vswhere, "-latest", "-products", "*", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"]
            res = subprocess.run(cmd, capture_output=True, text=True)
            vs_path = res.stdout.strip()
            if not vs_path: return None, None
            
            vcvars = os.path.join(vs_path, "VC", "Auxiliary", "Build", "vcvars64.bat")
            if not os.path.exists(vcvars):
                return None, None
                
            msvc_root = os.path.join(vs_path, "VC", "Tools", "MSVC")
            versions = [d for d in os.listdir(msvc_root) if os.path.isdir(os.path.join(msvc_root, d))]
            best_ver = sorted(versions)[-1]
            ml64 = os.path.join(msvc_root, best_ver, "bin", "Hostx64", "x64", "ml64.exe")
            link = os.path.join(msvc_root, best_ver, "bin", "Hostx64", "x64", "link.exe")
            
            if os.path.exists(ml64) and os.path.exists(link):
                return vcvars, (ml64, link)
        except Exception:
            pass
            
        return None, None

    def compile_file(self):
        if not self.file_path:
            messagebox.showerror("Error", "Please select a file first.")
            return

        try:
            self.log(f"[*] Lexing {self.file_path}...")
            with open(self.file_path, "r") as f:
                code = f.read()
            lexer = Lexer(code)
            
            self.log("[*] Parsing AST...")
            parser = Parser(lexer)
            ast = parser.parse()

            self.log("[*] Generating x86-64 Assembly...")
            codegen = CodeGenerator()
            asm_output = codegen.generate(ast)

            out_dir = os.path.dirname(self.file_path)
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            asm_path = os.path.join(out_dir, base_name + ".asm")
            obj_path = os.path.join(out_dir, base_name + ".obj")
            exe_path = os.path.join(out_dir, base_name + ".exe")

            with open(asm_path, "w") as f:
                f.write(asm_output)

            self.log(f"[*] Locating MSVC build tools...")
            vcvars, tools = self.find_msvc_tools()
            
            if not vcvars:
                self.log("[-] Error: Could not locate Visual Studio C++ tools.")
                return

            ml64, link = tools
            self.log(f"[+] Found vcvars: {vcvars}")

            # --- ASSEMBLE ---
            self.log("[*] Assembling...")
            
            # We construct the exact cmd.exe string, quoting ONLY the executable and the arguments individually
            # /Fo needs to be right next to the path.
            asm_cmd = f'call "{vcvars}" >nul && "{ml64}" /c /nologo "{asm_path}" /Fo"{obj_path}"'
            
            res_asm = subprocess.run(
                asm_cmd, 
                capture_output=True, text=True, shell=True
            )
            
            if res_asm.returncode != 0:
                self.log("[-] Assembler Error:\n" + res_asm.stdout + res_asm.stderr)
                return
                
            if not os.path.exists(obj_path):
                self.log(f"[-] Error: Assembler claimed success, but {obj_path} was not created.")
                self.log("This usually means the path has weird characters or permission issues.")
                return

            # --- LINK ---
            self.log("[*] Linking...")
            # Added /ENTRY:main_wrapper so the linker knows where the program starts
            link_cmd = f'call "{vcvars}" >nul && "{link}" /nologo /SUBSYSTEM:CONSOLE /ENTRY:main_wrapper "{obj_path}" /OUT:"{exe_path}"'
            
            res_link = subprocess.run(
                link_cmd, 
                capture_output=True, text=True, shell=True
            )
            
            if res_link.returncode != 0:
                self.log("[-] Linker Error:\n" + res_link.stdout + res_link.stderr)
                return

            self.log(f"\n[+] SUCCESS! Executable created at:\n{exe_path}")

        except Exception as e:
            self.log(f"\n[-] COMPILATION ERROR:\n{str(e)}")

if __name__ == "__main__":
    app = MiniCompilerGUI()
    app.mainloop()
