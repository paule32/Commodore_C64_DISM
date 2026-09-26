// Stage 213: stable runtime ABI/ordinal-map identity exported by name.
#pragma once

#include <cstdint>
#include <cstring>
#include "d64qt5_bridge.h"
#include "d64_runtime_abi.inc"

namespace {
static const D64RuntimeAbiInfo g_d64_runtime_abi_info = []() {
    D64RuntimeAbiInfo info{};
    info.structSize = static_cast<std::uint32_t>(sizeof(D64RuntimeAbiInfo));
    info.abiMajor = D64_RUNTIME_ABI_MAJOR;
    info.abiMinor = D64_RUNTIME_ABI_MINOR;
    info.ordinalMapVersion = D64_RUNTIME_ORDINAL_MAP_VERSION;
    info.loaderMinVersion = D64_RUNTIME_MIN_LOADER_VERSION;
    std::memcpy(info.ordinalMapHash, D64_RUNTIME_ORDINAL_MAP_HASH, sizeof(info.ordinalMapHash));
    std::strncpy(info.runtimeName, D64_RUNTIME_NAME, sizeof(info.runtimeName) - 1u);
    info.runtimeName[sizeof(info.runtimeName) - 1u] = '\0';
    return info;
}();
}

extern "C" D64QT5_API const D64RuntimeAbiInfo *D64GetRuntimeAbiInfo(void)
{
    return &g_d64_runtime_abi_info;
}
