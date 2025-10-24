#pragma once

#include "filter.h"

class Blur : public IFilter {
public:
    explicit Blur(float sigma);
    void Apply(BMP& image) const override;

private:
    float sigma_;
};
