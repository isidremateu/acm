#include <iostream>
#include <unistd.h>

int main(int argc, char *argv[]) {
    int opt;
    bool flagA = false;
    bool flagB = false;
    
    while ((opt = getopt(argc, argv, "ab")) != -1) {
        switch (opt) {
            case 'a':
                flagA = true;
                break;
            case 'b':
                flagB = true;
                break;
            default:
                std::cerr << "Usage: " << argv[0] << " [-a] [-b]" << std::endl;
                return 1;
        }
    }
    
    std::cout << "Flag A: " << (flagA ? "set" : "not set") << std::endl;
    std::cout << "Flag B: " << (flagB ? "set" : "not set") << std::endl;
    
    return 0;
}
