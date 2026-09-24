// #include <stdio.h>
// #include <stdlib.h>
// #include <stdarg.h>
// #include <unistd.h>
#include <string>
#include <iostream>
#include <pigpio.h>
#include <cstdarg>
#include <filesystem>
#include <cstdlib>
#include <unistd.h>
#include <chrono>
#include <fstream>
#include <thread>
#include <atomic>


#define MAX_EVENTS 10000
#define MAX_GPIOS 40

#define OPT_R_MIN 1
#define OPT_R_MAX 100000
#define OPT_R_DEF 1000

#define OPT_S_MIN 1
#define OPT_S_MAX 10
#define OPT_S_DEF 5

// Global file stream objects for logging and data
std::ofstream logFile;
std::ofstream dataFile;

std::atomic<bool> request_received(false);
std::atomic<bool> exit_condition(false);
std::atomic<int> latest_number(0);

std::string dataFilename;

static volatile int g_pulse_count[MAX_GPIOS];
static volatile int g_reset_counts;

static int g_num_gpios;
static int g_gpio[MAX_GPIOS];

static int g_opt_r = OPT_R_DEF;
static int g_opt_s = OPT_S_DEF;
static std::string g_opt_f;
static bool subp = false;
static bool savedata = false;

static uint32_t n_events = 0;
namespace fs = std::filesystem;
static int channel_array[MAX_EVENTS];
static uint32_t tick_array[MAX_EVENTS];


int width = 10;

void handle_requests() {
    std::string request;
    while (true) {
        std::getline(std::cin, request);
        if (request == "GET") {
            request_received = true;
        }
        if (request == "STOP") {
             exit_condition = true;
             break;
        }
    }
}


std::string prependPath(const std::string& pathString) {
    if (pathString.find('/') == std::string::npos && pathString.find('\\') == std::string::npos) {
        return "./" + pathString;
    }
    return pathString;
}


// Function to get the current timestamp in a specific format
std::string getCurrentTimestamp() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_c = std::chrono::system_clock::to_time_t(now);
    std::tm tm = *std::localtime(&now_c);
    std::stringstream ss;
    ss << std::put_time(&tm, "%Y%m%d_%H%M%S");
    return ss.str();
}

// Function to log data
void log_data(const std::string& message) {
        
        if (savedata){
            if (dataFile.is_open()) {
                dataFile << message << std::endl;
            } else {
                std::cerr << "Data file is not open." << std::endl;
            }
        }
       
        //if (not subp) std::cout << "\r" << message << std::flush;
}

void show_progress(const std::string& message) {
        
        /*if (savedata){
            if (dataFile.is_open()) {
                dataFile << message << std::endl;
            } else {
                std::cerr << "Data file is not open." << std::endl;
            }
        }*/
       
        std::cout << "\r" << message << std::flush;
}


// Function to log information
void log_info(const std::string& message, bool logToFile) {
    if (logToFile) {
        if (logFile.is_open()) {
            logFile << message << std::endl;
        } else {
            std::cerr << "Log file is not open." << std::endl;
        }
    } 
    
    if(not subp) {
        // Print to console
        std::cout << message << std::endl;
    }
}

int createDataFile(){

    // Ensure the logs directory exists
    std::filesystem::path dataDir = "/home/lhep/acm/data";
    if (!std::filesystem::exists(dataDir)) {
        std::filesystem::create_directory(dataDir);
    }

    // Open the log file in append mode
    dataFilename = "/home/lhep/acm/data/" + getCurrentTimestamp() + "_" + g_opt_f +".txt";
    dataFile.open(dataFilename, std::ios_base::app);
    if (!dataFile.is_open()) {
        std::cerr << "Unable to open data file: " << dataFilename << std::endl;
        return -1; // Exit if log file cannot be opened
    }

    // Log the creation of the log file
    log_info("Data file created: " + dataFilename, subp);

    
    return 0;
}

