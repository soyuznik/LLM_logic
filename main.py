
from modules.model_interface import ModelInterface
from modules.logger import Logger
from modules.database import Database

db = Database()
def process_user_input(user_input: str, model_interface: ModelInterface, db: Database):
    Logger.log("Model Output: ", end="")
    user_input = str(db.get_record_list()) + user_input
    expr = model_interface.get_expression(user_input)
    defin = model_interface.get_definitions(user_input)
    db.add_record(defin)
    print(expr)
    Logger.log()

def main():
    model_interface = ModelInterface()
    
    user_input = """I love cake. A cake is a type of dessert. Desserts are typically sweet foods eaten after a meal."""
    process_user_input(user_input, model_interface, db)
    user_input = """If I dont eat cake after a meal, I feel sad. I go cycling to the shop to buy something sweet."""
    process_user_input(user_input, model_interface, db)
    user_input = """If what I eat after a meal is not sweet, I feel sad."""
    process_user_input(user_input, model_interface, db)
    user_input = """I feel sad. That means I should eat cake."""
    process_user_input(user_input, model_interface, db)
    user_input = """Cycling makes me want to eat cake. I have money , so i should go buy cake"""
    process_user_input(user_input, model_interface, db)
    

if __name__ == "__main__":
    main()