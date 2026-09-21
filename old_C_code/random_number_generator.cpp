#include <iostream>
#include <cstdlib>
#include <ctime>
#include <unistd.h>
#include <string>
#include <thread>
#include <atomic>

std::atomic<bool> request_received(false);
std::atomic<int> latest_number(0);

void handle_requests() {
    std::string request;
    while (true) {
        std::getline(std::cin, request);
        if (request == "GET") {
            request_received = true;
        }
    }
}

int main() {
    std::srand(std::time(0)); // Seed the random number generator

    // Start the request handler thread
    std::thread request_thread(handle_requests);
    request_thread.detach();  // Detach the thread to run independently

    while (true) {
        // Generate a random number
        latest_number = std::rand() % 100;

        // Check if a request has been received
        if (request_received) {
            request_received = false;  // Reset the flag
            std::cout << latest_number << std::endl;
            std::flush(std::cout);  // Ensure the output is sent immediately
        }

        usleep(500000); // Sleep for 500ms (0.5 seconds)
    }

    return 0;
}
