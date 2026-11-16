	.text
	.globl	_crc32_init
_crc32_init:
LFB1:
	leal	-8(%esp), %esp
	cmpl	$0, __ZL17crc32_initialized
	je	L12
L3:
	movl	12(%esp), %eax
	movl	$-1, (%eax)
	leal	8(%esp), %esp
	ret
L12:
	movl	%ebx, (%esp)
	movl	%esi, 4(%esp)
	movl	$0, %esi
L2:
	movl	%esi, %eax
	movl	$8, %ecx
	.p2align 5
L6:
	movl	%eax, %edx
	shrl	%edx
	xorl	$-306674912, %edx
	movl	%eax, %ebx
	shrl	%ebx
	testb	$1, %al
	movl	%edx, %eax
	cmove	%ebx, %eax
	subl	$1, %ecx
	jne	L6
	movl	%eax, __ZL11crc32_table(,%esi,4)
	addl	$1, %esi
	cmpl	$256, %esi
	jne	L2
	movl	$1, __ZL17crc32_initialized
	movl	(%esp), %ebx
	movl	4(%esp), %esi
	jmp	L3
LFE1:
	.globl	_crc32_update
_crc32_update:
LFB2:
	pushl	%esi
	pushl	%ebx
	movl	12(%esp), %ebx
	movl	16(%esp), %edx
	movl	20(%esp), %esi
	testl	%esi, %esi
	je	L13
	addl	%edx, %esi
	.p2align 5
L15:
	movl	(%ebx), %eax
	addl	$1, %edx
	movl	%eax, %ecx
	xorb	-1(%edx), %cl
	movzbl	%cl, %ecx
	shrl	$8, %eax
	xorl	__ZL11crc32_table(,%ecx,4), %eax
	movl	%eax, (%ebx)
	cmpl	%edx, %esi
	jne	L15
L13:
	popl	%ebx
	popl	%esi
	ret
LFE2:
	.globl	_crc32_final
_crc32_final:
LFB3:
	movl	4(%esp), %eax
	movl	(%eax), %eax
	notl	%eax
	ret
LFE3:
	.globl	_crc32_calc
_crc32_calc:
LFB4:
	pushl	%ebx
	subl	$16, %esp
	leal	12(%esp), %ebx
	movl	%ebx, (%esp)
	call	_crc32_init
	movl	28(%esp), %eax
	movl	%eax, 8(%esp)
	movl	24(%esp), %eax
	movl	%eax, 4(%esp)
	movl	%ebx, (%esp)
	call	_crc32_update
	movl	12(%esp), %eax
	notl	%eax
	addl	$16, %esp
	popl	%ebx
	ret
LFE4:
	.section .rdata,"dr"
LC0:
	.ascii "%08x\0"
	.text
	.globl	__jit_crc32
__jit_crc32:
LFB5:
	pushl	%esi
	pushl	%ebx
	subl	$20, %esp
	movl	36(%esp), %eax
	movl	%eax, 4(%esp)
	movl	32(%esp), %eax
	movl	%eax, (%esp)
	call	_crc32_calc
	movl	%eax, %esi
	movl	$9, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L21
	movl	%esi, 12(%esp)
	movl	$0, 16(%esp)
	movl	$LC0, 8(%esp)
	movl	$9, 4(%esp)
	movl	%eax, (%esp)
	call	__jit_snprintf
L21:
	movl	%ebx, %eax
	addl	$20, %esp
	popl	%ebx
	popl	%esi
	ret
LFE5:
.lcomm __ZL17crc32_initialized,4,4
.lcomm __ZL11crc32_table,1024,32
	.section .drectve
	.ascii " -export:\"_jit_crc32\""
	.ascii " -export:\"crc32_update\""
	.ascii " -export:\"crc32_init\""
