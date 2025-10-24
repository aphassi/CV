#pragma once

#include "filter.h"
#include <vector>

class Sharpen : public IFilter {
public:
    void Apply(BMP& image) const override;
};
