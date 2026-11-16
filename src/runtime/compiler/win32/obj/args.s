	.text
__ZL21free_argument_storagev:
LFB1:
	subl	$4, %esp
	movl	__ZL17g_argument_vector, %eax
	testl	%eax, %eax
	je	L2
	movl	%eax, (%esp)
	call	__jit_free
	movl	$0, __ZL17g_argument_vector
L2:
	movl	__ZL18g_argument_storage, %eax
	testl	%eax, %eax
	je	L3
	movl	%eax, (%esp)
	call	__jit_free
	movl	$0, __ZL18g_argument_storage
L3:
	movl	$0, __ZL16g_argument_count
	movl	$0, __ZL16g_argument_ready
	addl	$4, %esp
	ret
LFE1:
	.globl	__jit_args_init
__jit_args_init:
LFB3:
	leal	-36(%esp), %esp
	movl	%esi, 24(%esp)
	movl	__ZL16g_argument_ready, %esi
	testl	%esi, %esi
	je	L54
	movl	$1, %esi
L5:
	movl	%esi, %eax
	movl	24(%esp), %esi
	leal	36(%esp), %esp
	ret
L54:
	movl	%ebx, 20(%esp)
	movl	%edi, 28(%esp)
	call	__ZL21free_argument_storagev
	call	_GetCommandLineA@0
	movl	%eax, %ebx
	testl	%eax, %eax
	movl	$__ZL14g_empty_string, %eax
	cmove	%eax, %ebx
	movl	%ebx, (%esp)
	call	__jit_strlen
	movl	%eax, %edi
	leal	1(%eax), %eax
	movl	%eax, (%esp)
	call	__jit_malloc
	movl	%eax, __ZL18g_argument_storage
	testl	%eax, %eax
	je	L53
	leal	8(,%edi,4), %eax
	movl	%eax, (%esp)
	call	__jit_malloc
	movl	%eax, %edi
	movl	%eax, __ZL17g_argument_vector
	testl	%eax, %eax
	je	L55
	cmpb	$0, (%ebx)
	je	L35
	movl	%ebp, 32(%esp)
	movl	__ZL18g_argument_storage, %ebp
	movl	%esi, %eax
	movl	%ebx, %edx
	movl	%esi, %ebx
	movl	%edi, %esi
	jmp	L11
L55:
	call	__ZL21free_argument_storagev
	movl	20(%esp), %ebx
	movl	28(%esp), %edi
	jmp	L5
L14:
	cmpb	$92, %cl
	je	L56
	cmpb	$34, %cl
	je	L57
	addl	$1, %edx
	movb	%cl, 0(%ebp)
	leal	1(%ebp), %ebp
L20:
	movzbl	(%edx), %ecx
	testb	%cl, %cl
	je	L58
L28:
	testl	%edi, %edi
	jne	L14
	cmpb	$32, %cl
	je	L37
	cmpb	$9, %cl
	jne	L14
L37:
	movl	8(%esp), %esi
	movl	12(%esp), %eax
	movl	16(%esp), %ebx
	movl	%ebp, %ecx
	jmp	L13
L56:
	movzbl	(%edx), %eax
	cmpb	$92, %al
	jne	L16
	movl	%edx, %eax
	.p2align 4
L17:
	movl	%eax, %ebx
	addl	$1, %eax
	movzbl	(%eax), %ecx
	cmpb	$92, %cl
	je	L17
	movl	%ebx, 4(%esp)
	movl	$1, %esi
	subl	%edx, %esi
	movl	%esi, %ebx
	movl	4(%esp), %esi
	addl	%esi, %ebx
	cmpb	$34, %cl
	je	L18
	testl	%ebx, %ebx
	je	L59
	leal	0(%ebp,%ebx), %ecx
	movl	%ebp, %edx
	.p2align 4
L25:
	addl	$1, %edx
	movb	$92, -1(%edx)
	cmpl	%ecx, %edx
	jne	L25
	addl	%ebx, %ebp
	movl	%eax, %edx
	jmp	L20
L59:
	movl	%eax, %edx
	jmp	L20
L18:
	movl	%ebx, %esi
	shrl	%esi
	movl	%esi, %ecx
	je	L38
	addl	%ebp, %esi
	movl	%ebp, %edx
	.p2align 4
L22:
	addl	$1, %edx
	movb	$92, -1(%edx)
	cmpl	%esi, %edx
	jne	L22
	movl	%ecx, %esi
	addl	%ebp, %esi
L21:
	testb	$1, %bl
	je	L23
	leal	1(%esi), %ebp
	movb	$34, (%esi)
	movl	4(%esp), %edx
	addl	$2, %edx
	jmp	L20
L38:
	movl	%ebp, %esi
	jmp	L21
L61:
	leal	1(%esi), %ebp
	movb	$34, (%esi)
	leal	2(%eax), %edx
	jmp	L20
L57:
	testl	%edi, %edi
	je	L27
	cmpb	$34, 1(%edx)
	je	L60
