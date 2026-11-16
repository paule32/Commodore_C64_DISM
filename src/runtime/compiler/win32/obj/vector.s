	.text
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIiEC2Ev
__ZNSt6vectorIiEC2Ev:
LFB7:
	movl	$0, (%ecx)
	movl	$0, 4(%ecx)
	movl	$0, 8(%ecx)
	ret
LFE7:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIiEC1Ev
__ZNSt6vectorIiEC1Ev:
LFB8:
	movl	$0, (%ecx)
	movl	$0, 4(%ecx)
	movl	$0, 8(%ecx)
	ret
LFE8:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIiED2Ev
__ZNSt6vectorIiED2Ev:
LFB10:
	subl	$8, %esp
	movl	%ecx, %eax
	leal	7(%esp), %ecx
	movl	(%eax), %eax
	movl	%eax, (%esp)
	call	__ZNSt9AllocatorIiE4freeEPi
	subl	$4, %esp
	addl	$8, %esp
	ret
LFE10:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIiED1Ev
__ZNSt6vectorIiED1Ev:
LFB11:
	subl	$8, %esp
	movl	%ecx, %eax
	leal	7(%esp), %ecx
	movl	(%eax), %eax
	movl	%eax, (%esp)
	call	__ZNSt9AllocatorIiE4freeEPi
	subl	$4, %esp
	addl	$8, %esp
	ret
LFE11:
	.section	.text
	.align 2
	.globl	__ZNKSt6vectorIiE4sizeEv
__ZNKSt6vectorIiE4sizeEv:
LFB12:
	movl	4(%ecx), %eax
	ret
LFE12:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIiEixEj
__ZNSt6vectorIiEixEj:
LFB13:
	movl	(%ecx), %eax
	movl	4(%esp), %edx
	leal	(%eax,%edx,4), %eax
	ret	$4
LFE13:
	.section	.text
	.align 2
	.globl	__ZNKSt6vectorIiEixEj
__ZNKSt6vectorIiEixEj:
LFB14:
	movl	(%ecx), %eax
	movl	4(%esp), %edx
	leal	(%eax,%edx,4), %eax
	ret	$4
LFE14:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIiE9push_backERKi
__ZNSt6vectorIiE9push_backERKi:
LFB15:
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	movl	%ecx, %ebx
	movl	8(%ecx), %eax
	cmpl	%eax, 4(%ecx)
	jb	L11
	leal	(%eax,%eax), %esi
	testl	%eax, %eax
	movl	$4, %eax
	cmove	%eax, %esi
	leal	11(%esp), %ecx
	movl	%esi, 4(%esp)
	movl	(%ebx), %eax
	movl	%eax, (%esp)
	call	__ZNSt9AllocatorIiE7reallocEPij
	subl	$8, %esp
	movl	%eax, (%ebx)
	movl	%esi, 8(%ebx)
L11:
	movl	24(%esp), %eax
	movl	(%eax), %ecx
	movl	(%ebx), %edx
	movl	4(%ebx), %eax
	leal	1(%eax), %esi
	movl	%esi, 4(%ebx)
	movl	%ecx, (%edx,%eax,4)
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	ret	$4
LFE15:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIcEC2Ev
__ZNSt6vectorIcEC2Ev:
LFB17:
	movl	$0, (%ecx)
	movl	$0, 4(%ecx)
	movl	$0, 8(%ecx)
	ret
LFE17:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIcEC1Ev
__ZNSt6vectorIcEC1Ev:
LFB18:
	movl	$0, (%ecx)
	movl	$0, 4(%ecx)
	movl	$0, 8(%ecx)
	ret
LFE18:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIcED2Ev
__ZNSt6vectorIcED2Ev:
LFB20:
	subl	$8, %esp
	movl	%ecx, %eax
	leal	7(%esp), %ecx
	movl	(%eax), %eax
	movl	%eax, (%esp)
	call	__ZNSt9AllocatorIcE4freeEPc
	subl	$4, %esp
	addl	$8, %esp
	ret
LFE20:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIcED1Ev
__ZNSt6vectorIcED1Ev:
LFB21:
	subl	$8, %esp
	movl	%ecx, %eax
	leal	7(%esp), %ecx
	movl	(%eax), %eax
	movl	%eax, (%esp)
	call	__ZNSt9AllocatorIcE4freeEPc
	subl	$4, %esp
	addl	$8, %esp
	ret
LFE21:
	.section	.text
	.align 2
	.globl	__ZNKSt6vectorIcE4sizeEv
__ZNKSt6vectorIcE4sizeEv:
LFB22:
	movl	4(%ecx), %eax
	ret
LFE22:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIcEixEj
__ZNSt6vectorIcEixEj:
LFB23:
	movl	(%ecx), %eax
	addl	4(%esp), %eax
	ret	$4
LFE23:
	.section	.text
	.align 2
	.globl	__ZNKSt6vectorIcEixEj
__ZNKSt6vectorIcEixEj:
LFB24:
	movl	(%ecx), %eax
	addl	4(%esp), %eax
	ret	$4
LFE24:
	.section	.text
	.align 2
	.globl	__ZNSt6vectorIcE9push_backERKc
__ZNSt6vectorIcE9push_backERKc:
LFB25:
	pushl	%esi
	pushl	%ebx
	subl	$12, %esp
	movl	%ecx, %ebx
	movl	8(%ecx), %eax
	cmpl	%eax, 4(%ecx)
	jb	L25
	leal	(%eax,%eax), %esi
	testl	%eax, %eax
	movl	$4, %eax
	cmove	%eax, %esi
	leal	11(%esp), %ecx
	movl	%esi, 4(%esp)
	movl	(%ebx), %eax
	movl	%eax, (%esp)
	call	__ZNSt9AllocatorIcE7reallocEPcj
	subl	$8, %esp
	movl	%eax, (%ebx)
	movl	%esi, 8(%ebx)
L25:
	movl	24(%esp), %eax
	movzbl	(%eax), %ecx
	movl	(%ebx), %edx
	movl	4(%ebx), %eax
	leal	1(%eax), %esi
	movl	%esi, 4(%ebx)
	movb	%cl, (%edx,%eax)
	addl	$12, %esp
	popl	%ebx
	popl	%esi
	ret	$4
LFE25:
