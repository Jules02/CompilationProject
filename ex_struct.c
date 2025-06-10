typedef struct {
    long x;
    double y;
} Point;

typedef struct {
    Point src;
    Point trgt;
} Line;

long main () {
    Point p;
    p.x = 4;
    p.y = 5.0;
    printf(p.x);
    printf(p.y + p.x);
    return (p.x + p.y);
}