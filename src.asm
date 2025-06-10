extern printf, atoi, atof, malloc

section .data

sum: dq 0

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%.12f", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi


mov rax, 4
push rax
mov rax, 5
mov rbx, rax
pop rax
add rax, rbx
mov   [sum], rax

mov rax, [sum]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rax, [sum]

pop rbp
ret
