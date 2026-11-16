	.text
	.section .rdata,"dr"
LC0:
	.ascii "\0"
	.text
_jit_set_error:
LFB4:
	movl	%eax, _g_last_error
	testl	%edx, %edx
	movl	$LC0, %ecx
	cmove	%ecx, %edx
	movl	%edx, _g_last_error_message
	movl	_g_error_hook, %ecx
	testl	%ecx, %ecx
	je	L6
	subl	$8, %esp
	movl	%edx, 4(%esp)
	movl	%eax, (%esp)
	call	*%ecx
	addl	$8, %esp
	ret
L6:
	ret
LFE4:
	.section .rdata,"dr"
LC1:
	.ascii "VMT pointer is null\0"
	.align 4
LC2:
	.ascii "VMT instance_size is smaller than the object header\0"
	.text
_jit_valid_vmt:
LFB5:
	testl	%eax, %eax
	je	L14
	movl	$1, %edx
	cmpl	$3, 8(%eax)
	jbe	L15
L9:
	movl	%edx, %eax
	ret
L14:
	movl	$LC1, %edx
	movl	$1, %eax
	call	_jit_set_error
	jmp	L12
L15:
	movl	$LC2, %edx
	movl	$1, %eax
	call	_jit_set_error
L12:
	movl	$0, %edx
	jmp	L9
LFE5:
_d64_object_transition:
LFB2:
	testl	%eax, %eax
	je	L39
	pushl	%ebp
	pushl	%edi
	pushl	%esi
	pushl	%ebx
	movl	%eax, %esi
	movl	%edx, %ebp
	movl	$1, %edx
	jmp	L18
L19:
/APP
 # 39 "jitObject.cc" 1
	pause
 # 0 "" 2
/NO_APP
L18:
	movl	%edx, %eax
	xchgl	_g_registry_lock, %eax
	testl	%eax, %eax
	jne	L19
	movl	%esi, %edx
	shrl	$4, %edx
	leal	8192(%edx), %edi
	movl	$8192, %ebx
	jmp	L33
L54:
	testl	%ebp, %ebp
	jne	L22
	leal	(%eax,%eax,2), %edx
	cmpl	$3, _g_tracked+4(,%edx,4)
	je	L23
L26:
	movl	$-1, %eax
L24:
	movl	$0, _g_registry_lock
	jmp	L16
L23:
	leal	(%eax,%eax), %edx
	leal	(%edx,%eax), %ecx
	movl	$1, _g_tracked+4(,%ecx,4)
	movl	_g_generation, %ebx
	leal	1(%ebx), %ecx
	movl	%ecx, _g_generation
	addl	%eax, %edx
	movl	%ecx, _g_tracked+8(,%edx,4)
L27:
	movl	$1, %eax
	jmp	L24
L22:
	cmpl	$1, %ebp
	je	L50
	cmpl	$2, %ebp
	je	L51
	cmpl	$4, %ebp
	je	L52
	leal	(%eax,%eax,2), %eax
	movl	_g_tracked+4(,%eax,4), %edx
	leal	-1(%edx), %eax
	cmpl	$1, %eax
	jbe	L43
	movl	$-1, %eax
	cmpl	$4, %edx
	jne	L24
L43:
	movl	$1, %eax
	jmp	L24
L50:
	leal	(%eax,%eax,2), %edx
	cmpl	$1, _g_tracked+4(,%edx,4)
	jne	L26
	movl	$2, _g_tracked+4(,%edx,4)
	jmp	L27
L51:
	leal	(%eax,%eax,2), %edx
	movl	_g_tracked+4(,%edx,4), %edx
	subl	$1, %edx
	cmpl	$1, %edx
	ja	L26
	leal	(%eax,%eax,2), %eax
	movl	$4, _g_tracked+4(,%eax,4)
	jmp	L27
L52:
	leal	(%eax,%eax,2), %edx
	cmpl	$4, _g_tracked+4(,%edx,4)
	jne	L26
	movl	$3, _g_tracked+4(,%edx,4)
	jmp	L27
L31:
	addl	$1, %edx
	cmpl	%edi, %edx
	je	L53
