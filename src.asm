extern printf, atoi, atof, malloc

section .data

num: dq 0
ptrValHolder: dq 0
ptrNum: dq 0

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%.12f", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi




mov rax, 12345
mov   [num], rax


lea rax, [num]

mov   [ptrNum], rax

mov rax, [num]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rbx, [ptrNum]
mov rax, [rbx]
mov   [ptrValHolder], rax

mov rax, [ptrValHolder]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rax, 0

pop rbp
ret
