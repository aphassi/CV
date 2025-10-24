#include "utility/negative.h"
constexpr uint8_t MaxColor = 255;
void Negative::Apply(BMP& image) const {
    auto& data = image.GetData();
    for (auto& bit : data) {
        bit = MaxColor - bit;
    }
}