int writeHeader(){

     std::ostringstream  str;

     str << std::setw(width) << std::right << "ticks";
     str << "," << std::setw(width) << std::right << "channel";
    
    /* for (int i=0; i<g_num_gpios; i++){
         std::ostringstream  gpio_str;
         gpio_str << "GPIO_" << g_gpio[i];
         str << "," << std::setw(width) << std::right << gpio_str.str();
     }*/

    if (savedata){
        if (dataFile.is_open()) {
            dataFile << "dwell time [ms]: " + std::to_string(g_opt_r) << std::endl;
            dataFile << "GPIO clock period [us]: " + std::to_string(g_opt_s) << std::endl;
            dataFile << str.str() << std::endl;

        } else {
            std::cerr << "Data file is not open." << std::endl;
        }
    }
    
    if (not subp) std::cout << str.str() << std::endl;
    
    return 0;
}



int createLogFile(){

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
        return -1; // Exit if log file cannot be opened
    }

    // Log the creation of the log file
    log_info("Log file created: " + logFilename, subp);
    
    return 0;
}



bool isValidPathToWrite(const std::string& pathString) {

    fs::path filePath = prependPath(pathString);
    
    // Check if the parent path exists and is writable
    if (!fs::exists(filePath.parent_path()) || !fs::is_directory(filePath.parent_path())) {
        std::cerr << "Parent directory does not exist or is not a directory." << std::endl;
        return false;
    }
    
    // Check if the file doesn't exist or if it's a regular file and writable
    if (!fs::exists(filePath) || 
        (fs::is_regular_file(filePath) && 
         (fs::status(filePath).permissions() & fs::perms::owner_write) == fs::perms::owner_write) ) {
        return true;
    } else {
        std::cerr << "File exists or is not writable." << std::endl;
        return false;
    }
}




void usage()
{
   fprintf
   (stderr,
      "\n" \
      "Usage: sudo ./counting-code gpio ... [OPTION] ...\n" \
      "   -f file_path, path of the file to save the data to\n" \
      "   -r value, sets refresh period in deciseconds, %d-%d, default %d\n" \
      "   -s value, sets sampling rate in micros, %d-%d, default %d\n" \
      "   -c, indicates that the progrm is launched as a subprocess from the GUI application"\
      "\nEXAMPLE\n" \
      "sudo ./freq_count_1 4 7 -r2 -s2\n" \
      "Monitor gpios 4 and 7.  Refresh every 0.2 seconds.  Sample rate 2 micros.\n" \
      "\n",
      OPT_R_MIN, OPT_R_MAX, OPT_R_DEF,
      OPT_S_MIN, OPT_S_MAX, OPT_S_DEF
   );
}

void fatal(int show_usage, const char *fmt, ...)
{
   char buf[128];
   va_list ap;

   va_start(ap, fmt);
   vsnprintf(buf, sizeof(buf), fmt, ap);
   va_end(ap);

   fprintf(stderr, "%s\n", buf);

   if (show_usage) usage();

   fflush(stderr);

   exit(EXIT_FAILURE);
}


int printout_parameters() {
    log_info("Parameters:", subp);
    log_info("----------", subp);
    log_info("g_opt_r: " + std::to_string(g_opt_r), subp);
    log_info("g_opt_s: " + std::to_string(g_opt_s), subp);
    log_info("g_opt_f: " + g_opt_f, subp);
    
    return 0;
    
    }


static int initOpts(int argc, char *argv[])
{
   int i, opt;

   while ((opt = getopt(argc, argv, "s:r:f:c")) != -1)
   {
      i = -1;

      switch (opt)
      {
         case 'f':
            g_opt_f = optarg;
            if (!isValidPathToWrite(g_opt_f.c_str())) fatal(1, "invalid file: %s", g_opt_f);
            savedata = true;
            break;

         case 'r':
            i = atoi(optarg);
            if ((i >= OPT_R_MIN) && (i <= OPT_R_MAX))
               g_opt_r = i;
            else fatal(1, "invalid -r option (%d)", i);
            break;

         case 's':
            i = atoi(optarg);
            if ((i >= OPT_S_MIN) && (i <= OPT_S_MAX))
               g_opt_s = i;
            else fatal(1, "invalid -s option (%d)", i);
            break;
            
        case 'c':
            subp = true;
            break;

        default: /* '?' */
           usage();
           exit(-1);
        }
    }   
    
    return optind;
}
    
