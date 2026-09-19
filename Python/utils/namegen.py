"""
utils/namegen.py
=================
Faker is not installable in this offline environment, so this module
provides curated Egyptian-context name/text pools and helper functions
used across every generator. This keeps names/companies realistic and
locale-appropriate (arguably more so than Faker's generic ar_EG locale).
"""

import numpy as np

MALE_FIRST = ["Ahmed", "Mohamed", "Mahmoud", "Omar", "Youssef", "Khaled", "Karim",
              "Amr", "Tarek", "Hossam", "Sherif", "Ibrahim", "Hassan", "Hany",
              "Mostafa", "Waleed", "Ayman", "Adel", "Ashraf", "Sameh"]
FEMALE_FIRST = ["Sara", "Mona", "Nour", "Yasmin", "Heba", "Dina", "Rania",
                "Salma", "Aya", "Nadine", "Marwa", "Hala", "Reem", "Farida",
                "Mervat", "Nesma", "Shaimaa", "Amira", "Doaa", "Eman"]
LAST_NAMES = ["Abdelrahman", "El Sayed", "Hassan", "Ibrahim", "Mostafa", "Kamal",
              "Fahmy", "Zaki", "Nour El Din", "El Shazly", "Anwar", "Gaber",
              "Farouk", "El Masry", "Saleh", "Amin", "Mansour", "El Gendy",
              "Youssef", "Adly", "Shawky", "El Hakim", "Ramadan", "Sabry"]

COMPANY_SUFFIX_LOCAL = ["Trading", "for Food Industries", "Agro Group", "Import & Export",
                         "Packaging Co.", "Industrial Group", "Holding", "for Manufacturing"]
COMPANY_ROOT_LOCAL = ["Nile", "Delta", "Pharaoh", "Cairo", "Alex", "Sphinx", "Horus",
                       "Sakkara", "Rosetta", "Oasis", "Fayoum", "Desert Rose", "Green Valley"]
COMPANY_ROOT_IMPORT = ["Global", "EuroFood", "AsiaPack", "TransCont", "Continental",
                        "Alpine", "Baltic", "Pacific Rim", "Meridian"]
COMPANY_SUFFIX_IMPORT = ["Trading Ltd.", "Import Group", "International", "Logistics Corp.",
                          "Supply Chain Ltd.", "Commodities Inc."]

DISTRIBUTOR_ROOTS = ["Nile Star", "Delta Link", "Fast Trade", "Prime Route", "Cairo Express",
                      "Golden Chain", "United Distributors", "Speedy Supply", "Metro Link",
                      "Al Amal", "Al Salam", "El Nour", "Modern Trade Partners"]

STORE_ROOTS = ["Al Amal", "Al Salam", "El Baraka", "Family", "City", "Metro", "Corner",
               "Al Rahma", "El Nour", "Sunrise", "Green", "Al Fajr", "Al Noor", "Star"]

FACTORY_ROOTS = ["Delta", "Nile Valley", "October", "10th Ramadan", "Badr City",
                  "Suez Canal", "New Cairo", "El Sadat"]

_rng = np.random.default_rng(42)


def person_name():
    is_male = _rng.random() < 0.6
    first = _rng.choice(MALE_FIRST if is_male else FEMALE_FIRST)
    last = _rng.choice(LAST_NAMES)
    return f"{first} {last}"


def local_supplier_name(i):
    return f"{_rng.choice(COMPANY_ROOT_LOCAL)} {_rng.choice(COMPANY_SUFFIX_LOCAL)} {i}"


def imported_supplier_name(i):
    return f"{_rng.choice(COMPANY_ROOT_IMPORT)} {_rng.choice(COMPANY_SUFFIX_IMPORT)} {i}"


def distributor_name(i):
    return f"{_rng.choice(DISTRIBUTOR_ROOTS)} Distribution {i}"


def store_name(i, store_type):
    return f"{_rng.choice(STORE_ROOTS)} {store_type} {i}"


def factory_name(i, governorate):
    return f"{_rng.choice(FACTORY_ROOTS)} Plant {i} - {governorate}"
