typedef struct
{
    long x;
    long y;
} Point;

typedef struct
{
    Point src;
    Point tgt;
} Ligne;

typedef struct
{
    long x;
    double T;
    double Z;
} Test;

long main(long X, double Y, long Z)
{
    double E = 1.0e-10;

    /* Structs */
    Point p;

    /* Ponteiros */
    long *ptr;
    ptr = &Z; // endereço de variável

    long *buf;
    buf = malloc(); // alocação dinâmica (8 bytes)

    /* Loop e impressão */
    while (3 + X)
    {
        long T = 3 + X;
        printf(Y);
        Z = X + 4;
        X = X - 1;
    }

    return (Z);
}
