// #include <stdio.h>
// #include <stdlib.h>
// #include <stdarg.h>
// #include <unistd.h>
#include <string>
#include <iostream>
#include <pigpio.h>

#include <filesystem>


/*
freq_count_1.c
2014-08-21
Public Domain

gcc -o freq_count_1 freq_count_1.c -lpigpio -lpthread
$ sudo ./freq_count_1  4 7 8

This program uses the gpioSetAlertFunc function to request
a callback (the same one) for each gpio to be monitored.

EXAMPLES

Monitor gpio 4 (default settings)
sudo ./freq_count_1  4

Monitor gpios 4 and 8 (default settings)
sudo ./freq_count_1  4 8

Monitor gpios 4 and 8, sample rate 2 microseconds
sudo ./freq_count_1  4 8 -s2

Monitor gpios 7 and 8, sample rate 4 microseconds, report every second
sudo ./freq_count_1  7 8 -s4 -r10

Monitor gpios 4,7, 8, 9, 10, 23 24, report five times a second
sudo ./freq_count_1  4 7 8 9 10 23 24 -r2

Monitor gpios 4, 7, 8, and 9, report once a second, sample rate 1us,
generate 2us edges (4us square wave, 250000 highs per second).
sudo ./freq_count_1  4 7 8 9 -r 10 -s 1 -p 2
*/


#define MAX_GPIOS 40

#define OPT_R_MIN 1
#define OPT_R_MAX 100
#define OPT_R_DEF 5

#define OPT_S_MIN 1
#define OPT_S_MAX 10
#define OPT_S_DEF 5

static volatile int g_pulse_count[MAX_GPIOS];
static volatile int g_reset_counts;

static uint32_t g_mask;

static int g_num_gpios;
static int g_gpio[MAX_GPIOS];

static int g_opt_r = OPT_R_DEF;
static int g_opt_s = OPT_S_DEF;
static std::string g_opt_f;

namespace fs = std::filesystem;

bool isValidFileToWrite(const std::string& filePath) {
    // Check if the path points to a regular file
    if (!fs::is_regular_file(filePath)) {
        std::cout << "Error: Not a regular file.\n";
        return false;
    }

    // Check if the file is writable
    if (!fs::is_writable(filePath)) {
        std::cout << "Error: File is not writable.\n";
        return false;
    }

    return true;
}


void usage()
{
   fprintf
   (stderr,
      "\n" \
      "Usage: sudo ./freq_count_1 gpio ... [OPTION] ...\n" \
      "   -f file_path, path of the file to save the data to\n" \
      "   -r value, sets refresh period in deciseconds, %d-%d, default %d\n" \
      "   -s value, sets sampling rate in micros, %d-%d, default %d\n" \
      "\nEXAMPLE\n" \
      "sudo ./freq_count_1 4 7 -r2 -s2\n" \
      "Monitor gpios 4 and 7.  Refresh every 0.2 seconds.  Sample rate 2 micros.\n" \
      "\n",
      OPT_R_MIN, OPT_R_MAX, OPT_R_DEF,
      OPT_S_MIN, OPT_S_MAX, OPT_S_DEF
   );
}

void fatal(int show_usage, char *fmt, ...)
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

static int initOpts(int argc, char *argv[])
{
   int i, opt;

   while ((opt = getopt(argc, argv, "s:r:f:")) != -1)
   {
      i = -1;

      switch (opt)
      {
         case 'f':
            g_opt_f = optarg;
            if !isValidFileToWrite(g_opt_f) fatal(1, "invalid file: %s", g_opt_f)
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

        default: /* '?' */
           usage();
           exit(-1);
        }
    }
   return optind;
}

void edges(int gpio, int level, uint32_t tick)
{
   int g;
   if (g_reset_counts)
   {
      g_reset_counts = 0;
      for (g=0; g<MAX_GPIOS; g++) g_pulse_count[g] = 0;
   }
    if (level == 1) g_pulse_count[gpio]++;
}

int main(int argc, char *argv[]){

    int rest;
    
    rest = initOpts(argc, argv);

    

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
































