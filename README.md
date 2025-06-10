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

# Ce qu'il est possible

### Double

### Types

### Struct

Pour les structures, nous avons choisi de définir toutes les structures
utilisées avant le `main`. Chaque structure est alors définie selon le modèle
suivant :

```
typedef struct {
    <ATTR1_TYPE> <ATTR1_NAME>;
    ...
} <STRUCT_NAME>;
```

Cela étant fait la structure est utilisable dans le main. Dans notre cas,
l'utilisation se réalise avec :

1. l'initialisation de l'entité `<STRUCT_NAME> <ENTITY_NAME>;`
2. l'affectation de ses attributs `<ENTITY_NAME>.<ATTR1_NAME> = ...`
3. l'accès à la valeur de ses attributs `<ENTITY_NAME>.<ATTR1_NAME>`

Il est possible de définir une structure dont un ou plusieurs attributs sont eux
mêmes des structures. Cependant, il ne sera pas possible d'utiliser ces
attributs.

### Pointeurs

Il y a quatre syntax importantes à retenir pour les pointeurs :

1. La déclaration d'un pointeur : `long *p;`
2. L'atribution d'une valeur à un pointeur : `p = &x;`
3. L'accès à la valeur pointée par un pointeur : `*p`
4. L'accès à l'adresse d'une variable : `&x`
