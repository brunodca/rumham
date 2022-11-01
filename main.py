import argparse
import datetime
import json
import os
import requests
import time
import typing

scryfall = "https://api.scryfall.com/cards/search"

# Non URL encoded since the request does that for us
query_heritage_commander = {
    "q": "(st:core OR st:expansion) -is:digital format:commander"
}

file_name = "./commander_heritage.json"


def isFileOK() -> bool:
    """Check if the local card database file is in good condition. Needs to
    exist and not be older than some days

    Return
        True if the file is ok
    """

    if not os.path.isfile(file_name):
        return False
    now = datetime.datetime.today()
    file_changed_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_name))
    time_since_modification = now - file_changed_time
    if time_since_modification.days > 7:
        return False
    return True


def getCardListFromUrl(
    current_url: str, data: typing.List[typing.Dict]
) -> typing.List[typing.Dict]:
    """Given the URL, and the existing list with cards, this function will
    prompt the URL for more data, append to existing data and return it.

    ARG
        current_url the url to poll for that
        data list of cards

    Return
        extended list of cards
    """

    time.sleep(0.2)
    answer = requests.get(url=current_url)
    answer_json = answer.json()
    data.extend(answer_json["data"])
    print(f"Reading {len(data)} of {answer_json['total_cards']} cards.")
    if answer_json["has_more"]:
        return getCardListFromUrl(answer_json["next_page"], data)
    else:
        return data


def createHeritageDataFile():
    """Creates the mtg commander heritage card database if it does not exist or
    if it is too old, and saves database file in the current folder
    """

    if isFileOK():
        print("Existing local card database is up to date.")
        return
    print("Refreshing local card database - will take a while.")
    answer = requests.get(url=scryfall, params=query_heritage_commander)
    answer_json = answer.json()
    data = answer_json["data"]
    if answer_json["has_more"]:
        data = getCardListFromUrl(answer_json["next_page"], data)
    with open("./commander_heritage.json", "w") as dump:
        json.dump(data, dump)


def loadHeritageDataFile() -> typing.List[typing.Dict]:
    """Loads the contents of the heritage data file

    return
       list with cards represented as dicts
    """

    with open(file_name, "r") as read_file:
        data_read = json.load(read_file)
        return data_read


def getHeritageDataCardNames(
    heritage_data: typing.List[typing.Dict],
) -> typing.List[str]:
    """Given the list of dictionaries representing the cards, get the card names
    and stort them out in case the card is double sided.

    args
        heritage_data list of dictionaries where each dictionary represents a card

    return
        list of strings containing the card names.
    """
    card_name_list = []
    for card in heritage_data:
        card_name = card["name"]
        # Deck stats used the full name, including the second card name so we
        # need to save it
        card_name_list.append(card_name.lower())
        # Tapped out only used the first card name so we need to separate and
        # extract that.
        card_names = card_name.split("//")
        # Use only the first name since that is what the deck apps are using
        card_name_list.append(card_names[0].strip().lower())
    return card_name_list


def parseArguments():
    parser = argparse.ArgumentParser(
        prog="RumHam",
        description="Take a decklist in Magic Online format and check if it respects commander heritage format",
        epilog="Lycka till.",
    )
    parser.add_argument(
        "--deck", type=str, required=True, help="The file containing the deck list"
    )

    args = parser.parse_args()
    return args.deck


def getCardsFromMagicOnlineFile(arena_file: str) -> typing.List[str]:
    """Given an magic online style file, extract all card names and return them in a
    list of strings

    Args
        arena_file file containing deck list in arena format

    Return
        list of strings representing the file names
    """

    card_list = []
    with open(arena_file, "r") as card_contents:
        for line in card_contents:
            # Empty line means end so we need to exit
            if not line.strip():
                break
            # Remove trailling newline
            line = line.rstrip()
            # Separate by spaces
            line_contents = line.split(" ")
            # Join all but the first result of the split which is the number of
            # copies
            card_list.append(" ".join(line_contents[1:]))

    return card_list


def main():
    createHeritageDataFile()
    heritage_data = loadHeritageDataFile()
    heritage_card_names = getHeritageDataCardNames(heritage_data)
    deck_list = getCardsFromMagicOnlineFile(parseArguments())
    for card_in_deck_list in deck_list:
        if card_in_deck_list.lower() not in heritage_card_names:
            print("--" + card_in_deck_list + "-- is not a legal card in heritage.")


if __name__ == "__main__":
    main()