L27:
	addl	$1, %edx
	xorl	$1, %edi
	jmp	L20
L60:
	movb	$34, 0(%ebp)
	addl	$2, %edx
	leal	1(%ebp), %ebp
	jmp	L20
L58:
	movl	8(%esp), %esi
	movl	12(%esp), %eax
	movl	16(%esp), %ebx
	movl	%ebp, %ecx
L13:
	leal	1(%ecx), %ebp
	movb	$0, (%ecx)
	movzbl	(%edx), %ecx
	cmpb	$32, %cl
	je	L46
	cmpb	$9, %cl
	jne	L29
	.p2align 4
L46:
	addl	$1, %edx
	movzbl	(%edx), %ecx
	cmpb	$32, %cl
	je	L46
	cmpb	$9, %cl
	je	L46
L29:
	cmpb	$0, (%edx)
	je	L49
L11:
	movzbl	(%edx), %ecx
	cmpb	$32, %cl
	je	L45
	cmpb	$9, %cl
	jne	L32
	.p2align 4
L45:
	addl	$1, %edx
	movzbl	(%edx), %ecx
	cmpb	$32, %cl
	je	L45
	cmpb	$9, %cl
	je	L45
L32:
	testb	%cl, %cl
	je	L47
	movl	%ebp, (%esi,%eax,4)
	addl	$1, %eax
	movzbl	(%edx), %ecx
	testb	%cl, %cl
	je	L36
	movl	%ebx, %edi
	movl	%esi, 8(%esp)
	movl	%eax, 12(%esp)
	movl	%ebx, 16(%esp)
	jmp	L28
L36:
	movl	%ebp, %ecx
	jmp	L13
L35:
	movl	%esi, %eax
	jmp	L10
L47:
	movl	%esi, %edi
	movl	32(%esp), %ebp
L10:
	movl	$0, (%edi,%eax,4)
	movl	%eax, __ZL16g_argument_count
	movl	$1, __ZL16g_argument_ready
	movl	$1, %esi
	movl	20(%esp), %ebx
	movl	28(%esp), %edi
	jmp	L5
L49:
	movl	%esi, %edi
	movl	32(%esp), %ebp
	jmp	L10
L16:
	cmpb	$34, %al
	jne	L20
	movl	%ebp, %esi
	movl	%edx, %eax
L23:
	testl	%edi, %edi
	je	L24
	cmpb	$34, 1(%eax)
	je	L61
L24:
	leal	1(%eax), %edx
	xorl	$1, %edi
	movl	%esi, %ebp
	jmp	L20
L53:
	movl	20(%esp), %ebx
	movl	28(%esp), %edi
	jmp	L5
LFE3:
	.globl	__jit_args_shutdown
__jit_args_shutdown:
LFB4:
	call	__ZL21free_argument_storagev
	ret
LFE4:
	.globl	__jit_param_count
__jit_param_count:
LFB5:
	cmpl	$0, __ZL16g_argument_ready
	je	L66
L64:
	movl	__ZL16g_argument_count, %eax
	testl	%eax, %eax
	movl	$1, %edx
	cmovle	%edx, %eax
	subl	$1, %eax
L63:
	ret
L66:
	call	__jit_args_init
	testl	%eax, %eax
	jne	L64
	ret
LFE5:
	.globl	__jit_param_str_cstr
__jit_param_str_cstr:
LFB6:
	cmpl	$0, __ZL16g_argument_ready
	je	L71
L68:
	cmpl	$0, 4(%esp)
	js	L70
	movl	4(%esp), %eax
	cmpl	%eax, __ZL16g_argument_count
	jle	L70
	movl	__ZL17g_argument_vector, %eax
	movl	4(%esp), %edx
	movl	(%eax,%edx,4), %eax
	ret
L71:
	call	__jit_args_init
	testl	%eax, %eax
	jne	L68
L70:
	movl	$__ZL14g_empty_string, %eax
	ret
LFE6:
	.globl	__jit_command_line_cstr
__jit_command_line_cstr:
LFB7:
	call	_GetCommandLineA@0
	testl	%eax, %eax
	movl	$__ZL14g_empty_string, %edx
	cmove	%edx, %eax
	ret
LFE7:
	.globl	__jit_GetCommandLineA
__jit_GetCommandLineA:
LFB8:
	call	*_p_GetCommandLineA
	ret
LFE8:
	.section .rdata,"dr"
__ZL14g_empty_string:
	.space 1
.lcomm __ZL16g_argument_ready,4,4
.lcomm __ZL16g_argument_count,4,4
.lcomm __ZL17g_argument_vector,4,4
.lcomm __ZL18g_argument_storage,4,4
	.section .drectve
	.ascii " -export:\"_jit_GetCommandLineA\""
	.ascii " -export:\"_jit_command_line_cstr\""
	.ascii " -export:\"_jit_param_str_cstr\""
	.ascii " -export:\"_jit_param_count\""
	.ascii " -export:\"_jit_args_shutdown\""
	.ascii " -export:\"_jit_args_init\""
