Mathis ISAAC, Yuetong LU, Diogo BASSO, Jules DUPONT

# Compilateur

Le compilateur utilise le langage assembleur Linux pour compiler. Il est donc
recommandé de l'exécuter sur un système Linux.

Ce projet est un compilateur minimaliste écrit en Python, qui prend en charge
les types de base, les doubles, les structures et les pointeurs.

### Comment compiler

1. Installez les dépendances nécessaires :

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Compilez le fichier `nanoc.py` en assembly :

```bash
python nanoc.py > src.asm 
nasm -f elf64 src.asm -o src.o
```

3. Exécutez le code d'assemblage :

```bash
gcc -no-pie src.o -o src
./src
```

### Qui a fait quoi

Vous trouverez ci-dessous un tableau détaillant qui s'est vu attribuer quelle
fonctionnalité supplémentaire principale :

| Fonctionnalité | Personne |
| -------------- | -------- |
| types          | Jules    |
| double         | Yuetong  |
| struct         | Mathis   |
| pointeurs      | Diogo    |
