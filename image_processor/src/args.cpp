#include "utility/args.h"

#include <stdexcept>
#include <ranges>

Args::Filter::Filter(std::string_view name, std::vector<std::string>&& param) : name_(name), param_(std::move(param)) {
}

const std::string& Args::Filter::GetName() const {
    return name_;
}

const std::vector<std::string>& Args::Filter::GetParam() const {
    return param_;
}

Args::Args(int argc, char* argvector[]) {
    if (argc < 3) {
        throw std::runtime_error("Too short for a filter");
    }

    input_file_ = argvector[1];
    output_file_ = argvector[2];

    int i = 3;
    while (i < argc) {
        std::string_view filter_name = argvector[i];

        if (filter_name.empty() || filter_name[0] != '-') {
            throw std::runtime_error("Filter name should start with '-'");
        }

        filter_name.remove_prefix(1);

        if (!NameChecking(filter_name)) {
            throw std::runtime_error("Not a filter: " + std::string(filter_name));
        }

        ++i;
        std::vector<std::string> params;

        while (i < argc && argvector[i][0] != '-') {
            params.emplace_back(argvector[i]);
            ++i;
        }

        filters_.emplace_back(filter_name, std::move(params));
    }
}

bool Args::NameChecking(std::string_view name) {
    return name == "crop" || name == "gs" || name == "neg" || name == "sharp" || name == "edge" || name == "blur" ||
           name == "falsecolor";
}

const std::string& Args::GetInputFile() const {
    return input_file_;
}

const std::string& Args::GetOutputFile() const {
    return output_file_;
}

const std::vector<Args::Filter>& Args::GetFilters() const {
    return filters_;
}
