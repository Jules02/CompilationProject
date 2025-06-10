typedef struct {
    long x;
    long y;
} Point;

long main(long A, long B, long C)
{
    Point p;
    printf(p.x);

    long *ptrA;
    ptrA = &A;

    long *buffer;
    buffer = malloc();

    long sum = A + B;
    long sub = ptrA - C;

    printf(sum);
    printf(sub);

    return (sum + sub);
}
