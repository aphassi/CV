#pragma once

#include "filter.h"

class Edge : public IFilter {
public:
    explicit Edge(float threshold);
    void Apply(BMP& image) const override;

private:
    float threshold_;
};
