#pragma once

#if defined(D64_SAMPLE_LIBRARY)
#  define D64_SAMPLE_API __declspec(dllexport)
#else
#  define D64_SAMPLE_API __declspec(dllimport)
#endif

extern "C" D64_SAMPLE_API int d64_add(int left, int right);

