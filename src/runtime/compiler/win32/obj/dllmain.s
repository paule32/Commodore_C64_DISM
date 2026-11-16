	.text
	.globl	_DllMain@12
_DllMain@12:
LFB0:
	movl	8(%esp), %eax
	cmpl	$1, %eax
	je	L5
	testl	%eax, %eax
	je	L6
L4:
	movl	$1, %eax
L1:
	ret	$12
L5:
	call	_init_loader
	testl	%eax, %eax
	setne	%al
	movzbl	%al, %eax
	jmp	L1
L6:
	call	__jit_exception_tls_cleanup
	jmp	L4
LFE0:
	.globl	_DllMainCRTStartup@12
_DllMainCRTStartup@12:
LFB1:
	subl	$12, %esp
	movl	24(%esp), %eax
	movl	%eax, 8(%esp)
	movl	20(%esp), %eax
	movl	%eax, 4(%esp)
	movl	16(%esp), %eax
	movl	%eax, (%esp)
	call	_DllMain@12
	subl	$12, %esp
	addl	$12, %esp
	ret	$12
LFE1:
	.section .drectve
	.ascii " -export:\"DllMainCRTStartup@12\""
	.ascii " -export:\"DllMain@12\""
