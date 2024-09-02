// The Sieve of Eratosthenes
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int sieve_of_eratosthenes(int n) {
    if (n == 1) { return 2; }
    int limit = ceil(n * log(n) + n * log(log(n))); 
    // char *is_prime = calloc(limit + 1, sizeof(char)); 
    char *is_prime = (char*) calloc(limit + 1, sizeof(char));


    if (is_prime == NULL) {
        fprintf(stderr, "limit = %d\n", limit);
        fprintf(stderr, "Memory allocation failed.\n");
        exit(1);
    }

    int count = 1, i = 2;
    for (; i <= limit + 1; i++) {
        if (is_prime[i] == 0) { 
            if (count++ == n) break;
            for (int j = i * 2; j <= limit; j += i) is_prime[j] = 1;
        }
    }

    free(is_prime);
    return i;
}

int main(int argc, char ** argv) {
    if (argc != 2) {
        fprintf(stderr, "Invalid number of arguments\n");
        return 1;
    }
    int n = atoi(argv[1]);
    if (n <= 0) {
        fprintf(stderr, "Invalid input. Please enter a positive integer.\n");
        return 1;
    }

    int nth_prime = sieve_of_eratosthenes(n);
    printf("The prime no %d is: %d\n", n, nth_prime);
    return 0;
}

