#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <termios.h>
#include <unistd.h>
#include <stdint.h>
#include <time.h>
#include <math.h>
#include <seamaxlin.h>

SeaMaxLin *seaModule = NULL;

seaio_type_t	type;
address_loc_t	start;
address_range_t	range;

slave_address_t slaveId = 247;

unsigned char data[2] = {0, 0};

void print_binary(uint8_t number) {
    int bits = sizeof(number) * 8;
    
    for(int i = 5; i >= 0; i--) {
        putchar((number & (1U << i)) ? '1' : '0');
    }
    putchar('\n');
}

void transmit(uint8_t number) {
    type	= COILS;
	start	= 1;
	range	= 16;

    memset(&data, number, 1);
    int result = SeaMaxLinWrite(seaModule, slaveId, type, start, range, data);
}

int main(int argc, char** argv){

    char *port;
    double entropy;
    int freq;
    int ct;

    if(argc < 5){
        printf("Format: ./meter_sim [DAC port] [entropy] [frequency] [count]\n");
        printf("See LEAdge documentation for more information.\n");
        return -1;
    } else {
        port = argv[1];
        entropy = strtod(argv[2], NULL);
        freq = atoi(argv[3]);
        ct = atoi(argv[4]);
    }

    printf("Initializing SeaDAC... ");

    seaModule = SeaMaxLinCreate();

    char portString[100] = "sealevel_rtu:/";
    strcat(portString, port);

    int result = SeaMaxLinOpen(seaModule, portString);
    if (result != 0)
	{
		printf("ERROR: SeaDAC connection failed. Returned %d\n", result);
        printf("This is typically due to an incorrect port name. See documentation for details.\n");
		return -1;
	}
    printf("Success!\n\n");

    srand(time(NULL));
    uint8_t byte, prev_byte = 0;
    for(int i = 0 ; i < ct ; i++){
        prev_byte = byte;
        for(int k = 0 ; k < 6 ; k++){
            double roll = (double)rand() / (double)RAND_MAX;

            uint8_t mask = 1 << k;

            //if bit is 1
            if(byte & mask > 0){
                if(roll > entropy){
                    byte = byte & ~mask;
                }
                continue;
            } 
            //if bit is 0
            else {
                if(roll < entropy){
                    byte = byte ^ (1 << k);
                }
            }    
        }
        print_binary(byte);
        transmit(byte);
        usleep(freq * 1000);
    }

}



