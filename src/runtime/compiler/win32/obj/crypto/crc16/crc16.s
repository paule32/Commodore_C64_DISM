	.text
	.globl	_crc16_init
_crc16_init:
LFB0:
	movl	4(%esp), %eax
	movw	$-1, (%eax)
	ret
LFE0:
	.globl	_crc16_update
_crc16_update:
LFB1:
	leal	-16(%esp), %esp
	movl	%ebx, (%esp)
	movl	%esi, 4(%esp)
	movl	%edi, 8(%esp)
	movl	20(%esp), %esi
	movl	24(%esp), %ebx
	movl	28(%esp), %edi
	testl	%edi, %edi
	je	L2
	movl	%ebp, 12(%esp)
	addl	%ebx, %edi
L7:
	addl	$1, %ebx
	movzbl	-1(%ebx), %eax
	sall	$8, %eax
	xorw	(%esi), %ax
	movl	$8, %ecx
	.p2align 5
L6:
	leal	(%eax,%eax), %edx
	xorw	$4129, %dx
	leal	(%eax,%eax), %ebp
	testw	%ax, %ax
	movl	%edx, %eax
	cmovns	%ebp, %eax
	subl	$1, %ecx
	jne	L6
	movw	%ax, (%esi)
	cmpl	%ebx, %edi
	jne	L7
	movl	12(%esp), %ebp
L2:
	movl	(%esp), %ebx
	movl	4(%esp), %esi
	movl	8(%esp), %edi
	leal	16(%esp), %esp
	ret
LFE1:
	.globl	_crc16_final
_crc16_final:
LFB2:
	movl	4(%esp), %eax
	movzwl	(%eax), %eax
	ret
LFE2:
	.globl	_crc16_calc
_crc16_calc:
LFB3:
	subl	$16, %esp
	movw	$-1, 14(%esp)
	movl	24(%esp), %eax
	movl	%eax, 8(%esp)
	movl	20(%esp), %eax
	movl	%eax, 4(%esp)
	leal	14(%esp), %eax
	movl	%eax, (%esp)
	call	_crc16_update
	movzwl	14(%esp), %eax
	addl	$16, %esp
	ret
LFE3:
	.section .rdata,"dr"
LC0:
	.ascii "%04x\0"
	.text
	.globl	__jit_crc16
__jit_crc16:
LFB4:
	pushl	%esi
	pushl	%ebx
	subl	$20, %esp
	movw	$-1, 18(%esp)
	movl	36(%esp), %eax
	movl	%eax, 8(%esp)
	movl	32(%esp), %eax
	movl	%eax, 4(%esp)
	leal	18(%esp), %eax
	movl	%eax, (%esp)
	call	_crc16_update
	movzwl	18(%esp), %esi
	movl	$5, (%esp)
	call	__jit_malloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L14
	movzwl	%si, %esi
	movl	%esi, 12(%esp)
	movl	$LC0, 8(%esp)
	movl	$5, 4(%esp)
	movl	%eax, (%esp)
	call	__jit_snprintf
L14:
	movl	%ebx, %eax
	addl	$20, %esp
	popl	%ebx
	popl	%esi
	ret
LFE4:
	.section .drectve
	.ascii " -export:\"_jit_crc16\""
	.ascii " -export:\"crc16_update\""
	.ascii " -export:\"crc16_init\""
