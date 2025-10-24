#pragma once

#include "filter.h"

class Negative : public IFilter {
public:
    void Apply(BMP& image) const override;
};