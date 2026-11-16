	.text
	.section .rdata,"dr"
LC0:
	.ascii "\12\0"
	.text
	.globl	__jit_print_newline
__jit_print_newline:
LFB0:
	subl	$4, %esp
	movl	$LC0, (%esp)
	call	__jit_print_text
	addl	$4, %esp
	ret
LFE0:
	.globl	_utoa10
_utoa10:
LFB1:
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	subl	$20, %esp
	movl	40(%esp), %ecx
	movl	$0, %edi
	leal	3(%esp), %esi
	movl	$-858993459, %ebx
	.p2align 6
L4:
	movl	%edi, (%esp)
	addl	$1, %edi
	movl	%ecx, %eax
	mull	%ebx
	shrl	$3, %edx
	leal	(%edx,%edx,4), %ebp
	addl	%ebp, %ebp
	movl	%ecx, %eax
	subl	%ebp, %eax
	addl	$48, %eax
	movb	%al, (%esi,%edi)
	movl	%ecx, %eax
	movl	%edx, %ecx
	cmpl	$9, %eax
	ja	L4
	movl	44(%esp), %ebp
	testl	%edi, %edi
	je	L5
	leal	4(%esp), %ebx
	movl	(%esp), %eax
	addl	%ebx, %eax
	movl	%ebp, %ecx
	leal	3(%esp), %ebx
	.p2align 4
L6:
	movzbl	(%eax), %edx
	movb	%dl, (%ecx)
	subl	$1, %eax
	addl	$1, %ecx
	cmpl	%ebx, %eax
	jne	L6
L5:
	movb	$0, 0(%ebp,%edi)
	movl	%edi, %eax
	addl	$20, %esp
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE1:
	.globl	_itoa10
_itoa10:
LFB2:
	pushl	%ebx
	subl	$8, %esp
	movl	16(%esp), %edx
	movl	20(%esp), %eax
	movl	$0, %ebx
	testl	%edx, %edx
	js	L14
L11:
	addl	%ebx, %eax
	movl	%eax, 4(%esp)
	movl	%edx, (%esp)
	call	_utoa10
	addl	%ebx, %eax
	addl	$8, %esp
	popl	%ebx
	ret
L14:
	movb	$45, (%eax)
	negl	%edx
	movl	$1, %ebx
	jmp	L11
LFE2:
	.globl	__jit_print_char
__jit_print_char:
LFB3:
	subl	$24, %esp
	movl	$-11, (%esp)
	call	*_p_GetStdHandle
	subl	$4, %esp
	movl	$0, 16(%esp)
	leal	20(%esp), %edx
	movl	%edx, 12(%esp)
	movl	$1, 8(%esp)
	leal	28(%esp), %ecx
	movl	%ecx, 4(%esp)
	movl	%eax, (%esp)
	call	*_p_WriteFile
	subl	$20, %esp
	addl	$24, %esp
	ret
LFE3:
	.globl	__jit_print_int
__jit_print_int:
LFB5:
	pushl	%esi
	pushl	%ebx
	subl	$40, %esp
	leal	24(%esp), %esi
	movl	%esi, 4(%esp)
	movl	52(%esp), %eax
	movl	%eax, (%esp)
	call	_itoa10
	movl	%eax, %ebx
	movl	$-11, (%esp)
	call	*_p_GetStdHandle
	subl	$4, %esp
	movl	$0, 16(%esp)
	leal	20(%esp), %edx
	movl	%edx, 12(%esp)
	movl	%ebx, 8(%esp)
	movl	%esi, 4(%esp)
	movl	%eax, (%esp)
	call	*_p_WriteFile
	subl	$20, %esp
	addl	$40, %esp
	popl	%ebx
	popl	%esi
	ret
LFE5:
	.section .rdata,"dr"
LC2:
	.ascii "-\0"
LC3:
	.ascii ".\0"
	.text
	.globl	__jit_print_double
__jit_print_double:
LFB4:
	leal	4(%esp), %ecx
	andl	$-8, %esp
	pushl	-4(%ecx)
	pushl	%ebp
	movl	%esp, %ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	pushl	%ecx
	subl	$44, %esp
	fldl	(%ecx)
	fstl	-32(%ebp)
	fldz
	fcomip	%st(1), %st
	fstp	%st(0)
	ja	L26
L20:
	fldl	-32(%ebp)
	cvttsd2sil	-32(%ebp), %ebx
	movl	%ebx, -32(%ebp)
	fildl	-32(%ebp)
	fsubrp	%st, %st(1)
	fstpl	-32(%ebp)
	movl	$-11, (%esp)
	call	*_p_GetStdHandle
	subl	$4, %esp
	movl	%eax, -40(%ebp)
	movl	%ebx, (%esp)
	call	__jit_print_int
	movl	$LC3, (%esp)
	call	__jit_print_text
	movl	$6, %ebx
	leal	-20(%ebp), %edi
	leal	-21(%ebp), %esi
