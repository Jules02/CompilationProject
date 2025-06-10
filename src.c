typedef struct
{
    long x;
    double y;
} Point;

long main(long A, long B, long C)
{
    long sum = A + C;
    printf(sum);
    printf(A - B);

    Point p;

    printf(p.x);
    printf(p.y);

    p.x = 4;
    p.y = 2.0;

    printf(p.x);
    printf(p.y);

    long *ptrA;
    ptrA = &A;

    printf(ptrA);
    printf(*ptrA);

    long *buffer;
    buffer = malloc();
    buffer = &A;
    printf(buffer);

    return (sum);
}
