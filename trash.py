from enum import Enum
from random import shuffle
import os
import secrets
import time

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class CardSuit(Enum):
    CLUB = 1
    DIAMOND = 2
    HEART = 3
    SPADE = 4
    JOKER = 5

class CardType(Enum):
    NORMAL = 1
    WILD = 2
    TRASH = 3

    def by_card_value(value):
        if value in trash_cards:
            return CardType.TRASH
        elif value in wild_cards:
            return CardType.WILD
        else:
            return CardType.NORMAL

class Card():
    type = CardType.NORMAL
    
    def __init__(self, cardsuit, cardvalue):
        self.suit = cardsuit
        self.value = cardvalue
        self.type = CardType.by_card_value(self.value)

    def full_string(self):
        return str(self.suit.name) + "(" + self.value + ", " + str(self.type) + ")"

    def __str__(self):
        if self.suit == CardSuit.JOKER:
            return "JOKER"
        else:
            # return str(self.suit.name) + "(" + self.value + ")"
            return "{}({})".format(get_card_name(self.value), self.suit.name)
            # return "{} of {}S".format(get_card_name(self.value), self.suit.name)

class BoardSpot():
    flipped = False

    def __init__(self, value, card):
        self.value = value
        self.card = card
        self.last_card = None

    def __str__(self):
        return str("value: " + self.value) + ", card: " + str(self.card)

    def unflipped_or_wild(self):
        if self.flipped == False:
            return True
        elif self.card.value in wild_cards:
            return True
        else:
            return False

    def replace_card(self, card):
        self.last_card = self.card
        self.card = card
        self.flipped = True
        return self.last_card

def game_loop_input(board, deck):
    verbose = True
    current_card = None
    loop_count = 0

    while True:
        if current_card == None:
            clear_and_print_board(board)
            x = input("Please enter d to draw a card: ")
            if x == 'd' or x == 'D':
                current_card = deck.pop(0)

            can_continue = False
            while can_continue == False:

                if current_card == None:
                    break

                if current_card.type == CardType.TRASH:
                    clear_and_print_board(board)
                    print("You drew a {}. It is trash".format(current_card))
                    discard_pile.append(current_card)
                    current_card = None
                    sleep_and_clear()
                else:
                    if current_card.type == CardType.NORMAL and is_spot_taken(board, current_card):
                        clear_and_print_board(board)
                        print("You drew a {}. Its spot is already taken".format(current_card))
                        discard_pile.append(current_card)
                        current_card = None
                        time.sleep(5)
                        break
                    
                    clear_and_print_board(board)
                    x = input("You drew a {}. Would you like to place it? [A-10]: ".format(current_card))

                    index = -1
                    try:
                        index = tableau_assigments.index(x.upper())
                    except ValueError as error:
                        # print('Invalid input. Error: ' + repr(error))
                        print('Could not place card. Please pick a valid spot.')

                    if index >= 0:
                        try:
                            current_card = play_card_at_index(board, current_card, index)
                            cls()
                        except Exception as error:
                            # Error: ' + repr(error)
                            print('Could not place card. Please pick a valid spot.')

                    if check_win(board):
                        break

                    if current_card == None:
                        can_continue = True

                # # if verbose and current_card != None:
                # if verbose:
                #     print_board(board)

        if check_win(board):
            break

        loop_count += 1

        if loop_count > 50:
            print("Too many loops")
            exit(1)

def game_loop(board, deck):
    current_card = None
    loop_count = 0
    while True:
        if current_card == None and len(deck) > 0:
            current_card = deck.pop(0)
            print("You drew a {}".format(current_card))
        elif current_card != None:
            print("You uncovered a {}".format(current_card))

        current_card = play_card(board, current_card)

        if verbose and current_card != None:
            print_board(board)

        if check_win(board):
            break

        if len(deck) == 0:
            print("Deck is empty")
            exit(1)

        loop_count += 1
        if loop_count > 50:
            print("Too many loops")
            exit(1)

def play_card_at_index(board, card, index):
    return_card = None
    if board[index].unflipped_or_wild() and is_wild(card):
        return_card = board[index].replace_card(card)
    elif board[index].unflipped_or_wild() and is_normal(card) and board[index].value == card.value:
        return_card = board[index].replace_card(card)
    else:
        raise Exception("Cannot place card at index {}.".format(index))

    return return_card


def play_card(board, card):
    assigned_flag = False
    trash_flag = False
    wild_flag = False

    replaced_card = None

    # Normal replacement
    for index, value in enumerate(tableau_assigments):
        if card.value == value and board[index].unflipped_or_wild():
            assigned_flag = True
            print("Placing {} in spot {}".format(card, index + 1))
            replaced_card = board[index].replace_card(card)
            break

    # Current card is a trash card and cannot be placed.
    for value in trash_cards:
        if card.value == value:
            trash_flag = True
            print("Found {}. TRASH!".format(card))
            break

    # Current card is a wild card. Can be placed to any non flipped spot.
    for value in wild_cards:
        if card.value == value:
            wild_flag = True
            print("Found {}. WILD!".format(card))
            unflipped_spots = list(filter(lambda spot: spot.flipped == False, board))
            random_spot = secrets.choice(unflipped_spots)
            assign_index = tableau_assigments.index(random_spot.value)
            print("Placing {} in random spot {}".format(card, assign_index + 1))
            replaced_card = board[assign_index].replace_card(card)
            break

    if replaced_card == None:
        if trash_flag == False:
            print("Card spot {} taken. Discard.".format(card))
        discard_pile.append(card)

    return replaced_card

