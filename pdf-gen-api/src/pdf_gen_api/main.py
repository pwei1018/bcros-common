"""This is the driver for PDF Generation POC"""

from pdf_gen_api.resources import GenerableItem
from pdf_gen_api.models import Coordinator


def show_menu():
    print("\n==========================================================")
    print("============ PDF Auto Generation Demo v0.3 ===============")
    print("==========================================================")
    print("Please select a PDF file to generate:")
    count = 1
    for option in GenerableItem:
        words = option.value.split('_')
        option_name = ''
        for word in words:
            if word == 'agm':
                option_name += f"{word.upper()} "
            else:
                option_name += f"{word.capitalize()} "
        print(f'{count}. {option_name}')
        count += 1
    #print("(other forms to be configured)")
    print("---------------")
    print(f"{count}. Exit")
    print("----------------------------------------------------------")

def get_user_selection():
    show_menu()
    while True:
        selection = input("Your selection: ")
        if selection.isdigit():
            selection = int(selection)
            if 1 <= selection <= len(GenerableItem):
                return selection
            elif selection == len(GenerableItem) + 1:
                return 'exit'
        print("Please select from provided options.")
        print("----------------------------------------------------------")


def main():
    while True:
        selection = get_user_selection()
        if selection == 'exit':
            print("Thank you :)")
            break
        else:
            pdf_selection = list(GenerableItem)[selection - 1]
            coordinator = Coordinator()
            coordinator.run_app(pdf_selection)

if __name__ == "__main__":
    main()