L33:
	movl	%edx, %eax
	andl	$8191, %eax
	leal	(%eax,%eax,2), %ecx
	movl	_g_tracked(,%ecx,4), %ecx
	testl	%ecx, %ecx
	je	L20
	cmpl	%esi, %ecx
	je	L54
	leal	(%eax,%eax,2), %ecx
	cmpl	$3, _g_tracked+4(,%ecx,4)
	jne	L31
	cmpl	$8192, %ebx
	cmove	%eax, %ebx
	jmp	L31
L39:
	movl	$0, %eax
	ret
L53:
	testl	%ebp, %ebp
	jne	L37
	movl	$-1, %eax
	cmpl	$8192, %ebx
	je	L35
	movl	%ebx, %eax
L38:
	leal	(%eax,%eax), %edx
	leal	(%edx,%eax), %ecx
	sall	$2, %ecx
	movl	%esi, _g_tracked(%ecx)
	movl	$1, _g_tracked+4(%ecx)
	movl	_g_generation, %ebx
	leal	1(%ebx), %ecx
	movl	%ecx, _g_generation
	addl	%eax, %edx
	movl	%ecx, _g_tracked+8(,%edx,4)
	movl	$1, %eax
	jmp	L35
L20:
	testl	%ebp, %ebp
	je	L38
L37:
	movl	$0, %eax
L35:
	movl	$0, _g_registry_lock
L16:
	popl	%ebx
	popl	%esi
	popl	%edi
	popl	%ebp
	ret
LFE2:
	.globl	_jit_object_error_set_hook
_jit_object_error_set_hook:
LFB6:
	movl	4(%esp), %eax
	movl	%eax, _g_error_hook
	ret
LFE6:
	.globl	_jit_object_error_last
_jit_object_error_last:
LFB7:
	movl	_g_last_error, %eax
	ret
LFE7:
	.globl	_jit_object_error_last_message
_jit_object_error_last_message:
LFB8:
	movl	_g_last_error_message, %eax
	ret
LFE8:
	.globl	_jit_object_error_clear
_jit_object_error_clear:
LFB9:
	movl	$0, _g_last_error
	movl	$LC0, _g_last_error_message
	ret
LFE9:
	.section .rdata,"dr"
	.align 4
LC3:
	.ascii "Could not allocate object instance\0"
	.align 4
LC4:
	.ascii "Object allocation registry exhausted\0"
	.text
	.globl	_jit_object_instance_new
_jit_object_instance_new:
LFB10:
	pushl	%esi
	pushl	%ebx
	subl	$8, %esp
	movl	20(%esp), %esi
	call	_jit_object_error_clear
	movl	%esi, %eax
	call	_jit_valid_vmt
	testl	%eax, %eax
	je	L64
	movl	8(%esi), %eax
	movl	%eax, 4(%esp)
	movl	$1, (%esp)
	call	__jit_calloc
	movl	%eax, %ebx
	testl	%eax, %eax
	je	L67
	movl	$0, %edx
	call	_d64_object_transition
	cmpl	$1, %eax
	jne	L68
	movl	%esi, (%ebx)
	movl	12(%esi), %eax
	testl	%eax, %eax
	je	L59
	movl	%ebx, (%esp)
	call	*%eax
	jmp	L59
L67:
	movl	$LC3, %edx
	movl	$3, %eax
	call	_jit_set_error
	jmp	L59
L68:
	movl	%ebx, (%esp)
	call	__jit_free
	movl	$LC4, %edx
	movl	$7, %eax
	call	_jit_set_error
L64:
	movl	$0, %ebx
L59:
	movl	%ebx, %eax
	addl	$8, %esp
	popl	%ebx
	popl	%esi
	ret
LFE10:
	.section .rdata,"dr"
	.align 4
LC5:
	.ascii "Object already freed, is being freed, or was never allocated here\0"
	.align 4
LC6:
	.ascii "Object contains an invalid VMT pointer\0"
	.text
	.globl	_jit_object_instance_free
