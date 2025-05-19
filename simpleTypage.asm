extern printf, atoi, atof

section .data

X: dq 0
Y: dq 0
Z: dq 0
double_0: dq 0x3FD3333333333333 ; 3.0e-1

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
mov [X], rax
mov rbx, [argv]
mov rdi, [rbx + 16]
call atof
movsd [Y], xmm0
mov rbx, [argv]
mov rdi, [rbx + 24]
call atoi
mov [Z], rax

mov rax, 10
mov [X], rax
movsd xmm0, [double_1]
movsd [Y], xmm0
mov rax, [X]
cvtsi2sd xmm1, rax
movsd xmm0, [Y]
addsd xmm0, xmm1
mov [Z], rax

mov rax, [Z]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf


pop rbp
ret


