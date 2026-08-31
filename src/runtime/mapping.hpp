// ---------------------------------------------------------------------------
// \file mapping.hpp
// \note Copyright (c) 2026 by Jens Kallup - paule32
//       all rights reserved.
// ---------------------------------------------------------------------------
#ifndef __DBASE2MANY_MAPPING_HPP__
#define __DBASE2MANY_MAPPING_HPP__

#pragma once

// ---------------------------------------------------------------------------
// assembly label mapping ...
// ---------------------------------------------------------------------------
struct LabelMapping
{
    std::string asmjitLabel;
    std::string targetLabel;

    LabelMapping(
        const std::string& asmjit,
        const std::string& target);
};

class LabelMappings
{
private:
    std::vector<LabelMapping> mappings;

public:
    void add(
        const std::string& asmjitLabel,
        const std::string& targetLabel);
    void clear();
    void remove(
        const  std::string& asmjitLabel);
    void apply(std::string& asm_text);
};

// ---------------------------------------------------------------------------
// assembly symbol mapping
// ---------------------------------------------------------------------------
struct SymbolMapping
{
    std::string addressText;
    std::string symbolName;

    SymbolMapping(
        const std::string& address,
        const std::string& symbol);
};

class SymbolMappings
{
private:
    std::vector<SymbolMapping> mappings;

public:
    void add(
        const  std::string& addressText,
        const  std::string& symbolName);
        
    void apply(std::string& asm_text);
};

#endif  // __DBASE2MANY_MAPPING_HPP__
