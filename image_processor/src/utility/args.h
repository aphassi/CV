#pragma once

#include <string>
#include <string_view>
#include <vector>
#include <ranges>

class Args {
public:
    class Filter {
    public:
        Filter(std::string_view name, std::vector<std::string>&& param);
        const std::string& GetName() const;
        const std::vector<std::string>& GetParam() const;

    private:
        std::string name_;
        std::vector<std::string> param_;
    };

public:
    Args() = default;
    Args(int argc, char* argvector[]);

    const std::string& GetInputFile() const;
    const std::string& GetOutputFile() const;
    const std::vector<Filter>& GetFilters() const;

private:
    static bool NameChecking(std::string_view name);

private:
    std::string input_file_;
    std::string output_file_;
    std::vector<Filter> filters_;
};