int obtainGPIO(int rest, int argc, char *argv[]){
    std::ostringstream  str;
    int g;
   
    g_num_gpios = 0 ;
    for (int i=rest; i<argc; i++) {
        g = atoi(argv[i]);
        if (not ((g>=0) && (g<MAX_GPIOS))) fatal (1 , "%d is not a valid g_gpio number\n" , g) ;
        if (g_num_gpios == 0) {
                str << "Monitoring gpio " << g;
            }
        else{
                str << ", " << g;
        }
        g_gpio[g_num_gpios ++] = g; 
    }
    log_info(str.str(), subp);

    if (!g_num_gpios) fatal(1, "At least one gpio must be specified"); 
    
    return 0;
}



void edges(int gpio, int level, uint32_t tick)
{

   
   int g;
   /*if (g_reset_counts)
   {
      g_reset_counts = 0;
      for (g=0; g<MAX_GPIOS; g++) g_pulse_count[g] = 0;
   }*/
    if (level == 1) {
        //g_pulse_count[gpio]++;
        if (n_events< MAX_EVENTS){
            tick_array[n_events] = tick;
            channel_array[n_events] = gpio;
            n_events++;
        }
    }

}


int main(int argc, char *argv[]){

    int rest = initOpts(argc, argv);
    
    if (subp) {// only in the case it is launched from GUI (subp = True)
        if (createLogFile() < 0) return 1;
        // Start the request handler thread
        std::thread request_thread(handle_requests);
        request_thread.detach();  // Detach the thread to run independently
    }
    
    printout_parameters();

    //std::cout << "obtainGPIO" << std::endl;

    obtainGPIO(rest, argc, argv);    

    //std::cout << "if savedata..." << std::endl;

    
    if (savedata){
        //std::cout << "createDataFile" << std::endl;

        if (createDataFile()<0) return 1;
        if (subp) std::cout << dataFilename << std::endl;
        
    }

    //std::cout << "writeHeader" << std::endl;

    
    writeHeader();
    auto start_time = std::chrono::system_clock::now();


    gpioCfgClock ( g_opt_s , 1 , 1) ;
    if ( gpioInitialise () <0) return 1;

    for (int i=0; i<g_num_gpios; i++){
             gpioSetAlertFunc(g_gpio[i], edges);
             gpioSetMode ( g_gpio[i] , PI_INPUT) ;
        }
    
    g_reset_counts = 1;
    uint32_t n_events_written = 0;
    while (true){


        for (int i = n_events_written; i < n_events; i++){
            std::ostringstream  result;
            result << std::setw(width) << std::right << tick_array[i];
            result << "," << std::setw(2) << std::right << channel_array[i];
            std::ostringstream  display_text;
            display_text << n_events_written << " / " << MAX_EVENTS;
            
            log_data(result.str());
            show_progress(display_text.str());
            n_events_written++;
        }

        /*
        std::ostringstream result;
        auto time_now = std::chrono::system_clock::now();
        double elapsed_seconds = std::chrono::duration<double>(time_now - start_time).count();

        result << std::setw(width) << std::right << std::fixed << std::setprecision(3)<<elapsed_seconds;
         for (int i=0; i<g_num_gpios; i++){
             result << "," << std::setw(width) << std::right << g_pulse_count[g_gpio[i]];    
         }
        */
        
        
        if(exit_condition){
        
            std::cout << "exit condition received" << std::endl;
            break;
        }

        if(n_events_written >= MAX_EVENTS) {
            std::cout << "Max events reached" << std::endl;
            break;

        }
        
        // Check if a request has been received
        /*if (request_received) {
            request_received = false;  // Reset the flag
            std::cout << result.str() << std::endl;
            std::flush(std::cout);  // Ensure the output is sent immediately
        }*/
        
        
        
        //log_data(result.str());
        //g_reset_counts = 1;
        
        
        
        //delay in microseconds
        gpioDelay(g_opt_r * 1000);
    
    }
    std::cout << "while loop terminated" << std::endl;


    for (int i=0; i<g_num_gpios; i++) gpioSetAlertFunc(g_gpio[i], NULL);
    sleep(0.1);

    gpioTerminate();
    
    std::cout << "terminating..." << std::endl;

    if(not subp){
        std::cout << std::endl;
    }

}



