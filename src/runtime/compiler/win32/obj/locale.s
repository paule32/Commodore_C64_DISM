	.text
	.globl	__jit_locale_user
__jit_locale_user:
LFB1:
	call	*_p_GetUserDefaultLCID
	ret
LFE1:
	.globl	__jit_locale_system
__jit_locale_system:
LFB2:
	call	*_p_GetSystemDefaultLCID
	ret
LFE2:
	.section .drectve
	.ascii " -export:\"_jit_locale_system\""
	.ascii " -export:\"_jit_locale_user\""
