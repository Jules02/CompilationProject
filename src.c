typedef struct
{
    long x;
    long y;
} Point;

long main(long A, long B, long C)
{
    Point p;

    p.x = 4;
    p.y = 2;

    printf(A - B);
    long *ptrA;
    ptrA = &A;

    long *buffer;
    buffer = malloc();
    buffer = &A;
    printf(buffer);

    long sum = A + B;

    printf(sum);

    return (sum);
}
