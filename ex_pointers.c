typedef struct
{
    long num;
} Test;

long main()
{
    long num;
    long ptrValHolder;

    num = 12345;
    printf(num);

    long *ptrNum;
    ptrNum = &num;

    ptrValHolder = *ptrNum;
    printf(ptrValHolder);

    Test *test;
    test.num = 4;
    printf(test.num);

    return (0);
}