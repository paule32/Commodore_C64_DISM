	.text
	.section .rdata,"dr"
LC0:
	.ascii "kernel32.dll\0"
LC1:
	.ascii "TlsAlloc\0"
LC2:
	.ascii "TlsFree\0"
LC3:
	.ascii "TlsGetValue\0"
LC4:
	.ascii "TlsSetValue\0"
	.text
__ZL23d64_exception_tls_readyv:
LFB0:
	leal	-16(%esp), %esp
	movl	%esi, 12(%esp)
	movl	$2, %eax
	lock cmpxchgl	%eax, __ZL11g_tls_state
	movl	$1, %esi
	cmpl	$2, %eax
	je	L1
	movl	$0, %eax
	movl	$1, %edx
	lock cmpxchgl	%edx, __ZL11g_tls_state
	sete	%al
	movl	%eax, %esi
	jne	L3
	movl	%ebx, 8(%esp)
	movl	$LC0, (%esp)
	call	_LoadLibraryA@4
	subl	$4, %esp
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L4
	movl	$LC1, 4(%esp)
	movl	%eax, (%esp)
	call	_GetProcAddress@8
	subl	$8, %esp
	movl	%eax, __ZL11g_tls_alloc
	movl	$LC2, 4(%esp)
	movl	%ebx, (%esp)
	call	_GetProcAddress@8
	subl	$8, %esp
	movl	%eax, __ZL10g_tls_free
	movl	$LC3, 4(%esp)
	movl	%ebx, (%esp)
	call	_GetProcAddress@8
	subl	$8, %esp
	movl	%eax, __ZL9g_tls_get
	movl	$LC4, 4(%esp)
	movl	%ebx, (%esp)
	call	_GetProcAddress@8
	subl	$8, %esp
	movl	%eax, __ZL9g_tls_set
L4:
	movl	__ZL11g_tls_alloc, %eax
	testl	%eax, %eax
	je	L5
	cmpl	$0, __ZL10g_tls_free
	je	L5
	cmpl	$0, __ZL9g_tls_get
	je	L5
	cmpl	$0, __ZL9g_tls_set
	je	L5
	call	*%eax
	movl	%eax, __ZL11g_tls_index
	lock orl	$0, (%esp)
	cmpl	$-1, %eax
	je	L9
	movl	$2, %eax
	jmp	L6
L5:
	lock orl	$0, (%esp)
	movl	$0, %esi
	movl	$3, %eax
L6:
	movl	%eax, __ZL11g_tls_state
	movl	8(%esp), %ebx
L1:
	movl	%esi, %eax
	movl	12(%esp), %esi
	leal	16(%esp), %esp
	ret
L9:
	movl	$0, %esi
	movl	$3, %eax
	jmp	L6
L7:
/APP
 # 48 "exception.cc" 1
	pause
 # 0 "" 2
/NO_APP
L3:
	movl	%edx, %eax
	lock cmpxchgl	%edx, __ZL11g_tls_state
	cmpl	$1, %eax
	je	L7
	movl	$2, %eax
	lock cmpxchgl	%eax, __ZL11g_tls_state
	cmpl	$2, %eax
	sete	%al
	movl	%eax, %esi
	jmp	L1
LFE0:
__ZL21d64_current_exceptionv:
LFB1:
	subl	$4, %esp
	call	__ZL23d64_exception_tls_readyv
	testb	%al, %al
	je	L16
L14:
	movl	__ZL11g_tls_index, %eax
	movl	%eax, (%esp)
	call	*__ZL9g_tls_get
	subl	$4, %esp
	addl	$4, %esp
	ret
L16:
	movl	$1, (%esp)
	call	_ExitProcess@4
	subl	$4, %esp
	jmp	L14
