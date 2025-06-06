typedef struct {
    long x;
    long y;
    double alpha;
} Point;

typedef struct {
    Point src;
    Point tgt;
} Ligne;

typedef struct {
    long x;
    double T;
    double Z;
} Test;

long main(long X, Point p, double Y, double Z){
    double E = 1.0e-10;
    Point P2 = p;
    Z = (double)X + Y - E;
    return (Z);
}