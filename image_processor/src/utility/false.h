#pragma once

#include "filter.h"

class FalseColor : public IFilter {
public:
    FalseColor() = default;
    void Apply(BMP& image) const override;
};
