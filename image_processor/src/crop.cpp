#include "utility/crop.h"

#include <algorithm>
#include <stdexcept>

namespace {
constexpr int ColorChannels = 3;
}  // namespace

Crop::Crop(const std::vector<std::string>& args) {
    if (args.size() != 2) {
        throw std::runtime_error("Crop need two parameters");
    }
    width_ = std::stoi(args[0]);
    height_ = std::stoi(args[1]);
}

void Crop::Apply(BMP& image) const {
    int32_t new_w = std::min(width_, image.GetWidth());
    int32_t new_h = std::min(height_, image.GetHeight());

    const size_t old_stride = static_cast<size_t>(image.GetWidth()) * ColorChannels;
    const size_t new_stride = static_cast<size_t>(new_w) * ColorChannels;
    std::vector<uint8_t> new_data(static_cast<size_t>(new_w) * new_h * ColorChannels);

    int start_y = image.GetHeight() - new_h;
    for (int y = 0; y < new_h; ++y) {

        std::copy_n(&image.GetData()[(start_y + y) * old_stride], new_stride, &new_data[y * new_stride]);
    }

    image = BMP(new_w, new_h);
    std::copy(new_data.begin(), new_data.end(), image.GetData().begin());
}