_jit_object_instance_free:
LFB11:
	leal	-12(%esp), %esp
	movl	%ebx, 4(%esp)
	movl	16(%esp), %ebx
	call	_jit_object_error_clear
	testl	%ebx, %ebx
	je	L69
	movl	$2, %edx
	movl	%ebx, %eax
	call	_d64_object_transition
	cmpl	$1, %eax
	je	L71
	movl	$LC5, %edx
	movl	$5, %eax
	call	_jit_set_error
L69:
	movl	4(%esp), %ebx
	leal	12(%esp), %esp
	ret
L71:
	movl	%esi, 8(%esp)
	movl	(%ebx), %eax
	movl	%eax, %esi
	call	_jit_valid_vmt
	testl	%eax, %eax
	je	L75
	movl	16(%esi), %eax
	testl	%eax, %eax
	je	L73
	movl	%ebx, (%esp)
	call	*%eax
L73:
	movl	$0, (%ebx)
	movl	$4, %edx
	movl	%ebx, %eax
	call	_d64_object_transition
	movl	%ebx, (%esp)
	call	__jit_free
	movl	8(%esp), %esi
	jmp	L69
L75:
	movl	$LC6, %edx
	movl	$2, %eax
	call	_jit_set_error
	movl	8(%esp), %esi
	jmp	L69
LFE11:
	.section .rdata,"dr"
	.align 4
LC7:
	.ascii "Object VMT requested for invalid or freed pointer\0"
	.text
	.globl	_jit_object_class_type
_jit_object_class_type:
LFB13:
	pushl	%ebx
	movl	8(%esp), %ebx
	call	_jit_object_error_clear
	testl	%ebx, %ebx
	je	L81
	movl	$3, %edx
	movl	%ebx, %eax
	call	_d64_object_transition
	cmpl	$1, %eax
	jne	L83
	movl	(%ebx), %eax
	call	_jit_valid_vmt
	testl	%eax, %eax
	je	L84
	movl	(%ebx), %eax
L76:
	popl	%ebx
	ret
L83:
	movl	$LC7, %edx
	movl	$6, %eax
	call	_jit_set_error
L80:
	movl	$0, %eax
	jmp	L76
L84:
	movl	$LC6, %edx
	movl	$2, %eax
	call	_jit_set_error
	jmp	L80
L81:
	movl	%ebx, %eax
	jmp	L76
LFE13:
	.section .rdata,"dr"
	.align 4
LC8:
	.ascii "Repeated or concurrent jit_object_free detected\0"
	.text
	.globl	_jit_object_free
_jit_object_free:
LFB12:
	pushl	%ebx
	subl	$4, %esp
	movl	12(%esp), %ebx
	call	_jit_object_error_clear
	testl	%ebx, %ebx
	je	L85
	movl	$1, %edx
	movl	%ebx, %eax
	call	_d64_object_transition
	cmpl	$1, %eax
	je	L87
	movl	$LC8, %edx
	movl	$5, %eax
	call	_jit_set_error
L85:
	addl	$4, %esp
	popl	%ebx
	ret
L87:
	movl	%ebx, (%esp)
	call	_jit_object_class_type
	testl	%eax, %eax
	je	L85
	movl	20(%eax), %eax
	testl	%eax, %eax
	je	L88
	movl	%ebx, (%esp)
	call	*%eax
L88:
	movl	%ebx, (%esp)
	call	_jit_object_instance_free
	jmp	L85
LFE12:
	.globl	_jit_class_parent
_jit_class_parent:
LFB14:
	call	_jit_object_error_clear
	movl	4(%esp), %eax
	call	_jit_valid_vmt
	testl	%eax, %eax
	je	L92
	movl	4(%esp), %eax
	movl	(%eax), %eax
	ret
L92:
	movl	$0, %eax
	ret
LFE14:
	.section .rdata,"dr"
LC9:
	.ascii "<unknown>\0"
LC10:
	.ascii "vmt is nil\12\0"
	.text
	.globl	_jit_class_name
_jit_class_name:
LFB15:
	subl	$4, %esp
	movl	8(%esp), %eax
	testl	%eax, %eax
	je	L98
	movl	4(%eax), %eax
	testl	%eax, %eax
	movl	$LC9, %edx
	cmove	%edx, %eax
L93:
	addl	$4, %esp
	ret