/*int main(int argc, char *argv[])
{
   int i, rest, g, wave_id, mode;
   gpioPulse_t pulse[2];
   int count[MAX_GPIOS];
   int counter[MAX_GPIOS];
    
     
    
    char fileName[256];
    char filename[256];

    printf("Please enter filename: \n");
    scanf("%s", &fileName);
    sprintf(filename, "%s.txt", fileName); 
    FILE *fp = fopen(filename , "a") ; 
    printf ( "\n" ) ;

    char buffer [20]; 
    struct tm *sTm;

    time_t now = time (0);
    sTm = gmtime (&now) ;

    strftime (buffer, sizeof(buffer), "%Y−%m−%d%H:%M:%S", sTm);
    fprintf(fp,"\n %s\n", buffer, "\t starting time");

    rest = initOpts(argc, argv);

    g_num_gpios = 0 ;

    for (i=rest; i<argc; i++) {
        g = atoi(argv[i]);
        if ((g>=0) && (g<MAX_GPIOS)) {
           g_gpio[g_num_gpios ++] = g; g_mask |= (1<<g) ;
           }
        else fatal (1 , "%d is not a valid g_gpio number\n" , g) ;
        }

    if (!g_num_gpios) fatal(1, "At least one gpio must be specified"); 
    printf("Monitoring gpios");
    fprintf(fp, "Monitoring gpios");

    for (i=0; i<g_num_gpios; i++){ 
        printf(" %d", g_gpio[i]); 
        fprintf(fp, " %d", g_gpio[i]);
        }
    printf ( "\nSample rate %d micros , refresh rate %d deciseconds\n" , g_opt_s , g_opt_r ) ;
    fprintf (fp , "\nSample rate %d micros , refresh rate %d deciseconds\n" , g_opt_s , g_opt_r ) ;

    for (i=0; i<g_num_gpios; i++){
             counter[i]=0;
        }
    
    gpioCfgClock ( g_opt_s , 1 , 1) ;

    if ( gpioInitialise () <0) return 1;

    gpioWaveClear ( ) ;
    
    pulse [ 0 ] . gpioOn = g_mask ; 
    pulse [0]. gpioOff = 0; 
    pulse[0].usDelay = g_opt_p;
    
    pulse[1].gpioOn = 0;
    pulse[1].gpioOff = g_mask;
    pulse[1].usDelay = g_opt_p;

    gpioWaveAddGeneric(2, pulse);

    wave_id = gpioWaveCreate();

    for (i=0; i<g_num_gpios; i++) gpioSetAlertFunc(g_gpio[i], edges);

    mode = PI_INPUT;

    if ( g_opt_t ) {
       gpioWaveTxSend ( wave_id , PI_WAVE_MODE_REPEAT) ;
       mode = PI_OUTPUT;
       }
    fprintf(fp,"\n\n");
    fprintf(fp,"time [s]");
    printf("\n\n");
    printf("time [s]");

    for (i=0; i<g_num_gpios; i++){ 
        gpioSetMode ( g_gpio [i] , mode) ;
        printf ("\t %d \t\t", g_gpio[i]);
        fprintf(fp,"\t %d \t\t", g_gpio[i]);
     }
     fprintf(fp, "\n\n");
     printf("\n\n");

     double time = 0;
     
     while (1) 
     {

       for (i=0; i<g_num_gpios; i++) count[i] = g_pulse_count[g_gpio[i]];

       g_reset_counts = 1;

       for (i=0; i<g_num_gpios; i++)
       {
         fprintf(fp, " %5.2f", time);
         printf(" %5.2f", time);
         for (i=0; i<g_num_gpios; i++){
             counter[i]=counter[i]+count[i];
             printf("\t\t\t %d ", counter[i]);
             fprintf(fp, "\t\t\t %d ", counter[i]);

        }
       fprintf (fp, "\n");
       printf ("\n");
       gpioDelay(g_opt_r * 100000);
       
       time += 01 * g_opt_r;
       }
       }

       gpioTerminate();
       
       fclose(fp);
       }*/
