L22:
	flds	LC4
	fmull	-32(%ebp)
	fstpl	-32(%ebp)
	cvttsd2sil	-32(%ebp), %eax
	movl	%eax, -36(%ebp)
	addl	$48, %eax
	movb	%al, -21(%ebp)
	movl	$0, 16(%esp)
	movl	%edi, 12(%esp)
	movl	$1, 8(%esp)
	movl	%esi, 4(%esp)
	movl	-40(%ebp), %eax
	movl	%eax, (%esp)
	call	*_p_WriteFile
	subl	$20, %esp
	fildl	-36(%ebp)
	fsubrl	-32(%ebp)
	fstpl	-32(%ebp)
	subl	$1, %ebx
	jne	L22
	leal	-16(%ebp), %esp
	popl	%ecx
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	leal	-4(%ecx), %esp
	ret
L26:
	movl	$LC2, (%esp)
	call	__jit_print_text
	fldl	-32(%ebp)
	fchs
	fstpl	-32(%ebp)
	jmp	L20
LFE4:
	.section .rdata,"dr"
LC6:
	.ascii "\0"
LC7:
	.ascii "Invalid dynamic string\0"
	.align 4
LC8:
	.ascii "Out of memory in dynstring_copy\0"
	.text
	.globl	__jit_dynstring_copy
__jit_dynstring_copy:
LFB6:
	leal	-32(%esp), %esp
	movl	%esi, 20(%esp)
	movl	%edi, 24(%esp)
	movl	%ebp, 28(%esp)
	movl	36(%esp), %esi
	movl	40(%esp), %edi
	movl	44(%esp), %ebp
	testl	%esi, %esi
	je	L36
	movl	%ebx, 16(%esp)
	cmpl	$1146311762, -12(%esi)
	jne	L37
L30:
	movl	-4(%esi), %ebx
	testl	%edi, %edi
	movl	$1, %eax
	cmovle	%eax, %edi
	testl	%ebp, %ebp
	jle	L34
	cmpl	%ebx, %edi
	jg	L34
	leal	-1(%edi), %eax
	movl	%eax, 12(%esp)
	subl	%eax, %ebx
	cmpl	%ebp, %ebx
	cmovg	%ebp, %ebx
	leal	13(%ebx), %eax
	movl	%eax, (%esp)
	call	__jit_malloc
	movl	%eax, %edi
	testl	%eax, %eax
	je	L38
L33:
	movl	$1146311762, (%edi)
	movl	$0, 4(%edi)
	movl	%ebx, 8(%edi)
	leal	12(%edi), %ebp
	movl	%ebx, 8(%esp)
	movl	12(%esp), %eax
	addl	%eax, %esi
	movl	%esi, 4(%esp)
	movl	%ebp, (%esp)
	call	__jit_memcpy
	movb	$0, 12(%edi,%ebx)
	movl	16(%esp), %ebx
	jmp	L27
L36:
	movl	$LC6, (%esp)
	call	__jit_dynstring_from_cstr
	movl	%eax, %ebp
	jmp	L27
L37:
	movl	$LC7, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	jmp	L30
L34:
	movl	$LC6, (%esp)
	call	__jit_dynstring_from_cstr
	movl	%eax, %ebp
	movl	16(%esp), %ebx
L27:
	movl	%ebp, %eax
	movl	20(%esp), %esi
	movl	24(%esp), %edi
	movl	28(%esp), %ebp
	leal	32(%esp), %esp
	ret
L38:
	movl	$LC8, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	jmp	L33
LFE6:
	.section .rdata,"dr"
LC9:
	.ascii "Invalid search string\0"
LC10:
	.ascii "Invalid source string\0"
	.text
	.globl	__jit_dynstring_pos
__jit_dynstring_pos:
LFB7:
	leal	-32(%esp), %esp
	movl	%esi, 20(%esp)
	movl	%edi, 24(%esp)
	movl	36(%esp), %esi
	movl	40(%esp), %edi
	testl	%esi, %esi
	je	L45
	testl	%edi, %edi
	je	L45
	movl	%ebp, 28(%esp)
	cmpl	$1146311762, -12(%esi)
	jne	L52
L43:
	cmpl	$1146311762, -12(%edi)
	jne	L53
