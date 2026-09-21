#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <ctime>
#include <chrono>
#include <iomanip>
#include <filesystem>

// Global variables for demonstration
int g_opt_r = 10;
int g_opt_s = 20;
int g_opt_f = 30;
// Global file stream object for logging
std::ofstream logFile;

// Function to get the current timestamp in a specific format
std::string getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_c = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&now_c);
    std::stringstream ss;
    ss << std::put_time(&tm, "%Y%m%d_%H%M%S");
    return ss.str();
}

// Function to log information
void log_info(const std::string& message, bool logToFile) {
    if (logToFile) {
        if (logFile.is_open()) {
            logFile << message << std::endl;
        } else {
            std::cerr << "Log file is not open." << std::endl;
        }
    } else {
        // Print to console
        std::cout << message << std::endl;
    }
}


// Function to create and open the log file
bool createLogFile() {
    // Ensure the logs directory exists
    std::filesystem::path logDir = "logs";
    if (!std::filesystem::exists(logDir)) {
        std::filesystem::create_directory(logDir);
    }

    // Open the log file in append mode
    std::string logFilename = "logs/" + getCurrentTimestamp() + "_log.txt";
    logFile.open(logFilename, std::ios_base::app);
    if (!logFile.is_open()) {
        std::cerr << "Unable to open log file: " << logFilename << std::endl;
        return false; // Return false if log file cannot be opened
    }

    // Log the creation of the log file
    log_info("Log file created: " + logFilename, true);
    return true; // Return true if log file is successfully opened
}


// Function to log or print parameters
int printout_parameters(bool logToFile) {
    log_info("Parameters:", logToFile);
    log_info("----------", logToFile);
    log_info("g_opt_r: " + std::to_string(g_opt_r), logToFile);
    log_info("g_opt_s: " + std::to_string(g_opt_s), logToFile);
    log_info("g_opt_f: " + std::to_string(g_opt_f), logToFile);
    
    return 0;
}


int main(int argc, char* argv[]) {
    // Check for the -log flag
    bool logToFile = false;
    if (argc > 1 && std::string(argv[1]) == "-log") {
        logToFile = true;
    }

    // Prepare for logging to file if the -log flag is present
    if (logToFile) {
        if (!createLogFile()) {
            return 1; // Exit if log file cannot be opened
        }
    }

    // Example usage of printout_parameters function
    printout_parameters(logToFile);

    // Log different messages during the program execution
    log_info("Execution information: Program started.", logToFile);
    log_info("Performing some operations...", logToFile);
    log_info("Execution information: Program finished.", logToFile);

    // Close the log file if it was opened
    if (logFile.is_open()) {
        logFile.close();
    }

    return 0;
}
