#pragma once

#include "filter.h"

class Grayscale : public IFilter {
public:
    void Apply(BMP& image) const override;
};