L44:
	movl	-4(%esi), %ebp
	movl	-4(%edi), %eax
	cmpl	%eax, %ebp
	jg	L50
	testl	%ebp, %ebp
	jle	L51
	movl	%ebx, 16(%esp)
	subl	%ebp, %eax
	addl	$1, %eax
	movl	%eax, 12(%esp)
	movl	$0, %ebx
L47:
	movl	%ebp, 8(%esp)
	movl	%esi, 4(%esp)
	leal	(%edi,%ebx), %eax
	movl	%eax, (%esp)
	call	__jit_memcmp
	testl	%eax, %eax
	je	L54
	addl	$1, %ebx
	movl	12(%esp), %eax
	cmpl	%eax, %ebx
	jne	L47
	movl	16(%esp), %ebx
	movl	28(%esp), %ebp
	jmp	L45
L50:
	movl	28(%esp), %ebp
L45:
	movl	$0, %eax
L39:
	movl	20(%esp), %esi
	movl	24(%esp), %edi
	leal	32(%esp), %esp
	ret
L51:
	movl	28(%esp), %ebp
	jmp	L45
L52:
	movl	$LC9, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	jmp	L43
L53:
	movl	$LC10, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	jmp	L44
L54:
	leal	1(%ebx), %eax
	movl	16(%esp), %ebx
	movl	28(%esp), %ebp
	jmp	L39
LFE7:
	.section .rdata,"dr"
LC11:
	.ascii "0x%08X\0"
	.text
	.globl	__jit_print_variant
__jit_print_variant:
LFB8:
	pushl	%ebp
	movl	%esp, %ebp
	andl	$-8, %esp
	subl	$28, %esp
	movl	8(%ebp), %eax
	testl	%eax, %eax
	je	L55
	cmpl	$6, (%eax)
	ja	L55
	movl	(%eax), %edx
	jmp	*L58(,%edx,4)
	.section .rdata,"dr"
	.align 4
L58:
	.long	L55
	.long	L63
	.long	L62
	.long	L61
	.long	L60
	.long	L59
	.long	L57
	.text
L63:
	movl	4(%eax), %eax
	movl	%eax, (%esp)
	call	__jit_print_int
	jmp	L55
L62:
	cmpl	$0, 4(%eax)
	setne	%al
	movzbl	%al, %eax
	movl	%eax, (%esp)
	call	__jit_print_int
	jmp	L55
L61:
	movl	4(%eax), %eax
	testl	%eax, %eax
	je	L55
	movzbl	(%eax), %eax
	movl	%eax, (%esp)
	call	__jit_print_char
	jmp	L55
L60:
	movl	4(%eax), %eax
	movl	%eax, (%esp)
	call	__jit_print_text
	jmp	L55
L59:
	movl	8(%eax), %ecx
	movl	4(%eax), %eax
	movl	%eax, 20(%esp)
	movl	%ecx, 24(%esp)
	movl	$8, 8(%esp)
	leal	20(%esp), %eax
	movl	%eax, 4(%esp)
	leal	12(%esp), %eax
	movl	%eax, (%esp)
	call	__jit_memcpy
	movsd	12(%esp), %xmm0
	movsd	%xmm0, (%esp)
	call	__jit_print_double
	jmp	L55
L57:
	movl	4(%eax), %eax
	movl	%eax, 4(%esp)
	movl	$LC11, (%esp)
	call	__jit_printf
L55:
	leave
	ret
LFE8:
	.globl	__jit_print_variant_array
__jit_print_variant_array:
LFB9:
	leal	-16(%esp), %esp
	movl	%ebx, 4(%esp)
	movl	%edi, 12(%esp)
	movl	20(%esp), %ebx
	movl	24(%esp), %edi
	testl	%ebx, %ebx
	je	L65
	testl	%edi, %edi
	js	L65
	movl	%esi, 8(%esp)
	movl	$0, %esi
L67:
	movl	%ebx, (%esp)
	call	__jit_print_variant
	addl	$1, %esi
	addl	$12, %ebx
	cmpl	%esi, %edi
	jge	L67
	movl	8(%esp), %esi
L65:
	movl	4(%esp), %ebx
	movl	12(%esp), %edi
	leal	16(%esp), %esp
	ret
LFE9:
	.section .rdata,"dr"
	.align 4
LC4:
	.long	1092616192
	.section .drectve
	.ascii " -export:\"_jit_print_variant_array\""
	.ascii " -export:\"_jit_print_variant\""
	.ascii " -export:\"_jit_dynstring_pos\""
	.ascii " -export:\"_jit_dynstring_copy\""
	.ascii " -export:\"_jit_print_double\""
	.ascii " -export:\"_jit_print_int\""
	.ascii " -export:\"_jit_print_char\""
	.ascii " -export:\"_jit_print_newline\""
