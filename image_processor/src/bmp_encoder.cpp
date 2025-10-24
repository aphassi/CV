#include "bmp_encoder.h"
namespace {
constexpr int KRowAlignment = 4;
constexpr int KColorChannels = 3;
}  // namespace
BMP::BMP(const std::string& filename) {
    Read(filename);
}

BMP::BMP(int32_t width, int32_t height) {
    if (width <= 0 || height <= 0) {
        throw std::runtime_error("Width and height must cannot be < 0");
    }

    info_.width = width;
    info_.height = height;
    info_.bit_count = BitsPerPixel24;
    info_.compression = 0;
    info_.planes = 1;
    info_.header_size = sizeof(BMPInfo);
    info_.x_permeter = DefaultResolution;
    info_.y_permeter = DefaultResolution;
    info_.colors_used = 0;
    info_.important_colors = 0;

    size_t row_ss = static_cast<size_t>(width) * KColorChannels;
    size_t padding = (KRowAlignment - (row_ss % KRowAlignment)) % KRowAlignment;
    info_.size_image = static_cast<uint32_t>((row_ss + padding) * height);

    header_.type[0] = 'B';
    header_.type[1] = 'M';
    header_.offset = sizeof(BMPHeader) + sizeof(BMPInfo);
    header_.file_size = header_.offset + info_.size_image;
    header_.reserved_first = 0;
    header_.reserved_second = 0;

    data_.resize(row_ss * height);
}

int32_t BMP::GetWidth() const {
    return info_.width;
}

int32_t BMP::GetHeight() const {
    return info_.height;
}

const std::vector<uint8_t>& BMP::GetData() const {
    return data_;
}
std::vector<uint8_t>& BMP::GetData() {
    return data_;
}

void BMP::Read(const std::string& filename) {
    std::ifstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot open this file: " + filename);
    }

    file.read(reinterpret_cast<char*>(&header_), sizeof(BMPHeader));
    file.read(reinterpret_cast<char*>(&info_), sizeof(BMPInfo));

    ValidateHeader();

    const size_t row_size = GetRowS();
    const size_t data_size = row_size * info_.height;
    data_.resize(data_size);

    file.seekg(header_.offset, std::ios::beg);

    for (int32_t y = 0; y < info_.height; ++y) {
        file.read(reinterpret_cast<char*>(&data_[y * row_size]), static_cast<std::streamsize>(row_size));
        if (info_.width % KRowAlignment != 0) {
            file.seekg(info_.width % KRowAlignment, std::ios::cur);
        }
    }
}

void BMP::ValidateHeader() {
    if (header_.type[0] != 'B' || header_.type[1] != 'M') {
        throw std::runtime_error("Strange file");
    }
    if (info_.bit_count != BitsPerPixel24) {
        throw std::runtime_error("Only 24-bit");
    }
    if (info_.compression != 0) {
        throw std::runtime_error("Only uncompressed");
    }
}

size_t BMP::GetRowS() const {
    return static_cast<size_t>(info_.width) * KColorChannels;
}

void BMP::Pixel(int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    size_t row_size = GetRowS();
    size_t index = static_cast<size_t>(info_.height - 1 - y) * row_size + x * KColorChannels;
    if (index + 2 >= data_.size()) {
        throw std::out_of_range("Pixel coordinate out of range");
    }
    data_[index + 0] = b;
    data_[index + 1] = g;
    data_[index + 2] = r;
}

void BMP::Save(const std::string& filename) const {
    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Unable to open file: " + filename);
    }

    BMPHeader header = header_;
    BMPInfo info = info_;
    size_t row_size = GetRowS();
    size_t padding = (KRowAlignment - (row_size % KRowAlignment)) % KRowAlignment;
    size_t data_size = (row_size + padding) * info_.height;

    header.file_size = sizeof(BMPHeader) + sizeof(BMPInfo) + data_size;
    info.size_image = static_cast<uint32_t>(data_size);

    file.write(reinterpret_cast<const char*>(&header), sizeof(BMPHeader));
    file.write(reinterpret_cast<const char*>(&info), sizeof(BMPInfo));

    for (int32_t y = 0; y < info.height; ++y) {
        file.write(reinterpret_cast<const char*>(&data_[y * row_size]), static_cast<std::streamsize>(row_size));
        if (padding > 0) {
            static constexpr uint8_t Pad[KRowAlignment] = {0, 0, 0, 0};
            file.write(reinterpret_cast<const char*>(Pad), static_cast<std::streamsize>(padding));
        }
    }
}

//(2*3)%4 просто двигаем коретка file.seekg 1 argument - wight % 4, 2 - argumnet - std::ious:cur
