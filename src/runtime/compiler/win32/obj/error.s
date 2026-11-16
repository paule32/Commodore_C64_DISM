	.text
	.section .rdata,"dr"
LC0:
	.ascii "division through zero\0"
	.text
	.globl	__jit_error_divide_by_zero
__jit_error_divide_by_zero:
LFB0:
	subl	$8, %esp
	movl	$LC0, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE0:
	.section .rdata,"dr"
LC1:
	.ascii "Array bounds error: \0"
	.text
	.globl	__Z23_jit_error_array_boundsPKciii
__Z23_jit_error_array_boundsPKciii:
LFB1:
	subl	$8, %esp
	movl	$LC1, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE1:
	.section .rdata,"dr"
LC2:
	.ascii "String range check error\0"
	.text
	.globl	__jit_error_string_range
__jit_error_string_range:
LFB2:
	subl	$8, %esp
	movl	$LC2, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE2:
	.section .rdata,"dr"
LC3:
	.ascii "Nil pointer error: \0"
	.text
	.globl	__Z22_jit_error_nil_pointerPKc
__Z22_jit_error_nil_pointerPKc:
LFB3:
	subl	$8, %esp
	movl	$LC3, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE3:
	.section .rdata,"dr"
LC4:
	.ascii "Out of memory: \0"
	.text
	.globl	__jit_error_out_of_memory
__jit_error_out_of_memory:
LFB4:
	subl	$8, %esp
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	movl	$__ZSt4cout, %ecx
	call	__ZNSt7ostreamlsEPKc
	subl	$4, %esp
	movl	%eax, %ecx
	movl	$__ZSt4endlRSt7ostream, (%esp)
	call	__ZNSt7ostreamlsEPFRS_S0_E
	subl	$4, %esp
	movl	$LC4, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE4:
	.globl	__Z18_jit_set_exceptionP10JitContextPKc
__Z18_jit_set_exceptionP10JitContextPKc:
LFB5:
	movl	4(%esp), %eax
	testl	%eax, %eax
	je	L11
	movl	$1, 40(%eax)
	movl	8(%esp), %edx
	movl	%edx, 44(%eax)
L11:
	ret
LFE5:
	.section .rdata,"dr"
LC5:
	.ascii "Runtime error\0"
	.text
	.globl	__jit_error_runtime
__jit_error_runtime:
LFB6:
	subl	$8, %esp
	movl	12(%esp), %eax
	testl	%eax, %eax
	movl	$LC5, %edx
	cmove	%edx, %eax
	movl	%eax, 4(%esp)
	movl	$1, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE6:
	.section .drectve
	.ascii " -export:\"_jit_error_runtime\""
	.ascii " -export:\"_Z18_jit_set_exceptionP10JitContextPKc\""
	.ascii " -export:\"_jit_error_out_of_memory\""
	.ascii " -export:\"_Z22_jit_error_nil_pointerPKc\""
	.ascii " -export:\"_jit_error_string_range\""
	.ascii " -export:\"_Z23_jit_error_array_boundsPKciii\""
	.ascii " -export:\"_jit_error_divide_by_zero\""
