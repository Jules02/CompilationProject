typedef struct
{
    long num;
} Test;

long main()
{
    long **test;
    long tstNumLong;
    long ptrValHolder;

    tstNumLong = 12345;
    printf(tstNumLong);

    long *ptrNum;
    ptrNum = &tstNumLong;

    ptrValHolder = *ptrNum;
    printf(ptrValHolder);

    Test *test;
    test.num = 4;
    printf(test.num);

    return (0);
}