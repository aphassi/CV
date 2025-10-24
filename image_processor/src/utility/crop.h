#pragma once

#include "filter.h"

class Crop : public IFilter {
public:
    explicit Crop(const std::vector<std::string>& args);
    void Apply(BMP& image) const override;

private:
    int width_;
    int height_;
};
