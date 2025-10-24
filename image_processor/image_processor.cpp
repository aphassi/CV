#include <iostream>
#include <stdexcept>

#include "src/utility/bmp_encoder.h"
#include "src/utility/args.h"
#include "src/utility/filter.h"
#include "src/utility/processor.h"

int main(int argc, char** argv) {
    try {
        Args args(argc, argv);

        BMP image(args.GetInputFile());

        Processor processor;

        for (const auto& filter_info : args.GetFilters()) {
            auto f = CreateFilter(filter_info.GetName(), filter_info.GetParam());
            processor.AddFilter(std::move(f));
        }

        processor.Process(image);

        image.Save(args.GetOutputFile());

        std::cout << "Huraayyy! Image saved to: " << args.GetOutputFile() << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}