def check_win(board):
    if all(spot.flipped for spot in board):
        return True
    else:
        return False

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

def sleep_and_clear():
    time.sleep(3.000)
    cls()

def clear_and_print_board(board):
    cls()
    print_board(board)

def is_normal(card):
    if card.value in tableau_assigments:
        return True
    else:
        return False

def is_normal_or_wild(card):
    if is_normal(card) or is_wild(card):
        return True
    else:
        return False

def is_spot_taken(board, card):
    for spot in board:
        if spot.value == card.value and spot.card.type == CardType.NORMAL and spot.flipped:
            return True
    return False

def is_trash(card):
    if card.value in trash_cards:
        return True
    else:
        return False

def is_wild(card):
    if card.value in wild_cards:
        return True
    else:
        return False

def get_card_name(value):
    if value == 'A':
        return 'Ace'
    elif value == 'K':
        return 'King'
    elif value == 'Q':
        return 'Queen'
    elif value == 'J':
        return 'Jack'
    else:
        return value

def print_deck(deck):
    cards = []
    for card in deck:
        cards.append(card.full_string())
    print(','.join(cards))

def print_board(board):
    board_width = 87

    def print_border():
        print('-'.join(["+", '-' * board_width, '+']))

    def print_cards(start, end):
        line = ["|"]
        take_five = []
        for board_spot in board[start:end]:
            if board_spot.flipped:
                line.append("{:>15}".format(str(board_spot.card)))
            else:
                line.append("{:>15}".format('X'))
            line.append("|")
        print(' '.join(line))

    # print top boarder
    print_border()

    # print top row of cards
    print_cards(0, 5)

    # print middle boarder
    print_border()

    # print bottom row of cards
    print_cards(5, 10)

    # print bottom boarder
    print_border()

suit_cards = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
tableau_assigments = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']
trash_cards = ['J', 'Q']
wild_cards = ['K', '98', '99']

games_played = 0
total_games_count = 1_000_000
total_games_count = 1
trashless_run_count = 0
start_time = time.time()
verbose = False

# Build the card playing deck
unsorted_deck = list(map(lambda x: Card(CardSuit.CLUB, x), suit_cards))
unsorted_deck.extend(list(map(lambda x: Card(CardSuit.DIAMOND, x), suit_cards)))
unsorted_deck.extend(list(map(lambda x: Card(CardSuit.HEART, x), suit_cards)))
unsorted_deck.extend(list(map(lambda x: Card(CardSuit.SPADE, x), suit_cards)))
unsorted_deck.append(Card(CardSuit.JOKER, '98'))
unsorted_deck.append(Card(CardSuit.JOKER, '99'))

while games_played < total_games_count:

    deck = unsorted_deck.copy()
    shuffle(deck)

    # Initialize the discard pile
    discard_pile = list()

    # print('>>>')
    if verbose:
        print('Creating tableau')

    board = [None] * 10
    board[0] = BoardSpot('A', deck.pop())
    board[1] = BoardSpot('2', deck.pop())
    board[2] = BoardSpot('3', deck.pop())
    board[3] = BoardSpot('4', deck.pop())
    board[4] = BoardSpot('5', deck.pop())
    board[5] = BoardSpot('6', deck.pop())
    board[6] = BoardSpot('7', deck.pop())
    board[7] = BoardSpot('8', deck.pop())
    board[8] = BoardSpot('9', deck.pop())
    board[9] = BoardSpot('10', deck.pop())

    if verbose:
        print_board(board)

    # game_loop(board, deck)
    game_loop_input(board, deck)

    if len(discard_pile) == 0:
        trashless_run_count += 1
        print("A trashless run was played!")
    else:
        print("You won.")

    # Print winning tableau
    print_board(board)

    if verbose or True:
        print("---")
        print("Discard Pile")
        print_deck(discard_pile)
        print("Deck")
        print_deck(deck)
        print("Deck Count: {}, Discard Pile Count: {}, Total Count: {}".format(len(deck), len(discard_pile), len(deck)+len(discard_pile)))
        print("---")

    print()

    games_played += 1

print("Games Played: {}".format(games_played))
print("Trashless Runs: {}".format(trashless_run_count))

print ('The script took {0} seconds!'.format(time.time() - start_time))

# Various enum values
# print(CardType.CLUB)
# print(CardType.CLUB.name)
# print(CardType.CLUB.value)
# print(type(CardType.CLUB))
# print(repr(CardType.CLUB))
# print(list(CardType))
