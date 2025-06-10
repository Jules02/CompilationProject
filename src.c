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

long main(long A, long B, long C)
{
    long *ptrA;
    ptrA = &A;

    long *buffer;
    buffer = malloc();
    buffer = &A;

    long *ptrB;
    ptrB = &B;

    long sum = A + B;
    long sub = ptrA - C;

    Ligne line2 = line;

    printf(sum);
    printf(sub);

    return (sum + sub);
}
