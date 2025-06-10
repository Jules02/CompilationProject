extern printf, atoi, atof, malloc

section .data

A: dq 0
B: dq 0
C: dq 0
sum: dq 0
p: dq 0, 0
ptrA: dq 0
buffer: dq 0
LC0: dq 0x4000000000000000 ; 2.0

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%.12f", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi


mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [A], rax

mov rbx, [argv]
mov rdi, [rbx + 16]
call atoi
mov [B], rax

mov rbx, [argv]
mov rdi, [rbx + 24]
call atoi
mov [C], rax

mov rax, [A]
push rax
mov rax, [C]
mov rbx, rax
pop rax
add rax, rbx
mov   [sum], rax

mov rax, [sum]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rax, [A]
push rax
mov rax, [B]
mov rbx, rax
pop rax
sub rax, rbx
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

mov rax, [p + 0]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
movsd xmm0, [p + 8]
mov rdi, fmt_double
mov rax, 1
call printf
mov rax, 4
mov [p], rax
movsd xmm0, [LC0]

movsd [p+8], xmm0
mov rax, [p + 0]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
movsd xmm0, [p + 8]
mov rdi, fmt_double
mov rax, 1
call printf

lea rax, [A]

mov   [ptrA], rax

mov rax, [ptrA]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rbx, [ptrA]
mov rax, [rbx]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

mov rdi, 8
call malloc
mov   [buffer], rax

lea rax, [A]

mov   [buffer], rax

mov rax, [buffer]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rax, [sum]

pop rbp
ret
