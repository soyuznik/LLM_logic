


class Database:
    
    records = {}

        
    # add the record of type "name: definition" to the database
    def add_record(self, record: str):
        # 1. Safety Check: Ignore empty or whitespace-only strings
        if not record or not record.strip():
            return

        # count the number of definitions in the record
        num_definitions = record.count(": ")

        # if more do recursion
        if num_definitions > 1:
            definitions = record.split(".")
            for definition in definitions:
                # This recursion will now be safe because of the check at step #1
                self.add_record(definition)
            return

        # 2. Validation: Ensure the split actually results in two parts
        parts = record.split(": ", 1)
        if len(parts) == 2:
            name = parts[0].strip()
            descript = parts[1].strip()
            self.records[name] = descript
        else:
            # Optional: Log a warning for malformed records if necessary
            # print(f"Skipping malformed record: {record}")
            pass
    #get the list of records in the database
    def get_record_list(self):
        return self.records
    

    