LFE1:
__ZL25d64_set_current_exceptionP17JitExceptionFrame:
LFB2:
	pushl	%ebx
	subl	$8, %esp
	movl	%eax, %ebx
	call	__ZL23d64_exception_tls_readyv
	testb	%al, %al
	je	L18
	movl	%ebx, 4(%esp)
	movl	__ZL11g_tls_index, %eax
	movl	%eax, (%esp)
	call	*__ZL9g_tls_set
	subl	$8, %esp
	testl	%eax, %eax
	jne	L17
L18:
	movl	$1, (%esp)
	call	_ExitProcess@4
	subl	$4, %esp
L17:
	addl	$8, %esp
	popl	%ebx
	ret
LFE2:
	.globl	__jit_exception_tls_cleanup
__jit_exception_tls_cleanup:
LFB3:
	movl	$2, %eax
	lock cmpxchgl	%eax, __ZL11g_tls_state
	cmpl	$2, %eax
	je	L27
	ret
L27:
	subl	$4, %esp
	movl	__ZL11g_tls_index, %eax
	movl	%eax, (%esp)
	call	*__ZL10g_tls_free
	subl	$4, %esp
	movl	$-1, __ZL11g_tls_index
	movl	$3, __ZL11g_tls_state
	addl	$4, %esp
	ret
LFE3:
	.align 2
	.globl	__ZNSt13runtime_errorC2Ev
__ZNSt13runtime_errorC2Ev:
LFB5:
	ret
LFE5:
	.globl	__ZNSt13runtime_errorC1Ev
	.set	__ZNSt13runtime_errorC1Ev,__ZNSt13runtime_errorC2Ev
	.section .rdata,"dr"
LC5:
	.ascii "Error\0"
	.text
	.align 2
	.globl	__ZNSt13runtime_errorC2ERKSt6string
__ZNSt13runtime_errorC2ERKSt6string:
LFB8:
	subl	$16, %esp
	movl	20(%esp), %ecx
	call	__ZNKSt6string5c_strEv
	movl	$0, 12(%esp)
	movl	$LC5, 8(%esp)
	movl	%eax, 4(%esp)
	movl	$0, (%esp)
	call	_MessageBoxA@16
	subl	$16, %esp
	movl	$1, (%esp)
	call	_ExitProcess@4
	subl	$4, %esp
	addl	$16, %esp
	ret	$4
LFE8:
	.globl	__ZNSt13runtime_errorC1ERKSt6string
	.set	__ZNSt13runtime_errorC1ERKSt6string,__ZNSt13runtime_errorC2ERKSt6string
	.align 2
	.globl	__ZNSt15JitRuntimeErrorC2ERKSt6string
__ZNSt15JitRuntimeErrorC2ERKSt6string:
LFB11:
	subl	$4, %esp
	movl	8(%esp), %eax
	movl	%eax, (%esp)
	call	__ZNSt13runtime_errorC2ERKSt6string
	subl	$4, %esp
	addl	$4, %esp
	ret	$4
LFE11:
	.globl	__ZNSt15JitRuntimeErrorC1ERKSt6string
	.set	__ZNSt15JitRuntimeErrorC1ERKSt6string,__ZNSt15JitRuntimeErrorC2ERKSt6string
	.globl	__jit_exception_push
__jit_exception_push:
LFB13:
	pushl	%ebx
	movl	8(%esp), %ebx
	testl	%ebx, %ebx
	je	L33
	cmpl	$0, (%ebx)
	je	L33
	call	__ZL21d64_current_exceptionv
	movl	%eax, 264(%ebx)
	movl	$0, 4(%ebx)
	movb	$0, 8(%ebx)
	movl	%ebx, %eax
	call	__ZL25d64_set_current_exceptionP17JitExceptionFrame
L33:
	popl	%ebx
	ret
LFE13:
	.globl	__jit_exception_pop
__jit_exception_pop:
LFB14:
	call	__ZL21d64_current_exceptionv
	testl	%eax, %eax
	je	L36
	movl	264(%eax), %eax
	call	__ZL25d64_set_current_exceptionP17JitExceptionFrame
