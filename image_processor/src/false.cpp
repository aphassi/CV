#include "utility/false.h"

#include <cmath>
#include <array>
#include <cstdint>

namespace {

constexpr float MaxColorValue = 255.0f;

constexpr float RCoef = 0.299f;
constexpr float GCoef = 0.587f;
constexpr float BCoef = 0.114f;

constexpr std::array<uint8_t, 3> DarkColor = {0, 255, 0};     // зелёный
constexpr std::array<uint8_t, 3> LightColor = {255, 0, 255};  // фиолетовый

constexpr int ColorChannels = 3;

}  // namespace

void FalseColor::Apply(BMP& image) const {
    auto& data = image.GetData();
    int width = image.GetWidth();
    int height = image.GetHeight();

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            size_t i =
                static_cast<size_t>(height - 1 - y) * width * ColorChannels + static_cast<size_t>(x) * ColorChannels;

            float r = static_cast<float>(data[i + 2]) / MaxColorValue;
            float g = static_cast<float>(data[i + 1]) / MaxColorValue;
            float b = static_cast<float>(data[i + 0]) / MaxColorValue;

            float intensity = RCoef * r + GCoef * g + BCoef * b;

            for (int c = 0; c < ColorChannels; ++c) {
                float blended = (1.0f - intensity) * static_cast<float>(DarkColor[c]) +
                                intensity * static_cast<float>(LightColor[c]);
                data[i + (2 - c)] = static_cast<uint8_t>(std::round(blended));
            }
        }
    }
}