L98:
	movl	$LC10, (%esp)
	call	__jit_printf
	movl	$LC0, %eax
	jmp	L93
LFE15:
	.globl	_jit_class_instance_size
_jit_class_instance_size:
LFB16:
	call	_jit_object_error_clear
	movl	4(%esp), %eax
	call	_jit_valid_vmt
	movl	%eax, %edx
	movl	$0, %eax
	testl	%edx, %edx
	je	L99
	movl	4(%esp), %eax
	movl	8(%eax), %eax
L99:
	ret
LFE16:
	.globl	_jit_inherits_from_class
_jit_inherits_from_class:
LFB17:
	pushl	%esi
	pushl	%ebx
	movl	12(%esp), %ebx
	movl	16(%esp), %esi
	call	_jit_object_error_clear
	testl	%ebx, %ebx
	je	L106
	testl	%esi, %esi
	je	L106
	.p2align 4
L103:
	cmpl	%ebx, %esi
	je	L107
	movl	(%ebx), %ebx
	testl	%ebx, %ebx
	jne	L103
L106:
	movl	$0, %eax
L102:
	popl	%ebx
	popl	%esi
	ret
L107:
	movl	$1, %eax
	jmp	L102
LFE17:
	.globl	_jit_inherits_from_object
_jit_inherits_from_object:
LFB18:
	subl	$8, %esp
	call	_jit_object_error_clear
	cmpl	$0, 12(%esp)
	je	L115
	cmpl	$0, 16(%esp)
	je	L115
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	_jit_object_class_type
	testl	%eax, %eax
	je	L115
	movl	16(%esp), %edx
	movl	%edx, 4(%esp)
	movl	%eax, (%esp)
	call	_jit_inherits_from_class
	jmp	L111
L115:
	movl	$0, %eax
L111:
	addl	$8, %esp
	ret
LFE18:
	.section .rdata,"dr"
LC11:
	.ascii "Virtual method slot is null\0"
	.text
	.globl	_jit_get_virtual_vmt
_jit_get_virtual_vmt:
LFB19:
	pushl	%ebx
	movl	8(%esp), %ebx
	call	_jit_object_error_clear
	movl	%ebx, %eax
	call	_jit_valid_vmt
	testl	%eax, %eax
	je	L120
	movl	12(%esp), %eax
	movl	24(%ebx,%eax,4), %ebx
	testl	%ebx, %ebx
	je	L122
L117:
	movl	%ebx, %eax
	popl	%ebx
	ret
L122:
	movl	$LC11, %edx
	movl	$4, %eax
	call	_jit_set_error
	jmp	L117
L120:
	movl	$0, %ebx
	jmp	L117
LFE19:
	.globl	_jit_get_virtual_object
_jit_get_virtual_object:
LFB20:
	subl	$8, %esp
	call	_jit_object_error_clear
	movl	12(%esp), %eax
	movl	%eax, (%esp)
	call	_jit_object_class_type
	testl	%eax, %eax
	je	L123
	movl	16(%esp), %edx
	movl	%edx, 4(%esp)
	movl	%eax, (%esp)
	call	_jit_get_virtual_vmt
L123:
	addl	$8, %esp
	ret
LFE20:
.lcomm _g_error_hook,4,4
	.data
	.align 4
_g_last_error_message:
	.long	LC0
.lcomm _g_last_error,4,4
.lcomm _g_generation,4,4
.lcomm _g_registry_lock,4,4
.lcomm _g_tracked,98304,32
	.section .drectve
	.ascii " -export:\"jit_get_virtual_object\""
	.ascii " -export:\"jit_get_virtual_vmt\""
	.ascii " -export:\"jit_inherits_from_object\""
	.ascii " -export:\"jit_inherits_from_class\""
	.ascii " -export:\"jit_class_instance_size\""
	.ascii " -export:\"jit_class_name\""
	.ascii " -export:\"jit_class_parent\""
	.ascii " -export:\"jit_object_free\""
	.ascii " -export:\"jit_object_class_type\""
	.ascii " -export:\"jit_object_error_clear\""
	.ascii " -export:\"jit_object_error_last_message\""
	.ascii " -export:\"jit_object_error_last\""
