// The Sieve of Eratosthenes
#include <Python.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

int sieve_of_eratosthenes(int n) {
  if (n <= 1) {
    return 2;
  }
  int limit = ceil(n * log(n) + n * log(log(n)));
  char *is_prime = (char *)calloc(limit + 1, sizeof(char));

  if (is_prime == NULL) {
    fprintf(stderr, "limit = %d\n", limit);
    fprintf(stderr, "Memory allocation failed.\n");
    exit(1);
  }

  int count = 1, i = 2;
  for (; i <= limit + 1; i++) {
    if (is_prime[i] == 0) {
      if (count++ == n)
        break;
      for (int j = i * 2; j <= limit; j += i)
        is_prime[j] = 1;
    }
  }

  free(is_prime);
  return i;
}

static PyObject *sieve(PyObject *self, PyObject *args) {
  int i;
  PyArg_ParseTuple(args, "i", &i);
  int nth_prime = sieve_of_eratosthenes(i);
  return PyLong_FromLong(nth_prime);
}

static PyMethodDef TimerMethods[] = {
    {"sieve", sieve, METH_VARARGS, "Computes the sieve"},
    {NULL, NULL, 0, NULL} // Sentinel
};

static struct PyModuleDef timer_module = {
    PyModuleDef_HEAD_INIT,
    "jpamb.timer", // Module name
    "A timer module",
    -1, // Size of per-interpreter state of the module
    TimerMethods};

PyMODINIT_FUNC PyInit_timer(void) { return PyModule_Create(&timer_module); }
