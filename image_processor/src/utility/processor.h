#pragma once

#include "filter.h"
#include <vector>
#include <memory>

class Processor {
public:
    void AddFilter(std::unique_ptr<IFilter> filter);
    void Process(BMP& image) const;

private:
    std::vector<std::unique_ptr<IFilter>> filters_;
};
