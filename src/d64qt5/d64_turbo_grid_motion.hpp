#pragma once
// Stage 657: Pixel -> DOS-Zellen fuer das Verschieben von Turbo-Vision-Fenstern.
// Qt-frei, damit die Rastergrenzen separat getestet werden koennen.
#include <algorithm>
#include <cstdint>

inline int d64TurboRoundCells(int pixelDelta, int cellExtent)
{
    const std::int64_t cell = std::max(1, cellExtent);
    const std::int64_t pixel = pixelDelta;
    const std::int64_t cells = pixel >= 0
        ? (pixel + cell / 2) / cell
        : -((-pixel + cell / 2) / cell);
    return static_cast<int>(cells);
}

inline int d64TurboClampGridCoordinate(int desiredPixels, int cellExtent, int maxPixels)
{
    const int cell = std::max(1, cellExtent);
    const int maxCell = std::max(0, maxPixels) / cell;
    const int wantedCell = d64TurboRoundCells(desiredPixels, cell);
    return std::clamp(wantedCell, 0, maxCell) * cell;
}

// Stage 659: Fensterabmessungen ausschliesslich in ganzen Konsolenzellen.
// Das Maximum wird abgerundet, das Minimum aufgerundet. Falls der
// Konsolen-Viewport kleiner als die Mindestgroesse ist, hat Qt::minimumSize
// Vorrang; das Ergebnis bleibt trotzdem an ganzen Zellen ausgerichtet.
inline int d64TurboClampGridExtent(int wantedPixels, int cellExtent,
                                  int minimumPixels, int maximumPixels)
{
    const int cell = std::max(1, cellExtent);
    const std::int64_t minCells =
        (std::int64_t(std::max(1, minimumPixels)) + cell - 1) / cell;
    const std::int64_t maxCells = std::max<std::int64_t>(
        minCells, std::int64_t(std::max(0, maximumPixels)) / cell);
    const std::int64_t wantedCells = d64TurboRoundCells(wantedPixels, cell);
    return static_cast<int>(std::clamp(wantedCells, minCells, maxCells) * cell);
}

// Ausgangsgroesse und Maus-Delta werden EINMALIG in Zellen umgerechnet;
// deshalb sammeln sich beim Ziehen keine Pixel-Rundungsfehler an.
inline int d64TurboGridDragExtent(int startPixels, int dragDeltaPixels,
                                 int cellExtent, int minimumPixels,
                                 int maximumPixels)
{
    const int cell = std::max(1, cellExtent);
    const std::int64_t startCells = d64TurboRoundCells(startPixels, cell);
    const std::int64_t deltaCells = d64TurboRoundCells(dragDeltaPixels, cell);
    const std::int64_t minCells =
        (std::int64_t(std::max(1, minimumPixels)) + cell - 1) / cell;
    const std::int64_t maxCells = std::max<std::int64_t>(
        minCells, std::int64_t(std::max(0, maximumPixels)) / cell);
    return static_cast<int>(std::clamp(startCells + deltaCells,
                                       minCells, maxCells) * cell);
}
