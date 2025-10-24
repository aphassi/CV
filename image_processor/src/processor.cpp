#include "utility/processor.h"

void Processor::AddFilter(std::unique_ptr<IFilter> filter) {
    filters_.push_back(std::move(filter));
}

void Processor::Process(BMP& image) const {
    for (const auto& filter : filters_) {
        filter->Apply(image);
    }
}
