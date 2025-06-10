typedef struct {
    long x;
    long y;
}Point;

typedef struct {
    long p1;
    long p2;
}Ligne;

long main(long A, long B, long C)
{
    Point p;
    
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
