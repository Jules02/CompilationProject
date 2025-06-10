long main()
{
    long num;
    long ptrValHolder;

    num = 12345;
    long *ptrNum;
    ptrNum = &num;

    printf(num);

    ptrValHolder = *ptrNum;
    printf(ptrValHolder);

    return (0);
}