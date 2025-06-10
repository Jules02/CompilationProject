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

    // l'accès à un attribut d'un attribut n'est pas autorisé par la grammaire :
    l.src.y = q.y; // fail
    printf(l.src.x); // fail

    // les attributs des structures ne peuvent pas être défini au moment de la déclaration des structure :
    Point r = {1, 2}; // fail
    Point s = {.x = 4, .y = 1}; // fail

    return (p.x);
}