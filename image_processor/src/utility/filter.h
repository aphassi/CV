#pragma once

#include "bmp_encoder.h"
#include <memory>
#include <string>
#include <vector>

class IFilter {
public:
    virtual void Apply(BMP& image) const = 0;
    virtual ~IFilter() = default;
};

std::unique_ptr<IFilter> CreateFilter(const std::string& name, const std::vector<std::string>& args);
