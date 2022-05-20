# Downloads multiple molecule's substructures' CIDs and IsomericSMILES and creates files for each of them.
# Autor: Arthur Lacerda
# Autor: João Pedro Gonçalves Ribeiro
# Desenvolvimento: 16/05/2022
# Orientador: Edson Luiz Folador

import pandas as pd
from urllib.error import HTTPError
from urllib.request import urlopen
from urllib.parse import quote
from json import loads
from time import sleep
import os
from sys import argv


def get_result(url):
    try:
        connection = urlopen(url)
    except HTTPError:
        return None
    else:
        return connection.read().rstrip().decode('utf-8')


def get_listkey(cid):
    """Gets list needed to get substructures"""
    result = get_result(f"http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/substructure/cid/{cid}/XML")
    if not result:
        return []
    listkey = ""
    for line in result.split("\n"):
        if line.find("ListKey") >= 0:
            listkey = line.split("ListKey>")[1][:-2]
    print(f'lista necessaria para as substruturas:\n{listkey}\n')
    with open('listkey.txt', 'w') as list:
        list.write(listkey)


def listkey_to_substructures():
    """Gets substructures from listkey"""
    with open('listkey.txt', 'r') as list:
        listkey = list.read()
    result = get_result(
        f"http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/listkey/{listkey}/property/IsomericSMILES/JSON")
    result = loads(result)['PropertyTable']['Properties']
    os.remove('listkey.txt')
    return result


def move_isosmiles():
    """Formats cid/smiles DataFrame"""
    global df
    # Replaces cid as first column
    df = df[['CID'] + ['IsomericSMILES']]
    # Replaces main drug's cid for its name
    df.loc[df['IsomericSMILES'] == IsomericSMILES, 'CID'] = molecula
    # Replaces main drug as first row
    index = df.index[df['CID'] == molecula].to_list()
    idx = index + [i for i in range(len(df)) if i != index[0]]
    df = df.iloc[idx]
    df.reset_index(drop=True, inplace=True)


def create_files():
    """Create files"""
    if os.path.isdir("./lingad"):
        print("Missing ./ligand directory")
    os.mkdir(f'ligand/{molecula}')

    # Creates file with all cid and smiles
    df.to_csv(f"{molecula}-pubchem.txt", sep=' ', header=False)

    # Creates files for each smiles
    with open(f'ligand/{molecula}/{molecula}-{molecula}.smi', 'w') as arqv:
        arqv.write(IsomericSMILES)
    for i in range(1, len(df)):
        with open(f'ligand/{molecula}/{molecula}-cid{df["CID"][i]}.smi', 'w') as arqv:
            arqv.write(df['IsomericSMILES'][i])


def _name(mo):
    """Gets initial information from the molecule's name"""
    global molecula, cid
    molecula = mo
    cid = get_result(f"http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{mo}/cids/TXT")
    if cid is not None:
        return True
    else:
        return False


def _cid(mo):
    """Gets initial information from a cid code"""
    global molecula, cid
    cid = mo
    molecula = get_result(f"http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{mo}/description/JSON")
    if molecula is not None:
        molecula = loads(molecula)['InformationList']['Information'][0]['Title']
        return True
    else:
        return False


def _smiles(mo):
    """Gets initial information from a smiles code"""
    global molecula, cid
    smiles = get_result(f"http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/description/JSON?smiles={quote(mo)}")
    if smiles is not None:
        molecula = loads(smiles)['InformationList']['Information'][0]['Title']
        cid = loads(smiles)['InformationList']['Information'][0]['CID']
        return True
    else:
        return False


def _help():
    """Help function"""
    print(f"""
Usage: python3 {argv[0]} [-n] [-c] [-s] [-h] [molecule_descriptors]

Downloads multiple molecule's substructures' CIDs and IsomericSMILES and
creates files for each of them.

It takes each inputted molecule descriptor (one per molecule) and tries to
find information about said molecule on the Pubchem Compound Database. If it
finds them, it searches for similar ones by substructure and collects their
smiles and cid codes. Then it creates a folder "ligand" on the current path
and saves each smiles retrieved a folder named after the input molecule, each
in a different ".smi" file.

Parameters:
  -n, --name                : Searches information on the base molecule by
                              name (Default).
  -c, --cid                 : Searches information on the base molecule by
                              cid.
  -s, --smiles              : Searches information on the base molecule by
                              smiles.
  -h, --help                : Prints this message.

A least one parameter must be passed.
Everything that is not one of these parameters is considered a molecule
descriptor.
If more than one of these parameters is passed, the latest one will take
effect. The exception is are the help parameters, which will always print
this message and end the program regardless of position or other parameters.
""")
    exit(0)


# Checks for conditions that would cause the program to print a help message and close
if ("-h" in argv) or ("--help" in argv) or (len(argv) < 2):
    _help()

key = "--name"  # Type of initial search to perform.
molecules = []  # List of molecules passed as parameters to search.

# Dictionary with flag parameters mapped to their respective search functions.
search_opts = {"-c": _cid, "--cid": _cid,
               "-n": _name, "--name": _name,
               "-s": _smiles, "--smiles": _smiles}

molecula = None  # Name of the initial molecule
cid = None  # CID of the initial molecule.

print()

# Iterates all parameters.
for param in range(1, len(argv)):
    # Checks if parameter is on Search Dictionary.
    if argv[param] in search_opts.keys():
        key = argv[param]
    else:
        molecules.append(argv[param])  # Appends molecules' descriptors to be processed to the list molecules
    param += 1

# Iterates all molecule descriptors in moleculees playlist
for mol in molecules:
    print(f"{mol}:\n")

    # Executes search funtion and uses return to decide if it succedeed to retrieve the initial information.
    if search_opts[key](mol):
        IsomericSMILES = get_result(
            f"http://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/IsomericSMILES/TXT")
        print(f'Drug: \n{molecula}')
        print(f'cid:\n{cid}')
        print(f'isoSMILES:\n{IsomericSMILES}')

        get_listkey(cid)
        sleep(5)
        df = pd.DataFrame(listkey_to_substructures())

        print()
        print(f'{len(df.index)} substructures found')

        print("Running...\n")

        # Adjusts smiles
        move_isosmiles()

        # Creates .smi files
        create_files()

        print('SCHLUSS!')
    else:
        print('Descriptor not in database')

    # Resets states of molecula and cid.
    molecula = None
    cid = None
    print(f"\n{'-'*40}\n")
