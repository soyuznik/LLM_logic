
from modules.model_interface import ModelInterface
from modules.logger import Logger
def main():
    model_interface = ModelInterface()

    Logger.log("Enter your statements (type 'exit' to quit):")
    while True:
        user_input = """9. Win Through Your Actions, Never Through Argument Any momentary triumph you think gained through argument is really a Pyrrhic victory. The resentment you stir up is stronger and lasts longer than any momentary change of opinion."""
        
        
        
        #input(">> ")
        if user_input.lower() == 'exit':
            break
        Logger.log("Model Output: ", end="")
        model_interface.process_statement(user_input)
        Logger.log()  # for a new line after the output

if __name__ == "__main__":
    main()