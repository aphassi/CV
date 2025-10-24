#pragma once

#include <cstdint>
#include <fstream>
#include <string>
#include <vector>
#include <stdexcept>

#pragma pack(push, 1)
constexpr uint32_t BmpHeaderOffset = 54;
constexpr uint32_t BmpInfoHeaderSize = 40;
constexpr uint16_t BitsPerPixel24 = 24;
constexpr int32_t DefaultResolution = 11811;

struct BMPHeader {
    char type[2] = {'B', 'M'};
    uint32_t file_size = 0;
    uint16_t reserved_first = 0;
    uint16_t reserved_second = 0;
    uint32_t offset = BmpHeaderOffset;
};
struct BMPInfo {
    uint32_t header_size = BmpInfoHeaderSize;
    int32_t width = 0;
    int32_t height = 0;
    uint16_t planes = 1;
    uint16_t bit_count = BitsPerPixel24;
    uint32_t compression = 0;
    uint32_t size_image = 0;
    int32_t x_permeter = DefaultResolution;
    int32_t y_permeter = DefaultResolution;
    uint32_t colors_used = 0;
    uint32_t important_colors = 0;
};
#pragma pack(pop)

class BMP {
public:
    BMP() = default;
    explicit BMP(const std::string& filename);
    BMP(int32_t width, int32_t height);
    int32_t GetWidth() const;
    int32_t GetHeight() const;
    const std::vector<uint8_t>& GetData() const;
    std::vector<uint8_t>& GetData();

    void Pixel(int x, int y, uint8_t r, uint8_t g, uint8_t b);
    void Save(const std::string& filename) const;

private:
    void Read(const std::string& filename);
    void ValidateHeader();
    size_t GetRowS() const;

    BMPHeader header_;
    BMPInfo info_;
    std::vector<uint8_t> data_;
};
