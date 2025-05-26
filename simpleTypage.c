long main(long X, double Y, double Z){
    double E = 1.0e-10;
    Z = (double)X + Y - E;
    return (Z);
}