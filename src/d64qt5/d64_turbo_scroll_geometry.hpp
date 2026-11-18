#pragma once

// Stage 630: Die DOS-Scrollbar-Geometrie ist unabhaengig vom Qt-Style.
// Alle Intervalle sind halb offen [start, end). Dadurch koennen Slider
// und Pfeilfelder selbst an den beiden Endpositionen nicht ueberlappen.
// Diese Datei kann auch ohne Qt mit g++/MinGW getestet werden.
#include <algorithm>
#include <cstdint>

struct D64TurboScrollGeometry
{
    int axisExtent = 0;
    int buttonExtent = 0;
    int grooveStart = 0;
    int grooveExtent = 0;
    int thumbStart = 0;
    int thumbExtent = 0;
    int minimum = 0;
    int maximum = 0;

    int grooveEnd() const { return grooveStart + grooveExtent; }
    int thumbEnd() const { return thumbStart + thumbExtent; }
    int arrowEndStart() const { return axisExtent - buttonExtent; }

    int valueForThumbStart(int desiredStart) const
    {
        const int travel = grooveExtent - thumbExtent;
        if (travel <= 0 || maximum <= minimum)
            return minimum;
        const int displacement = std::max(0, std::min(travel, desiredStart - grooveStart));
        const std::int64_t range = std::int64_t(maximum) - minimum;
        const std::int64_t delta = (std::int64_t(displacement) * range + travel / 2) / travel;
        return int(std::int64_t(minimum) + delta);
    }
};

inline D64TurboScrollGeometry d64TurboScrollGeometry(
    int axisExtent, int thickness, int minimum, int maximum, int pageStep, int value)
{
    D64TurboScrollGeometry g;
    g.axisExtent = std::max(0, axisExtent);
    g.buttonExtent = std::min(std::max(0, thickness), g.axisExtent / 2);
    g.grooveStart = g.buttonExtent;
    g.thumbStart = g.grooveStart;
    g.grooveExtent = g.axisExtent - 2 * g.buttonExtent;
    g.minimum = minimum;
    g.maximum = std::max(minimum, maximum);
    if (g.grooveExtent <= 0)
        return g;

    const std::int64_t range = std::int64_t(g.maximum) - g.minimum;
    const std::int64_t page = std::max(1, pageStep);
    if (range == 0) {
        g.thumbExtent = g.grooveExtent;
        g.thumbStart = g.grooveStart;
        return g;
    }

    // Ein 12-Pixel-Thumb bleibt bei kurzen Scrollbars innerhalb der Rille.
    const std::int64_t scaled = (std::int64_t(g.grooveExtent) * page + (range + page) / 2)
                                / (range + page);
    const int minThumb = std::min(12, g.grooveExtent);
    g.thumbExtent = std::max(minThumb, std::min(g.grooveExtent, int(scaled)));
    const int travel = g.grooveExtent - g.thumbExtent;
    const std::int64_t clamped = std::max<std::int64_t>(
        0, std::min<std::int64_t>(range, std::int64_t(value) - g.minimum));
    const int displacement = int((clamped * travel + range / 2) / range);
    g.thumbStart = g.grooveStart + displacement;
    return g;
}
