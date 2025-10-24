#include "utility/filter.h"

#include "crop.h"
#include "grayscale.h"
#include "negative.h"
#include "sharpen.h"
#include "edge.h"
#include "blur.h"
#include "false.h"
#include <stdexcept>

std::unique_ptr<IFilter> CreateFilter(const std::string& name, const std::vector<std::string>& args) {
    if (name == "crop") {
        return std::make_unique<Crop>(args);
    } else if (name == "gs") {
        return std::make_unique<Grayscale>();
    } else if (name == "neg") {
        return std::make_unique<Negative>();
    } else if (name == "sharp") {
        return std::make_unique<Sharpen>();
    } else if (name == "edge") {
        if (args.size() != 1) {
            throw std::runtime_error("Edge filter need one parameter");
        }
        return std::make_unique<Edge>(std::stof(args[0]));
    } else if (name == "blur") {
        if (args.size() != 1) {
            throw std::runtime_error("Blur filter need one parameter");
        }
        return std::make_unique<Blur>(std::stof(args[0]));
    } else if (name == "falsecolor") {
        return std::make_unique<FalseColor>();
    }

    throw std::runtime_error("Unknown filter: " + name);
}
