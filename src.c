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
    printf(buffer);

    long *ptrB;
    ptrB = &B;

    long sum = A + B;
    long sub = ptrA - C;

    printf(sum);
    printf(sub);

    return (sum + sub);
}
