#include "utility/blur.h"

#include <algorithm>
#include <cmath>
#include <vector>

namespace {

constexpr int KColorChannels = 3;
constexpr int KClampMin = 0;
constexpr int KClampMax = 255;
constexpr int KSigmaFactor = 3;
constexpr float KNew = 2.0f;

constexpr int KMaxRadius = 50;
int CalcRadius(float sigma) {
    if (sigma <= 0) {
        throw std::runtime_error("Sigma must be > 0");
    }
    int radius = static_cast<int>(std::ceil(static_cast<double>(sigma) * KSigmaFactor));
    if (radius < 1) {
        radius = 1;
    }
    if (radius > KMaxRadius) {
        radius = KMaxRadius;
    }
    return radius;
}

std::vector<float> Generate1DKernel(float sigma) {
    int radius = CalcRadius(sigma);
    int size = 2 * radius + 1;
    std::vector<float> center(size);

    double sum_d = 0.0;
    double param_blur = 1.0 / (KNew * static_cast<double>(sigma) * static_cast<double>(sigma));
    for (int i = -radius; i <= radius; ++i) {
        double val = std::exp(-static_cast<double>(i) * i * param_blur);
        center[i + radius] = static_cast<float>(val);
        sum_d += val;
    }
    for (float &v : center) {
        v /= static_cast<float>(sum_d);
    }
    return center;
}

inline uint8_t ToByte(float x) {
    int val = static_cast<int>(std::lround(x));
    if (val < KClampMin) {
        val = KClampMin;
    }
    if (val > KClampMax) {
        val = KClampMax;
    }
    return static_cast<uint8_t>(val);
}

}  // namespace

Blur::Blur(float sigma) : sigma_(sigma) {
}

void Blur::Apply(BMP &image) const {
    int width = image.GetWidth();
    int height = image.GetHeight();
    auto &data = image.GetData();
    std::vector<float> center = Generate1DKernel(sigma_);
    int radius = static_cast<int>(center.size()) / 2;
    std::vector<float> temp_f(data.size(), 0.0f);

    size_t row_s = static_cast<size_t>(width) * KColorChannels;
    for (int row = 0; row < height; ++row) {
        size_t row_offset = static_cast<size_t>(row) * row_s;

        for (int col = 0; col < width; ++col) {
            float vert_b = 0.0f;
            float vert_g = 0.0f;
            float vert_r = 0.0f;
            for (int dx = -radius; dx <= radius; ++dx) {
                int cx = col + dx;
                // clamp
                if (cx < 0) {
                    cx = 0;
                } else if (cx >= width) {
                    cx = width - 1;
                }
                float w = center[dx + radius];
                size_t idx = row_offset + static_cast<size_t>(cx) * KColorChannels;
                vert_b += static_cast<float>(data[idx + 0]) * w;
                vert_g += static_cast<float>(data[idx + 1]) * w;
                vert_r += static_cast<float>(data[idx + 2]) * w;
            }
            size_t idx_new = row_offset + static_cast<size_t>(col) * KColorChannels;
            temp_f[idx_new + 0] = vert_b;
            temp_f[idx_new + 1] = vert_g;
            temp_f[idx_new + 2] = vert_r;
        }
    }
    for (int col = 0; col < width; ++col) {
        for (int row = 0; row < height; ++row) {
            float vert_b = 0.0f;
            float vert_g = 0.0f;
            float vert_r = 0.0f;
            for (int dy = -radius; dy <= radius; ++dy) {
                int ry = row + dy;
                if (ry < 0) {
                    ry = 0;
                } else if (ry >= height) {
                    ry = height - 1;
                }

                float w = center[dy + radius];
                size_t idx = static_cast<size_t>(ry) * row_s + static_cast<size_t>(col) * KColorChannels;
                vert_b += temp_f[idx + 0] * w;
                vert_g += temp_f[idx + 1] * w;
                vert_r += temp_f[idx + 2] * w;
            }
            size_t idx_new = static_cast<size_t>(row) * row_s + static_cast<size_t>(col) * KColorChannels;
            data[idx_new + 0] = ToByte(vert_b);
            data[idx_new + 1] = ToByte(vert_g);
            data[idx_new + 2] = ToByte(vert_r);
        }
    }
}
