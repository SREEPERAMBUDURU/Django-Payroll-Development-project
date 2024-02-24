def calculate_flames(name1, name2):
    name1 = name1.lower().replace(" ", "")
    name2 = name2.lower().replace(" ", "")

    flames = "flames"
    flames_count = len(name1) + len(name2)

    for char in name1:
        if char in name2:
            name1 = name1.replace(char, "", 1)
            name2 = name2.replace(char, "", 1)

    flames_count -= len(name1) + len(name2)

    while len(flames) > 1:
        index = (flames_count - 1) % len(flames)
        flames = flames[:index] + flames[index + 1:]

    return flames


def main():
    print("Welcome to FLAMES game!")
    name1 = input("Enter the first name: ")
    name2 = input("Enter the second name: ")

    result = calculate_flames(name1, name2)

    if result == 'f':
        print("You are FRIENDS!")
    elif result == 'l':
        print("There is LOVE between you!")
    elif result == 'a':
        print("You have AFFECTION towards each other!")
    elif result == 'm':
        print("You are MARRIED!")
    elif result == 'e':
        print("There is ENMITY between you!")
    elif result == 's':
        print("You are SISTERS/BROTHERS!")

    print("Thanks for playing!")


if __name__ == "__main__":
    main()


