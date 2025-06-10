long main(long X, double Y, double Z){

    double pi = 3.1415926;
    double E = 1.0e-10;
    double diff = pi - E;

    Z = (double)X + Y - E;

    double result = (double)X + Y;

    printf(diff);
    printf(result);
    printf(Z);

    return (Z);
}