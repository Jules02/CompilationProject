typedef struct {
    long x;
    long y;
} Point;

typedef struct {
    Point src;
    Point trgt;
    long length;
} Line;

long main() {
    Point p;
    Point q;
    Line l;

    l.src = p;
    l.trgt = q;
    printf(l.src.x) // l'accès à un attribut d'un attribut n'est pas autorisé par la grammaire

    return (p.x)
}