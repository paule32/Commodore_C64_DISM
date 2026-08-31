// ---------------------------------------------------------------------------
// \file mapping.cc
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
# include "dbase2many.hpp"

LabelMapping::LabelMapping(
    const std::string& asmjit,
    const std::string& target)
    :
    asmjitLabel(asmjit),
    targetLabel(target) {}

SymbolMapping::SymbolMapping(
    const std::string& address,
    const std::string& symbol)
    :
    addressText(address),
    symbolName(symbol) {}

DLL_API void
LabelMappings::add(
    const std::string& asmjitLabel,
    const std::string& targetLabel)
{
    mappings.emplace_back(
        asmjitLabel,
        targetLabel);
}

DLL_API void
LabelMappings::clear() { mappings.clear(); }

DLL_API void
LabelMappings::remove(const std::string& asmjitLabel)
{
    mappings.erase(
    std::remove_if(
        mappings.begin(),
        mappings.end(),
        [&](const LabelMapping& item)
        {
            return item.asmjitLabel == asmjitLabel;
        }),
    mappings.end());
}

DLL_API void
LabelMappings::apply(std::string& asm_text)
{
    for (const auto& item : mappings)
    {
        replace_all(
            asm_text,
            item.asmjitLabel + ":",
            item.targetLabel + ":");

        replace_all(
            asm_text,
            item.asmjitLabel,
            item.targetLabel);
    }
}

DLL_API void
SymbolMappings::add(
    const std::string& addressText,
    const std::string& symbolName) {
    
    mappings.emplace_back(addressText, symbolName);
}

DLL_API void
SymbolMappings::apply(
    std::string& asm_text)
{
    for (const auto& item : mappings)
    {
        replace_all(
            asm_text,
            item.addressText,
            item.symbolName);
    }
}

DLL_API void
_jit_symbols_add(SymbolMappings& symbols)
{
    symbols.add(std::to_string((uint64_t)&_jit_print_text), "_jit_print_text");
    symbols.add(std::to_string((uint64_t)&_jit_print_int), "_jit_print_int");
    symbols.add(std::to_string((uint64_t)&_jit_print_double), "_jit_print_double");
    symbols.add(std::to_string((uint64_t)&_jit_print_newline), "_jit_print_newline");
    
    symbols.add(std::to_string((uint64_t)&_jit_new_memory), "_jit_new_memory");
    symbols.add(std::to_string((uint64_t)&_jit_dispose_memory), "_jit_dispose_memory");
    
    symbols.add(std::to_string((uint64_t)&_jit_dynarray_setlength), "_jit_dynarray_setlength");
    
    symbols.add(std::to_string((uint64_t)&_jit_dynstring_from_cstr), "_jit_dynstring_from_cstr");
    symbols.add(std::to_string((uint64_t)&_jit_dynstring_setlength), "_jit_dynstring_setlength");
    symbols.add(std::to_string((uint64_t)&_jit_dynstring_length), "_jit_dynstring_length");
    symbols.add(std::to_string((uint64_t)&_jit_dynstring_concat), "_jit_dynstring_concat");
    symbols.add(std::to_string((uint64_t)&_jit_dynstring_copy), "_jit_dynstring_copy");
    symbols.add(std::to_string((uint64_t)&_jit_dynstring_pos), "_jit_dynstring_pos");
    
    symbols.add(std::to_string((uint64_t)&_jit_set_exception), "_jit_set_exception");
    symbols.add(std::to_string((uint64_t)&_jit_runtime_error), "_jit_runtime_error");
    
    symbols.add(std::to_string((uint64_t)&_jit_array_bounds_error), "_jit_array_bounds_error");
    symbols.add(std::to_string((uint64_t)&_jit_string_range_error), "_jit_string_range_error");
    symbols.add(std::to_string((uint64_t)&_jit_nil_pointer_error), "_jit_nil_pointer_error");
    symbols.add(std::to_string((uint64_t)&_jit_out_of_memory_error), "_jit_out_of_memory_error");
    
    symbols.add(std::to_string((uint64_t)&_jit_read_int), "_jit_read_int");
    symbols.add(std::to_string((uint64_t)&_jit_read_string), "_jit_read_string");
    
    symbols.add(std::to_string((uint64_t)&_jit_debug_break), "_jit_debug_break");
    
    symbols.add(std::to_string((uint64_t)&_jit_ExitProcess), "_jit_ExitProcess");
}
