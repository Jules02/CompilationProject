extern printf, atoi, atof, malloc

section .data

A: dq 0
B: dq 0
C: dq 0
p: dq 0, 0
ptrA: dq 0
buffer: dq 0
sum: dq 0
sub: dq 0

argv: dq 0
fmt_int:db "%d", 10, 0
fmt_double: db "%.12f", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi


mov rbx, [argv]
mov rdi, [rbx + 0]
call atoi
mov [A], rax

mov rbx, [argv]
mov rdi, [rbx + 8]
call atoi
mov [B], rax

mov rbx, [argv]
mov rdi, [rbx + 16]
call atoi
mov [C], rax


mov rax, [p + 0]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

lea rax, [A]

mov [ptrA]+0, rax+0



mov rdi, 8
call malloc

mov [buffer]+0, rax+0

mov rax, [A]
push rax
mov rax, [B]
mov rbx, rax
pop rax
add rax, rbx
mov [sum]+0, rax+0

mov rax, [ptrA]
push rax
mov rax, [C]
mov rbx, rax
pop rax
sub rax, rbx
mov [sub]+0, rax+0

mov rax, [sum]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rax, [sub]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf
mov rax, [sum]
push rax
mov rax, [sub]
mov rbx, rax
pop rax
add rax, rbx

pop rbp
ret


