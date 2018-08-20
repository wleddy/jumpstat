# jump models.py
from users.models import SqliteTable

class Bike(SqliteTable):
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'bike'
        self.order_by_col = 'id'
        self.defaults = {}
        
    def create_table(self):
        """Define and create the bike table"""
        
        sql = """
            jump_bike_id NUMBER,
            name TEXT
            """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
        
        
class Sighting(SqliteTable):
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'sighting'
        self.order_by_col = 'id'
        self.defaults = {'returned_to_service':0,}
        
    def create_table(self):
        """Define and create the sighting table"""
        
        sql = """
            jump_bike_id NUMBER,
            bike_name TEXT,
            retrieved DATETIME,
            network_id NUMBER,
            address TEXT,
            lng NUMBER,
            lat NUMBER,
            city TEXT,
            batt_level NUMBER,
            batt_distance NUMBER,
            hub_id NUMBER,
            day_number NUMBER,
            returned_to_service INT DEFAULT 0,
            stighted DATETIME,
            bonuses TEXT
            """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
        

class Trip(SqliteTable):
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'trip'
        self.order_by_col = 'id'
        self.defaults = {}

    def create_table(self):
        """Define and create the trip table"""

        sql = """
            jump_bike_id NUMBER,
            origin_sighting_id INTEGER,
            destination_sighting_id INTEGER,
            miles NUMBER,
            FOREIGN KEY (origin_sighting_id) REFERENCES sighting(id) ON DELETE CASCADE,
            FOREIGN KEY (destination_sighting_id) REFERENCES sighting(id) ON DELETE CASCADE
            """
        super().create_table(sql)

    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()

class AvailableBikeCount(SqliteTable):
    """Keeps a snapshot of the number of bikes available at each data retrieval"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'available_bike_count'
        self.order_by_col = 'id'
        self.defaults = {}

    def create_table(self):
        """Define and create the trip table"""

        sql = """
            bikes_available NUMBER,
            retrieved DATETIME,
            city, TEXT,
            day_number INTEGER
            """
        super().create_table(sql)

    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
    


def init_tables(db):
    Bike(db).init_table()
    Sighting(db).init_table()
    Trip(db).init_table()
    AvailableBikeCount(db).init_table()
        
    