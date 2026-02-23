"""MCC code mappings and spending category groups."""

mcc2name: dict[str, str] = {
    "5411": "Grocery Stores, Supermarkets",
    "5814": "Fast Food Restaurants",
    "5812": "Eating Places, Restaurants",
    "5977": "Cosmetic Stores",
    "5943": "Stationery, Office Supplies",
    "5199": "Nondurable Goods",
    "4121": "Taxicabs and Limousines",
    "5995": "Pet Shops",
    "5691": "Men's and Women's Clothing Stores",
    "5200": "Home Supply Warehouse Stores",
    "5311": "Department Stores",
    "7941": "Athletic Fields, Commercial Sports",
    "5262": "Marketplaces",
    "5912": "Drug Stores and Pharmacies",
    "5541": "Service Stations (Gas)",
    "8099": "Medical Services",
    "5331": "Variety Stores",
    "4829": "Money Orders / Wire Transfer",
    "4215": "Courier Services",
    "1750": "Carpentry Contractors",
    "7832": "Motion Picture Theaters",
    "5641": "Children's and Infant's Wear Stores",
    "3068": "Airlines",
    "5499": "Miscellaneous Food Stores",
    "8071": "Dental and Medical Laboratories",
}

mcc_groups: dict[str, list[str]] = {
    "Food & Dining": [
        "Grocery Stores, Supermarkets",
        "Fast Food Restaurants",
        "Eating Places, Restaurants",
        "Miscellaneous Food Stores",
    ],
    "Transport": [
        "Taxicabs and Limousines",
        "Airlines",
        "Service Stations (Gas)",
    ],
    "Shopping": [
        "Cosmetic Stores",
        "Stationery, Office Supplies",
        "Nondurable Goods",
        "Men's and Women's Clothing Stores",
        "Department Stores",
        "Marketplaces",
        "Variety Stores",
        "Children's and Infant's Wear Stores",
        "Home Supply Warehouse Stores",
    ],
    "Health & Beauty": [
        "Drug Stores and Pharmacies",
        "Medical Services",
        "Dental and Medical Laboratories",
    ],
    "Entertainment": [
        "Athletic Fields, Commercial Sports",
        "Motion Picture Theaters",
    ],
    "Services": [
        "Courier Services",
        "Carpentry Contractors",
        "Money Orders / Wire Transfer",
    ],
    "Pets": [
        "Pet Shops",
    ],
}

name_to_group: dict[str, str] = {}
for _group, _names in mcc_groups.items():
    for _name in _names:
        name_to_group[_name] = _group
