#include "utility/grayscale.h"
#include <cmath>

namespace {

constexpr float MaxColorFloat = 255.0f;
constexpr float GrayscaleRCoeff = 0.299f;
constexpr float GrayscaleGCoeff = 0.587f;
constexpr float GrayscaleBCoeff = 0.114f;

}  // namespace

void Grayscale::Apply(BMP& image) const {
    auto& data = image.GetData();
    const int width = image.GetWidth();
    const int height = image.GetHeight();

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            const size_t i = static_cast<size_t>((height - 1 - y) * width * 3 + x * 3);

            const float r = static_cast<float>(data[i + 2]) / MaxColorFloat;
            const float g = static_cast<float>(data[i + 1]) / MaxColorFloat;
            const float b = static_cast<float>(data[i + 0]) / MaxColorFloat;

            const float intensity = GrayscaleRCoeff * r + GrayscaleGCoeff * g + GrayscaleBCoeff * b;

            const uint8_t gray = static_cast<uint8_t>(std::round(intensity * MaxColorFloat));
            data[i + 0] = data[i + 1] = data[i + 2] = gray;
        }
    }
}
