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