L36:
	ret
LFE14:
	.section .rdata,"dr"
LC6:
	.ascii "Unhandled Runtime Exception\0"
	.text
	.globl	__jit_raise
__jit_raise:
LFB15:
	pushl	%esi
	pushl	%ebx
	subl	$8, %esp
	movl	24(%esp), %esi
	call	__ZL21d64_current_exceptionv
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L48
L39:
	movl	20(%esp), %eax
	movl	%eax, 4(%ebx)
	testl	%esi, %esi
	je	L43
	movzbl	(%esi), %edx
	testb	%dl, %dl
	je	L43
	movl	$0, %eax
	.p2align 5
L45:
	movb	%dl, 8(%ebx,%eax)
	addl	$1, %eax
	movzbl	(%esi,%eax), %edx
	testb	%dl, %dl
	je	L42
	cmpl	$255, %eax
	jne	L45
	jmp	L42
L48:
	movl	$LC6, (%esp)
	movl	$__ZSt4cout, %ecx
	call	__ZNSt7ostreamlsEPKc
	subl	$4, %esp
	movl	%eax, %ecx
	movl	$__ZSt4endlRSt7ostream, (%esp)
	call	__ZNSt7ostreamlsEPFRS_S0_E
	subl	$4, %esp
	testl	%esi, %esi
	je	L40
	movl	%esi, (%esp)
	movl	$__ZSt4cout, %ecx
	call	__ZNSt7ostreamlsEPKc
	subl	$4, %esp
	movl	%eax, %ecx
	movl	$__ZSt4endlRSt7ostream, (%esp)
	call	__ZNSt7ostreamlsEPFRS_S0_E
	subl	$4, %esp
L40:
	movl	$1, (%esp)
	call	_ExitProcess@4
	subl	$4, %esp
	jmp	L39
L43:
	movl	$0, %eax
L42:
	movb	$0, 8(%ebx,%eax)
	movl	$1, 4(%esp)
	movl	(%ebx), %eax
	movl	%eax, (%esp)
	call	__jit_longjmp
	addl	$8, %esp
	popl	%ebx
	popl	%esi
	ret
LFE15:
	.section .rdata,"dr"
LC7:
	.ascii "Out of memory\0"
	.text
	.globl	__Z24_jit_error_out_of_memoryv
__Z24_jit_error_out_of_memoryv:
LFB16:
	subl	$8, %esp
	movl	$LC7, 4(%esp)
	movl	$2, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE16:
	.section .rdata,"dr"
LC8:
	.ascii "Nil pointer\0"
	.text
	.globl	__jit_error_nil_pointer
__jit_error_nil_pointer:
LFB17:
	subl	$8, %esp
	movl	$LC8, 4(%esp)
	movl	$3, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE17:
	.section .rdata,"dr"
LC9:
	.ascii "Array bounds exceeded\0"
	.text
	.globl	__jit_error_array_bounds
__jit_error_array_bounds:
LFB18:
	subl	$8, %esp
	movl	$LC9, 4(%esp)
	movl	$4, (%esp)
	call	__jit_raise
	addl	$8, %esp
	ret
LFE18:
.lcomm __ZL11g_tls_state,4,4
	.data
	.align 4
__ZL11g_tls_index:
	.long	-1
.lcomm __ZL9g_tls_set,4,4
.lcomm __ZL9g_tls_get,4,4
.lcomm __ZL10g_tls_free,4,4
.lcomm __ZL11g_tls_alloc,4,4
	.section .drectve
	.ascii " -export:\"_jit_error_array_bounds\""
	.ascii " -export:\"_jit_error_nil_pointer\""
	.ascii " -export:\"_Z24_jit_error_out_of_memoryv\""
	.ascii " -export:\"_jit_raise\""
	.ascii " -export:\"_jit_exception_pop\""
	.ascii " -export:\"_jit_exception_push\""
