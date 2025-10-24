#include "utility/edge.h"
#include "utility/grayscale.h"

#include <algorithm>
#include <cmath>
#include <vector>

namespace {

constexpr int KMatrixSize = 3;
constexpr int KRadius = 1;
constexpr float KThresholdScale = 255.0f;
constexpr uint8_t KWhite = 255;
constexpr uint8_t KBlack = 0;
constexpr int KColorChannels = 3;

const float K_EDGE_KERNEL[KMatrixSize][KMatrixSize] = {{0, -1, 0}, {-1, 4, -1}, {0, -1, 0}};

}  // namespace

Edge::Edge(float threshold) : threshold_(threshold * KThresholdScale) {
}

void Edge::Apply(BMP& image) const {
    Grayscale gray;
    gray.Apply(image);

    int width = image.GetWidth();
    int height = image.GetHeight();
    auto& data = image.GetData();
    auto original = data;

    size_t row_stride = static_cast<size_t>(width) * KColorChannels;
    std::vector<uint8_t> result = data;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float sum = 0.0f;

            for (int dy = -KRadius; dy <= KRadius; ++dy) {
                for (int dx = -KRadius; dx <= KRadius; ++dx) {
                    int ny = std::clamp(y + dy, 0, height - 1);
                    int nx = std::clamp(x + dx, 0, width - 1);
                    size_t idx =
                        static_cast<size_t>(height - 1 - ny) * row_stride + static_cast<size_t>(nx) * KColorChannels;

                    float kernel_val = K_EDGE_KERNEL[dy + KRadius][dx + KRadius];
                    float intensity = static_cast<float>(original[idx]);  // grayscale: R = G = B
                    sum += kernel_val * intensity;
                }
            }

            uint8_t color = (sum > threshold_) ? KWhite : KBlack;
            size_t i = static_cast<size_t>(height - 1 - y) * row_stride + static_cast<size_t>(x) * KColorChannels;
            result[i + 0] = color;
            result[i + 1] = color;
            result[i + 2] = color;
        }
    }

    std::copy(result.begin(), result.end(), data.begin());
}
