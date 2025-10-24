#include "utility/sharpen.h"
#include <algorithm>
#include <cmath>

namespace {

constexpr int KMatrixSize = 3;
constexpr int KRadius = 1;
constexpr float KMaxColorValue = 255.0f;

const float K_MATRIX[KMatrixSize][KMatrixSize] = {{0.0f, -1.0f, 0.0f}, {-1.0f, 5.0f, -1.0f}, {0.0f, -1.0f, 0.0f}};

uint8_t Clamp(float value) {
    return static_cast<uint8_t>(std::max(0.0f, std::min(KMaxColorValue, value)));
}

}  // namespace

void Sharpen::Apply(BMP& image) const {
    const int width = image.GetWidth();
    const int height = image.GetHeight();
    const auto& data = image.GetData();
    std::vector<uint8_t> result = data;

    const size_t row_size = static_cast<size_t>(width) * 3;

    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            float sum_r = 0.0f;
            float sum_g = 0.0f;
            float sum_b = 0.0f;

            for (int y_line = -KRadius; y_line <= KRadius; ++y_line) {
                for (int x_line = -KRadius; x_line <= KRadius; ++x_line) {
                    const int matrix_y = std::clamp(y + y_line, 0, height - 1);
                    const int matrix_x = std::clamp(x + x_line, 0, width - 1);

                    const size_t index = static_cast<size_t>((height - 1 - matrix_y) * row_size + matrix_x * 3);
                    const float weight = K_MATRIX[y_line + KRadius][x_line + KRadius];

                    sum_b += weight * static_cast<float>(data[index + 0]);
                    sum_g += weight * static_cast<float>(data[index + 1]);
                    sum_r += weight * static_cast<float>(data[index + 2]);
                }
            }

            const size_t target = static_cast<size_t>((height - 1 - y) * row_size + x * 3);
            result[target + 0] = Clamp(sum_b);
            result[target + 1] = Clamp(sum_g);
            result[target + 2] = Clamp(sum_r);
        }
    }

    std::copy(result.begin(), result.end(), image.GetData().begin());
}
