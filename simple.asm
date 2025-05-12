extern printf, atoi

section .data


argv: dq 0
fmt_int:db "%d", 10, 0
fmt_float: db "%.6f", 10, 0
fmt_double: db "%.12f", 10, 0

global main
section .text

main:
push rbp
mov [argv], rsi


movss xmm0, [float_0]
mov [x], rax
 movsd xmm0, [double_0]
mov [y], rax
 mov rax, 42
mov [z], rax
 cvtsi2ss xmm0, rax
mov [f], rax
 cvtsi2sd xmm0, rax
mov [i], rax
 mov rax, [x] 
push rax
mov rax, [y]
mov rbx, rax
add rax, rbx
mov [result], rax
 mov rax, [result]
mov rsi, fmt
mov rdi, rax
xor rax, rax
call printf

mov rax, [result]
mov rdi, fmt_int
mov rsi, rax
xor rax, rax
call printf

pop rbp
ret


